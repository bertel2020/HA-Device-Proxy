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

    async def fake_call(path: str, data: dict[str, Any]) -> bool:
        sent.append((path, data))
        return True

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


def test_diagnostics_hide_host_names_and_the_notify_service() -> None:
    import io
    import zipfile

    from device_proxy.diagnostics import build

    config = {
        "settings": {"notify_service": "mobile_app_anna"},
        "connections": [{"kind": "modbus", "host": "wechselrichter.fritz.box", "name": "WR"}],
    }
    data = build(
        version="1",
        ser2net_version="4",
        snapshot={"connections": [{"upstream": "wechselrichter.fritz.box:502", "clients": []}]},
        config=config,
        runtime_yaml="",
        events=[{"message": "mobile_app_anna told"}],
    )
    text = "".join(
        zipfile.ZipFile(io.BytesIO(data)).read(n).decode()
        for n in zipfile.ZipFile(io.BytesIO(data)).namelist()
    )
    assert "wechselrichter" not in text and "anna" not in text
    assert "host-1:502" in text and "notify-service" in text


def test_notifications_update_retry_and_follow_the_language() -> None:
    from device_proxy.notify import RETRY_AFTER

    sent: list[tuple[str, dict[str, Any]]] = []
    now = [1000.0]
    notifier = Notifier(clock=lambda: now[0])
    notifier.available = True
    ok = [False]

    async def fake(path: str, data: dict[str, Any]) -> bool:
        sent.append((path, data))
        return ok[0]

    notifier._send = fake  # type: ignore[method-assign]

    async def run() -> None:
        now[0] += 90
        kwargs: dict[str, Any] = {"grace": 0, "dismiss": True, "service": "phone"}
        await notifier.update({"k": ("T", "one")}, **kwargs)
        assert len(sent) == 1  # failed
        await notifier.update({"k": ("T", "one")}, **kwargs)
        assert len(sent) == 1  # not again at once
        now[0] += RETRY_AFTER
        ok[0] = True
        await notifier.update({"k": ("T", "one")}, **kwargs)
        assert [p for p, _ in sent[1:]] == [
            "services/persistent_notification/create",
            "services/notify/phone",
        ]
        await notifier.update({"k": ("T", "two")}, **kwargs)
        assert sent[-1][0] == "services/persistent_notification/create"
        assert sent[-1][1]["message"] == "two"
        await notifier.update({}, **kwargs, resolved_message=True, language="en")
        assert sent[-1][1]["message"] == "OK again"

    asyncio.run(run())


def test_diagnostics_hide_the_own_mqtt_broker_and_its_login() -> None:
    import io
    import zipfile

    from device_proxy.diagnostics import build

    config = {
        "settings": {
            "mqtt_host": "emqx.example.org",
            "mqtt_user": "anna",
            "mqtt_password": "geheim",
        },
        "connections": [],
    }
    data = build(
        version="1",
        ser2net_version="4",
        snapshot={"error": "cannot reach emqx.example.org", "settings": dict(config["settings"])},
        config=config,
        runtime_yaml="",
        events=[],
    )
    archive = zipfile.ZipFile(io.BytesIO(data))
    text = "".join(archive.read(n).decode() for n in archive.namelist())
    assert "emqx.example" not in text and "geheim" not in text and "anna" not in text
    assert "mqtt-host" in text


def test_own_mqtt_broker_settings_are_checked() -> None:
    import pytest

    from device_proxy.model import Settings, ValidationError

    settings = Settings.from_dict({"mqtt_host": "emqx", "mqtt_port": 8883, "mqtt_tls": True})
    assert (settings.mqtt_host, settings.mqtt_port, settings.mqtt_tls) == ("emqx", 8883, True)
    with pytest.raises(ValidationError):
        Settings.from_dict({"mqtt_host": "not a host"})
    with pytest.raises(ValidationError):
        Settings.from_dict({"mqtt_port": 0})


def test_a_full_disk_does_not_move_the_history_aside(tmp_path: Path) -> None:
    import sqlite3

    import pytest

    from device_proxy.db import Database
    from device_proxy.events import EventLog

    db = Database(tmp_path / "h.db")

    class Full:
        def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
            raise sqlite3.OperationalError("database or disk is full")

        def close(self) -> None:
            pass

    real, db.conn = db.conn, Full()  # type: ignore[assignment]
    with pytest.raises(sqlite3.OperationalError):
        db.execute("SELECT 1")
    assert not list(tmp_path.glob("h.db.damaged-*"))
    log = EventLog(db)
    log.emit("info", "app_started", connections=0, active=0)  # not kept, but no error
    db.conn = real
