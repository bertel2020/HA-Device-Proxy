"""The history of the card Clients: when which computer was connected where."""

from pathlib import Path

from device_proxy.controller import Controller
from device_proxy.db import Database
from device_proxy.events import EventLog
from device_proxy.sessions import (
    FLUSH_SECONDS,
    GONE_SECONDS,
    MERGE_SECONDS,
    REFUSED_MERGE_SECONDS,
    SHORT_SECONDS,
    ClientSessions,
)
from device_proxy.store import Store
from device_proxy.trace import TraceHub

A = "192.168.1.20"
ADDR = f"{A}:5000"


def make(tmp_path: Path) -> tuple[ClientSessions, list[float], Database]:
    now = [100000.0]
    db = Database(tmp_path / "history.db")
    return ClientSessions(db, clock=lambda: now[0]), now, db


def test_a_visit_is_one_row_with_its_traffic(tmp_path: Path) -> None:
    sessions, now, _ = make(tmp_path)
    sessions.connected(ADDR, "c1", "Zähler")
    assert [r["end"] for r in sessions.history(A, 0)] == [None]
    now[0] += 500
    sessions.tick({("c1", ADDR): (900, 40)})
    assert sessions.history(A, 0)[0]["to_client"] == 900  # also while it runs
    now[0] += 500
    sessions.disconnected(ADDR, "c1", 1000, 50)
    row = sessions.history(A, 0)[0]
    assert (row["start"], row["end"], row["count"]) == (100000.0, 101000.0, 1)
    assert (row["to_client"], row["from_client"], row["unknown"]) == (1000, 50, False)
    assert sessions.history("192.168.1.21", 0) == []


def test_without_exact_traffic_the_last_status_counts(tmp_path: Path) -> None:
    sessions, now, _ = make(tmp_path)
    sessions.connected(ADDR, "c1", "Zähler")
    sessions.tick({("c1", ADDR): (70, 7)})
    now[0] += 10
    sessions.disconnected(ADDR, "c1")  # ser2net says only that it left
    assert sessions.history(A, 0)[0]["to_client"] == 70


def test_a_long_visit_is_not_continued(tmp_path: Path) -> None:
    sessions, now, _ = make(tmp_path)
    sessions.connected(ADDR, "c1", "Zähler")
    now[0] += SHORT_SECONDS + 1
    sessions.disconnected(ADDR, "c1")
    now[0] += 5
    sessions.connected(f"{A}:5001", "c1", "Zähler")
    assert [r["count"] for r in sessions.history(A, 0)] == [1, 1]


def test_short_visits_are_one_row_and_a_new_one_after_a_pause(tmp_path: Path) -> None:
    sessions, now, _ = make(tmp_path)
    for port in range(12):
        sessions.connected(f"{A}:{port}", "c1", "Zähler")
        now[0] += 2
        sessions.disconnected(f"{A}:{port}", "c1", 10, 1)
        now[0] += MERGE_SECONDS - 5
    rows = sessions.history(A, 0)
    assert len(rows) == 1 and rows[0]["count"] == 12 and rows[0]["to_client"] == 120
    now[0] += 10  # now the pause is too long
    sessions.connected(f"{A}:99", "c1", "Zähler")
    assert len(sessions.history(A, 0)) == 2


def test_a_series_ends_when_the_client_stays(tmp_path: Path) -> None:
    sessions, now, _ = make(tmp_path)
    for port in range(3):
        sessions.connected(f"{A}:{port}", "c1", "Zähler")
        now[0] += 2
        sessions.disconnected(f"{A}:{port}", "c1")
        now[0] += 2
    stays_from = now[0]
    sessions.connected(f"{A}:9", "c1", "Zähler")
    now[0] += SHORT_SECONDS + 1
    sessions.tick({("c1", f"{A}:9"): (5, 5)})
    settled, series = sessions.history(A, 0)
    assert (series["count"], series["end"]) == (3, stays_from)
    assert (settled["count"], settled["start"], settled["end"]) == (1, stays_from, None)
    assert settled["to_client"] == 5


def test_two_sockets_of_a_host_are_one_row(tmp_path: Path) -> None:
    sessions, now, _ = make(tmp_path)
    sessions.connected(ADDR, "c1", "Zähler")
    now[0] += SHORT_SECONDS + 10
    sessions.connected(f"{A}:5001", "c1", "Zähler")
    now[0] += SHORT_SECONDS + 10
    sessions.disconnected(f"{A}:5001", "c1", 1, 1)
    sessions.tick({("c1", ADDR): (2, 2)})
    row = sessions.history(A, 0)
    assert len(row) == 1 and row[0]["end"] is None and row[0]["to_client"] == 3
    sessions.disconnected(ADDR, "c1", 2, 2)
    assert sessions.history(A, 0)[0]["end"] == now[0]


def test_each_connection_has_its_own_rows(tmp_path: Path) -> None:
    sessions, _, _ = make(tmp_path)
    sessions.connected(ADDR, "c1", "Zähler")
    sessions.connected(f"{A}:5001", "c2", "Pumpe")
    assert {r["connection"] for r in sessions.history(A, 0)} == {"c1", "c2"}


def test_a_client_that_left_without_a_word(tmp_path: Path) -> None:
    sessions, now, _ = make(tmp_path)
    sessions.connected(ADDR, "c1", "Zähler")
    sessions.tick({})  # just connected, maybe not in the status yet
    assert sessions.history(A, 0)[0]["end"] is None
    now[0] += GONE_SECONDS + 1
    sessions.tick({}, check_gone=False)  # no answer from ser2net: nobody can say
    assert sessions.history(A, 0)[0]["end"] is None
    sessions.tick({})
    assert sessions.history(A, 0)[0]["end"] == now[0]


def test_refused_attempts_are_summed_up(tmp_path: Path) -> None:
    sessions, now, _ = make(tmp_path)
    for _ in range(3):
        sessions.refused(ADDR, "c1", "Zähler", "network")
        now[0] += 10
    rows = sessions.history(A, 0)
    assert len(rows) == 1 and (rows[0]["refused"], rows[0]["count"]) == ("network", 3)
    now[0] += REFUSED_MERGE_SECONDS + 1
    sessions.refused(ADDR, "c1", "Zähler", "network")
    sessions.refused(ADDR, "c1", "Zähler", "full")
    assert len(sessions.history(A, 0)) == 3


def test_repeats_are_written_rarely(tmp_path: Path) -> None:
    sessions, now, db = make(tmp_path)
    written = []
    db.conn.set_trace_callback(written.append)
    sessions.connected(ADDR, "c1", "Zähler")
    now[0] += 1
    sessions.disconnected(ADDR, "c1")
    written.clear()
    for port in range(50):
        now[0] += 1
        sessions.connected(f"{A}:{port}", "c1", "Zähler")
        now[0] += 1
        sessions.disconnected(f"{A}:{port}", "c1")
        sessions.tick({})
    assert sum("UPDATE" in sql for sql in written) == 0
    now[0] += FLUSH_SECONDS
    sessions.tick({})
    assert sum("UPDATE" in sql for sql in written) == 1


def test_after_a_power_cut_the_end_is_unknown(tmp_path: Path) -> None:
    sessions, now, db = make(tmp_path)
    sessions.connected(ADDR, "c1", "Zähler")
    now[0] += FLUSH_SECONDS
    sessions.tick({("c1", ADDR): (1, 1)})
    written_at = now[0]
    now[0] += 9999  # no shutdown; the next start finds the row open
    row = ClientSessions(db, clock=lambda: now[0]).history(A, 0)[0]
    assert row["end"] == written_at and row["unknown"] is True


def test_a_clean_end_closes_the_rows(tmp_path: Path) -> None:
    sessions, now, db = make(tmp_path)
    sessions.connected(ADDR, "c1", "Zähler")
    sessions.tick({("c1", ADDR): (8, 4)})
    now[0] += 30
    sessions.shutdown()
    row = ClientSessions(db, clock=lambda: now[0]).history(A, 0)[0]
    assert (row["end"], row["unknown"], row["to_client"]) == (now[0], False, 8)


def test_history_window_prune_and_forget(tmp_path: Path) -> None:
    sessions, now, _ = make(tmp_path)
    sessions.connected(ADDR, "c1", "Zähler")
    sessions.disconnected(ADDR, "c1")
    now[0] += 86400 * 2
    assert sessions.history(A, now[0] - 86400) == []
    assert len(sessions.history(A, now[0] - 86400 * 3)) == 1
    sessions.connected(f"{A}:6000", "c2", "Pumpe")  # still open: stays, however old
    now[0] += 86400 * 40
    sessions.prune(30)
    assert [r["connection"] for r in sessions.history(A, 0)] == ["c2"]
    sessions.forget(A)
    assert sessions.history(A, 0) == []
    sessions.disconnected(f"{A}:6000", "c2")  # nothing left of it, no error


def test_without_a_database_nothing_breaks() -> None:
    sessions = ClientSessions(None)
    sessions.connected(ADDR, "c1", "Zähler")
    sessions.tick({})
    sessions.disconnected(ADDR, "c1")
    assert sessions.history(A, 0) == []


def _controller(tmp_path: Path) -> Controller:
    db = Database(tmp_path / "history.db")
    return Controller(
        Store(db, tmp_path / "config.json"),
        EventLog(db),
        tmp_path / "ser2net.yaml",
        custom_file=tmp_path / "own.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )


def test_the_controller_follows_proxies_and_ser2net(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.known_clients.known[A] = 1.0
    emit = controller._proxy_event("c1")
    emit("info", "client_connected", address=ADDR)
    emit("info", "client_disconnected", address=ADDR, bytes_to_client=64, bytes_from_client=8)
    row = controller.sessions.history(A, 0)[0]
    assert (row["to_client"], row["from_client"]) == (64, 8) and row["end"] is not None
    # the byte counts stay out of the event itself
    assert "bytes_to_client" not in controller.events.live[-1].params

    emit("warning", "client_refused_network", address=f"{A}:7000")
    assert controller.sessions.history(A, 0)[0]["refused"] == "network"

    controller._admin_event("new connection", "port3", f"{A}:8000")
    assert controller.sessions.history(A, 0)[0]["connection"] == "port3"


def test_hosts_off_the_list_leave_no_rows(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.known_clients.learn_until = 0
    controller.known_clients.new = {f"10.0.0.{i}": {} for i in range(50)}  # the list is full
    emit = controller._proxy_event("c1")
    emit("info", "client_connected", address="10.9.9.9:1")
    emit("warning", "client_refused_network", address="10.9.9.8:1")
    assert controller.sessions.history("10.9.9.9", 0) == []
    assert controller.sessions.history("10.9.9.8", 0) == []
