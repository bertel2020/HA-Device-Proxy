from pathlib import Path

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
