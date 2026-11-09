from pathlib import Path

import pytest

from device_proxy.clients import KnownClients
from device_proxy.db import Database
from device_proxy.events import EventLog
from device_proxy.mqtt import MqttClient
from device_proxy.store import Store


def test_a_burst_is_summed_up(tmp_path: Path) -> None:
    now = [1000.0]
    log = EventLog(
        Database(tmp_path / "history.db"),
        debounce_count=3,
        debounce_minutes=5,
        clock=lambda: now[0],
    )
    for _ in range(10):
        log.emit("warning", "device_missing", connection="0000000a", name="eHZ", device="/dev/x")
        now[0] += 10
    history = log.history()
    assert [e.count for e in history] == [8, 1, 1]
    now[0] += 3600
    log.emit("warning", "device_missing", connection="0000000a", name="eHZ", device="/dev/x")
    assert [e.count for e in log.history()] == [1, 8, 1, 1]
    latest = log.history()[0]
    assert (latest.name, latest.params) == ("eHZ", {"device": "/dev/x"})
    assert latest.message == "Device missing: /dev/x"


@pytest.mark.parametrize(
    "kind", ["client_refused_network", "client_refused_exclusive", "client_refused_blocked"]
)
def test_refused_clients_are_summed_up_and_worded(kind: str) -> None:
    from device_proxy.events import MESSAGES, SUMMED, EventLog

    log = EventLog(None, debounce_count=2, debounce_minutes=5, clock=lambda: 100.0)
    log._store = lambda event: 1  # type: ignore[method-assign]
    log._store_count = lambda row, now, count: None  # type: ignore[method-assign]
    for _ in range(6):  # a port scan is one entry, not six
        event = log.emit("warning", kind, connection="c", name="N", address="192.0.2.7:1", only="x")
    assert kind in SUMMED and kind in MESSAGES
    assert event.count > 1 and "192.0.2.7:1" in event.message


def _log(tmp_path: Path, now: list[float]) -> EventLog:
    return EventLog(Database(tmp_path / "history.db"), clock=lambda: now[0])


def test_repeats_are_summed_per_client(tmp_path: Path) -> None:
    now = [1000.0]
    log = _log(tmp_path, now)
    for host in ("10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"):
        log.emit("warning", "client_refused_network", connection="m", name="M", address=f"{host}:1")
        now[0] += 1
    shown = {e.params["address"] for e in log.history()}
    assert shown == {f"10.0.0.{n}:1" for n in range(1, 6)}


def test_a_new_port_of_one_client_is_a_repeat(tmp_path: Path) -> None:
    now = [1000.0]
    log = _log(tmp_path, now)
    for port in range(6):
        log.emit("info", "client_connected", connection="m", name="M", address=f"10.0.0.1:{port}")
        now[0] += 1
    latest = log.history()[0]
    assert [e.count for e in log.history()] == [4, 1, 1]
    assert latest.params["address"] == "10.0.0.1:2"  # the row stays as it was written
    assert (latest.ts, latest.last_ts) == (1002.0, 1005.0)
    assert latest.to_dict()["last_ts"] == 1005.0


def test_flushing_forgets_what_is_over(tmp_path: Path) -> None:
    now = [1000.0]
    log = _log(tmp_path, now)
    log.emit("info", "client_connected", connection="m", name="M", address="10.0.0.1:1")
    now[0] += 3600
    log.flush_bursts()
    assert not log._bursts


def test_a_start_ends_an_outage_a_proxy_will_not_report_back(tmp_path: Path) -> None:
    now = [10_000_000.0]
    log = _log(tmp_path, now)
    log.emit("warning", "modbus_down", connection="m", name="M", target="x", error="e")
    now[0] += 3600
    log.emit("info", "app_started", version="1", connections=1, active=1)
    now[0] += 9 * 86400
    stats = log.stats(10)["m"]
    assert stats["missing_seconds"] == 3600
    assert stats["drops"] == 1


def test_an_outage_ends_with_the_app_and_a_new_one_counts_after_the_start(tmp_path: Path) -> None:
    now = [10_000_000.0]
    log = _log(tmp_path, now)
    log.emit("warning", "modbus_down", connection="m", name="M", target="x", error="e")
    now[0] += 100
    log.emit("info", "app_stopped")
    now[0] += 1000  # the app is off: nobody knows
    log.emit("info", "app_started", version="1", connections=1, active=1)
    log.emit("warning", "modbus_down", connection="m", name="M", target="x", error="e")
    now[0] += 50
    assert log.stats(10)["m"]["missing_seconds"] == 150


def test_an_old_start_entry_has_no_version(tmp_path: Path) -> None:
    now = [1000.0]
    log = _log(tmp_path, now)
    log.emit("info", "app_started", connections=2, active=1)
    assert log.history()[0].message == "Started version – with 2 connections, 1 active"


def test_history_finds_a_client_among_the_values(tmp_path: Path) -> None:
    now = [1000.0]
    log = _log(tmp_path, now)
    log.emit("info", "client_connected", connection="m", name="M", address="10.0.0.1:1")
    log.emit("info", "client_connected", connection="m", name="M", address="10.0.0.10:1")
    assert len(log.history(contains="10.0.0.1:")) == 1
    assert not log.history(contains="10.0.0_1")  # no wildcard


def test_problems_before_the_events_are_kept(tmp_path: Path) -> None:
    broken = tmp_path / "config.json"
    broken.write_text("{", encoding="utf-8")
    store = Store(None, broken)
    store.load()
    store.load()  # the start loads it more than once
    assert store.problems == [("config_lost", {})]

    known = tmp_path / "known.json"
    (tmp_path / "blocked_clients.json").write_text("{", encoding="utf-8")
    assert KnownClients(known).problems == [("blocked_unreadable", {})]

    damaged = tmp_path / "damaged.db"
    damaged.write_bytes(b"this is no database, not at all" * 100)
    assert [kind for kind, _ in Database(damaged).problems] == ["history_damaged"]


def test_mqtt_reports_only_changes() -> None:
    seen: list[tuple[bool, str]] = []

    async def nothing(*_: object) -> None:
        return None

    client = MqttClient("x", nothing, nothing, on_state=lambda up, why: seen.append((up, why)))
    client.error = "refused"
    client._report(False)
    client._report(False)
    client.error = ""
    client._report(True)
    client._report(True)
    assert seen == [(False, "refused"), (True, "")]


async def test_the_controller_reports_problems_and_a_failed_ser2net_start(tmp_path: Path) -> None:
    from device_proxy.controller import Controller
    from device_proxy.trace import TraceHub

    db = Database(tmp_path / "history.db")
    store = Store(db, tmp_path / "config.json")
    store.problems.append(("config_restored", {}))
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    await controller._report_problems()
    await controller._report_problems()
    assert [(e.level, e.kind) for e in controller.events.history()] == [
        ("error", "config_restored")
    ]

    controller.ser2net.start_error = "no such file"
    controller._ser2net_ended(None, 1)
    latest = controller.events.history()[0]
    assert (latest.level, latest.kind) == ("error", "ser2net_start_failed")


async def test_no_broker_is_no_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    from device_proxy import ha_mqtt
    from device_proxy.controller import Controller
    from device_proxy.trace import TraceHub

    monkeypatch.setattr(ha_mqtt, "supervisor_broker", lambda: None)
    db = Database(tmp_path / "history.db")
    controller = Controller(
        Store(db, tmp_path / "config.json"),
        EventLog(db),
        tmp_path / "s.yaml",
        trace=TraceHub(tmp_path / "t", tmp_path / "shm"),
    )
    await controller.mqtt.run(asyncio.Event())
    assert [(e.level, e.kind) for e in controller.events.history()] == [("info", "mqtt_no_broker")]
