import asyncio
import struct
from pathlib import Path

import pytest

from device_proxy import ha_mqtt
from device_proxy.admin import AdminError
from device_proxy.controller import Controller
from device_proxy.db import Database
from device_proxy.events import EventLog
from device_proxy.model import AppConfig, Connection
from device_proxy.mqtt import Broker, MqttClient, _packet, check_broker
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
    controller._stop, controller._running = asyncio.Event(), True
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


async def test_check_broker_says_why_it_fails() -> None:
    async def accepting(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.read(64)
        writer.write(bytes([0x20, 2, 0, 0]))
        await writer.drain()
        writer.close()

    async def refusing(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.read(64)
        writer.write(bytes([0x20, 2, 0, 4]))  # bad user name or password
        await writer.drain()
        writer.close()

    good = await asyncio.start_server(accepting, "127.0.0.1", 0)
    bad = await asyncio.start_server(refusing, "127.0.0.1", 0)
    good_port = good.sockets[0].getsockname()[1]
    bad_port = bad.sockets[0].getsockname()[1]
    assert await check_broker(Broker("127.0.0.1", good_port)) == ""
    assert "user or password" in await check_broker(Broker("127.0.0.1", bad_port, "a", "b"))
    good.close()
    bad.close()
    assert await check_broker(Broker("127.0.0.1", good_port))  # nothing listens any more


async def test_buttons_are_announced_and_pressed(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    configs = ha_mqtt.HaBridge(controller).configs()
    button = configs["homeassistant/button/device_proxy_0000000a/disconnect/config"]
    assert button["command_topic"] == "device_proxy/0000000a/disconnect/press"
    assert "state_topic" not in button
    assert not any("/to_fallback/" in topic for topic in configs)  # no fallback here

    pressed: list[tuple[str, str]] = []

    async def press(connection_id: str, action: str) -> None:
        pressed.append((connection_id, action))
        if action == "nonsense":
            raise ValueError("no such button")
        if action == "restart":
            raise AdminError("ser2net's admin socket is not there")

    controller.press = press  # type: ignore[method-assign]
    bridge = ha_mqtt.HaBridge(controller)
    await bridge._message("device_proxy/0000000a/disconnect/press", b"PRESS")
    await bridge._message("device_proxy/0000000a/nonsense/press", b"PRESS")  # logged, not raised
    await bridge._message("device_proxy/0000000a/restart/press", b"PRESS")  # the same
    assert pressed == [
        ("0000000a", "disconnect"),
        ("0000000a", "nonsense"),
        ("0000000a", "restart"),
    ]


async def test_meter_entities_for_the_energy_dashboard(tmp_path: Path) -> None:
    from dataclasses import replace

    controller = _controller(tmp_path)
    assert not any("meter_import" in t for t in ha_mqtt.HaBridge(controller).configs())
    meter = replace(controller.config.connections[0], meter_entities=True)
    controller.config = controller.config.with_connection(meter)
    configs = ha_mqtt.HaBridge(controller).configs()
    energy = configs["homeassistant/sensor/device_proxy_0000000a/meter_import/config"]
    assert (energy["device_class"], energy["state_class"], energy["unit_of_measurement"]) == (
        "energy",
        "total_increasing",
        "kWh",
    )
    assert energy["value_template"] == "{{ value_json.meter_import }}"


async def test_a_failing_message_does_not_end_the_connection() -> None:
    """An error while handling one message is logged; the next message still arrives."""
    topics = [b"a/first", b"a/second"]

    async def broker(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.read(1024)  # CONNECT
        writer.write(bytes([0x20, 2, 0, 0]))
        for topic in topics:
            writer.write(
                bytes([0x30, 2 + len(topic) + 1]) + struct.pack("!H", len(topic)) + topic + b"x"
            )
        await writer.drain()
        await reader.read(1024)

    server = await asyncio.start_server(broker, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    seen: list[str] = []
    stop = asyncio.Event()

    async def on_message(topic: str, payload: bytes) -> None:
        seen.append(topic)
        if topic == "a/first":
            raise RuntimeError("a bug")
        stop.set()

    async def on_connect() -> None:
        pass

    client = MqttClient("test", on_message, on_connect)
    await asyncio.wait_for(client.run(Broker("127.0.0.1", port), stop), 5)
    assert seen == ["a/first", "a/second"]
    server.close()


async def test_new_mqtt_settings_apply_when_mqtt_had_died(tmp_path: Path) -> None:
    controller = _controller(tmp_path)

    async def died() -> None:
        raise AdminError("no admin socket")

    controller._mqtt_task = asyncio.create_task(died())
    await asyncio.sleep(0)
    started: list[bool] = []
    controller._start_mqtt = lambda: started.append(True)  # type: ignore[method-assign]
    await controller._restart_mqtt()  # not raised
    assert started == [True]


async def test_a_settings_save_before_the_start_does_not_start_mqtt(tmp_path: Path) -> None:
    """Else start() starts a second client with the same id: both keep throwing out the other."""
    controller = _controller(tmp_path)
    await controller._restart_mqtt()
    assert controller._mqtt_task is None


async def test_old_entities_go_with_a_prefix_with_slashes_another_prefix_or_mqtt_off(
    tmp_path: Path,
) -> None:
    controller = _controller(tmp_path, mqtt_prefix="ha/disc")
    bridge = ha_mqtt.HaBridge(controller)
    sent: list[tuple[str, object]] = []

    async def publish(topic: str, payload: object, retain: bool = False) -> None:
        sent.append((topic, payload))

    bridge.client.publish = publish  # type: ignore[method-assign,assignment]
    stale = "ha/disc/switch/device_proxy_0000dead/enabled/config"
    await bridge._message(stale, b"{}")
    assert sent == [(stale, b"")]

    sent.clear()  # MQTT is switched off: what this bridge announced goes
    await bridge.announce()
    bridge.client.connected.set()
    announced = {t for t, _ in sent}
    sent.clear()
    await bridge.clear(set())
    assert {t for t, _ in sent} == announced and all(p == b"" for _, p in sent)

    sent.clear()  # a connection removed: its retained state goes too
    bridge._last["state:0000dead"] = "{}"
    await bridge.publish_states()
    assert (f"{bridge.base}/0000dead/state", b"") in sent


def test_the_device_list_shows_whose_device_it_is(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    device = ha_mqtt.HaBridge(controller).configs()[
        "homeassistant/button/device_proxy_0000000a/disconnect/config"
    ]["device"]
    assert device["model"].startswith("Device Proxy · ")
    assert device["identifiers"] == ["device_proxy_0000000a"]  # the same device as before
    assert device["model"].split(" · ")[1] in ("Serial", "Seriell")


def test_every_device_links_to_the_app(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.panel_url = "homeassistant://hassio/ingress/abc_device_proxy"
    configs = ha_mqtt.HaBridge(controller).configs()
    assert all(
        config["device"]["configuration_url"] == controller.panel_url for config in configs.values()
    )


def test_without_the_supervisor_there_is_no_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    assert ha_mqtt.panel_url() == ""
    configs = ha_mqtt.HaBridge(_controller(tmp_path)).configs()
    assert not any("configuration_url" in config["device"] for config in configs.values())
