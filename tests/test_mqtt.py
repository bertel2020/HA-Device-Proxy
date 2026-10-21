import asyncio
import struct
from pathlib import Path

from device_proxy import ha_mqtt
from device_proxy.controller import Controller
from device_proxy.db import Database
from device_proxy.events import EventLog
from device_proxy.model import AppConfig, Connection
from device_proxy.mqtt import Broker, _packet
from device_proxy.store import Store
from device_proxy.trace import TraceHub


def test_long_packets_encode_their_length() -> None:
    packet = _packet(3, 0, b"x" * 200)
    assert packet[:3] == bytes([0x30, 0xC8, 0x01])  # 200 = 0x48 | 0x80, then 1


async def test_discovery_and_switch_over_a_broker(tmp_path: Path, monkeypatch: object) -> None:
    published: dict[str, bytes] = {}
    commands: asyncio.Queue[bytes] = asyncio.Queue()

    async def broker(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        async def read() -> tuple[int, bytes]:
            head = (await reader.readexactly(1))[0]
            length, shift = 0, 0
            while True:
                byte = (await reader.readexactly(1))[0]
                length |= (byte & 0x7F) << shift
                shift += 7
                if not byte & 0x80:
                    break
            return head >> 4, await reader.readexactly(length)

        kind, _ = await read()
        assert kind == 1
        writer.write(bytes([0x20, 2, 0, 0]))  # CONNACK accepted
        while True:
            try:
                kind, body = await read()
            except asyncio.IncompleteReadError:
                return
            if kind == 3:
                n = struct.unpack("!H", body[:2])[0]
                published[body[2 : 2 + n].decode()] = body[2 + n :]
            elif kind == 8:  # subscribe: answer and send a switch command
                writer.write(bytes([0x90, 3]) + body[:2] + b"\x00")
                topic = b"device_proxy/0000000a/enabled/set"
                writer.write(
                    bytes([0x30, 2 + len(topic) + 3])
                    + struct.pack("!H", len(topic))
                    + topic
                    + b"OFF"
                )
                await writer.drain()
                await commands.put(b"sent")

    server = await asyncio.start_server(broker, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    monkeypatch.setattr(ha_mqtt, "supervisor_broker", lambda: Broker("127.0.0.1", port))  # type: ignore[attr-defined]
    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    store.save(
        AppConfig(),
        AppConfig(connections=(Connection("eHZ", "/dev/null", 3335, id="0000000a"),)),
        "test",
    )
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    controller._stop = asyncio.Event()
    controller._start_mqtt()
    await asyncio.wait_for(commands.get(), 5)
    for _ in range(50):
        if not controller.config.connections[0].enabled:
            break
        await asyncio.sleep(0.05)
    controller._stop.set()
    assert controller._mqtt_task is not None
    await controller._mqtt_task
    await asyncio.sleep(0.2)  # let the test broker read the last packets
    server.close()

    assert controller.config.connections[0].enabled is False
    assert "homeassistant/switch/device_proxy_0000000a/enabled/config" in published
    assert published["device_proxy/status"] == b"offline"  # said on a clean stop


def _controller(tmp_path: Path, **settings: object) -> Controller:
    from dataclasses import replace

    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    base = AppConfig()
    config = AppConfig(
        replace(base.settings, **settings),
        (Connection("eHZ", "/dev/null", 3335, id="0000000a"),),
    )
    store.save(base, config, "test")
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    controller.config = config
    return controller


async def test_switch_works_with_slashes_in_the_base(tmp_path: Path) -> None:
    controller = _controller(tmp_path, mqtt_base="a/b")
    applied: list[AppConfig] = []

    async def apply(new: object, source: str) -> None:
        assert callable(new)
        applied.append(new(controller.config))

    controller.apply = apply  # type: ignore[method-assign,assignment]
    bridge = ha_mqtt.HaBridge(controller)
    bridge.publish_states = lambda **_: asyncio.sleep(0)  # type: ignore[method-assign,assignment]
    await bridge._message("a/b/0000000a/enabled/set", b"OFF")
    await bridge._message("device_proxy/0000000a/enabled/set", b"OFF")  # another base
    assert [c.connections[0].enabled for c in applied] == [False]


async def test_stale_retained_configs_of_the_app_are_cleared(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    bridge = ha_mqtt.HaBridge(controller)
    sent: list[tuple[str, bytes]] = []

    async def publish(topic: str, payload: object, retain: bool = False) -> None:
        sent.append((topic, payload))  # type: ignore[arg-type]

    bridge.client.publish = publish  # type: ignore[method-assign,assignment]
    live = "homeassistant/switch/device_proxy_0000000a/enabled/config"
    await bridge._message(live, b"{}")
    await bridge._message("homeassistant/switch/device_proxy_0000dead/enabled/config", b"{}")
    await bridge._message("homeassistant/switch/other_app/x/config", b"{}")
    await bridge._message("homeassistant/switch/device_proxy_0000beef/enabled/config", b"")
    assert sent == [("homeassistant/switch/device_proxy_0000dead/enabled/config", b"")]
