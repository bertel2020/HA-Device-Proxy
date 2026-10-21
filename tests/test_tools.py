import asyncio
from pathlib import Path
from typing import Any

from device_proxy.controller import Controller
from device_proxy.db import Database
from device_proxy.diagnostics import redact
from device_proxy.events import EventLog
from device_proxy.meter import analyze, crc_x25
from device_proxy.model import AppConfig, Connection
from device_proxy.notify import Notifier
from device_proxy.store import Store
from device_proxy.trace import TraceHub

ENTRY = bytes.fromhex("7707 0100010800ff 6500 1c0104 01 621e 52ff 69000000000aff4a2b 01")


def sml(body: bytes, *, good: bool = True) -> bytes:
    data = bytes.fromhex("1b1b1b1b01010101") + body + bytes.fromhex("1b1b1b1b1a00")
    crc = crc_x25(data) ^ (0 if good else 1)
    return data + bytes([crc & 0xFF, crc >> 8])


def test_sml_and_d0() -> None:
    result = analyze(b"\x00\x12" + sml(ENTRY) + sml(ENTRY, good=False))
    assert (result.protocol, result.telegrams, result.valid) == ("sml", 2, 1)
    reading = result.readings[0]
    assert (reading.obis, reading.unit) == ("1-0:1.8.0", "Wh")
    assert abs(float(reading.value) - 18450282.7) < 0.01
    d0 = analyze(b"/EBZ5DD3BZ06ETA\r\n\r\n1-0:1.8.0*255(012345.678*kWh)\r\n!\r\n")
    assert (d0.protocol, d0.valid) == ("d0", 1)
    assert d0.readings[0].value == 12345.678 and d0.readings[0].unit == "kWh"


def test_notifications_wait_and_go_away(tmp_path: Path, monkeypatch: Any) -> None:
    db = Database(tmp_path / "h.db")
    controller = Controller(
        Store(db, tmp_path / "c.json"),
        EventLog(db),
        tmp_path / "s.yaml",
        trace=TraceHub(tmp_path / "t", tmp_path / "shm"),
    )
    c = Connection("eHZ", "/dev/ttyGONE", 3335)
    controller.config = AppConfig(connections=(c,))
    controller.present[c.id] = False
    sent: list[tuple[str, dict[str, Any]]] = []
    now = [1000.0]
    notifier = Notifier(clock=lambda: now[0])
    notifier.available = True

    async def fake_call(path: str, data: dict[str, Any]) -> None:
        sent.append((path, data))

    monkeypatch.setattr(notifier, "_send", fake_call)

    async def run() -> None:
        problems = controller.problems(now=now[0])
        assert "device_proxy_" + c.id + "_missing" in problems
        await notifier.update(problems, grace=30, dismiss=True)
        assert sent == []  # within the first minute after the start
        now[0] += 90
        await notifier.update(controller.problems(now=now[0]), grace=30, dismiss=True)
        assert [p for p, _ in sent] == ["services/persistent_notification/create"]
        assert "Gerät fehlt" in sent[0][1]["title"]
        controller.present[c.id] = True
        await notifier.update(controller.problems(now=now[0]), grace=30, dismiss=True)
        assert sent[-1][0] == "services/persistent_notification/dismiss"

    asyncio.run(run())


def test_diagnostics_hide_addresses() -> None:
    data = {"remaddr": "192.168.0.0/16,0", "client": "192.168.1.20:50114", "v6": "fd00:1:2::5"}
    assert redact(data) == {
        "remaddr": "192.168.0.0/16,0",
        "client": "x.x.x.x:50114",
        "v6": "x:x::x",
    }
