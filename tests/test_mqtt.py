import asyncio
import struct
from pathlib import Path

from ser2net_app import ha_mqtt
from ser2net_app.controller import Controller
from ser2net_app.db import Database
from ser2net_app.events import EventLog
from ser2net_app.model import AppConfig, Connection
from ser2net_app.mqtt import Broker, _packet
from ser2net_app.store import Store
from ser2net_app.trace import TraceHub


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
                topic = b"ser2net/0000000a/enabled/set"
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
    assert "homeassistant/switch/ser2net_0000000a/enabled/config" in published
    assert published["ser2net/status"] == b"offline"  # said on a clean stop
