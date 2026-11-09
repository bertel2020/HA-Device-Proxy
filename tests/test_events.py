from pathlib import Path

import pytest

from device_proxy.db import Database
from device_proxy.events import EventLog


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
