"""Events of the app: written to the app log, kept for the live log and stored as history.

An event is a kind plus values (`client_connected`, {"address": "192.168.1.20:50114"}); the
web interface words it in its own language, MESSAGES gives the English line for the app
log. The same event repeating quickly (a stick that keeps dropping out) is summed up: after
debounce_count of one kind for one connection within debounce_minutes, further ones only
raise the count of the last entry and are logged once more when the burst is over.
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from typing import Any

from .db import Database

_LOGGER = logging.getLogger("device_proxy")

LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}
LIVE_SIZE = 1000
SUMMED = {
    "device_missing",
    "device_back",
    "client_connected",
    "client_disconnected",
    "modbus_down",
    "modbus_back",
    "enocean_down",
    "enocean_back",
    "client_refused",
    "write_blocked",
}
GONE = {"device_missing", "modbus_down", "enocean_down"}  # the device is away (for the history) ...
BACK = {"device_back", "device", "modbus_back", "enocean_back"}  # ... and there again
APP = "App"  # the name of events that belong to no connection

MESSAGES = {
    "app_started": "Started with {connections} connections, {active} active",
    "connection_loaded": (
        "{state}: {device} · {format} · {mode} · port {port} · up to {max_clients} clients"
    ),
    "config_changed": "Configuration saved: {summary}",
    "tool_write": (
        "Written with the tool: unit {unit}, function {function}, address {address} = {values}"
    ),
    "tool_write_failed": (
        "Writing with the tool failed: unit {unit}, function {function}, address {address}"
    ),
    "clients_reconnect": "{count} client(s) disconnected so the change takes effect",
    "client_connected": "Client connected: {address}",
    "client_disconnected": "Client disconnected: {address}",
    "client_stuck": (
        "Client {address} does not read ({queued} bytes waiting); "
        "all clients of this connection are slowed down"
    ),
    "stuck_disconnected": "Clients disconnected because {address} did not read",
    "device": "Device found: {device} → {target}",
    "device_back": "Device back: {device} → {target}",
    "device_missing": "Device missing: {device}",
    "keep_open_failed": "Could not keep the device open: {error}",
    "ser2net_restart": "ser2net ended (exit code {code}), starting again in {delay} s",
    "line_errors": (
        "Line errors since start: {frame} frame, {parity} parity, {overrun} overrun, "
        "{buffer_overrun} buffer overrun, {break} break"
    ),
    "latency_read_only": ("FTDI latency could not be set to 1 ms: /sys is read-only for the app"),
    "custom_saved": "Own ser2net.yaml saved ({connections} connections)",
    "custom_invalid": "Own ser2net.yaml cannot be used, nothing is shared: {errors}",
    "imported": "Import: {taken} connections taken over, {skipped} skipped, {notes} notes",
    "import_failed": "Import failed: {error}",
    "modbus_loaded": (
        "{state}: Modbus {link} {target} · port {port} · up to {max_clients} clients"
    ),
    "modbus_down": "Device not reachable: {target} ({error})",
    "modbus_back": "Device reachable again: {target}",
    "enocean_loaded": (
        "{state}: EnOcean {protocol} {target} · port {port} · up to {max_clients} clients"
    ),
    "enocean_down": "Gateway not reachable: {target} ({error})",
    "enocean_back": "Gateway reachable again: {target}",
    "duty_cycle_high": "{of_limit} % of the 1 % duty cycle used in the last hour",
    "client_dropped": "Client {address} stopped reading and was disconnected ({queued} bytes)",
    "capture_started": "Capture into {file}",
    "capture_locked": "Capture into {file}, only {peer} may send",
    "capture_stopped": "Capture ended: {file}, {frames} frames",
    "listen_failed": "Port {port} cannot be opened: {error}",
    "client_refused": "Client refused, all places taken: {address}",
    "write_blocked": "Write refused (function {function}) from {address}",
}


def message(kind: str, params: dict[str, Any]) -> str:
    try:
        return MESSAGES[kind].format(**params)
    except (KeyError, IndexError, ValueError):
        return f"{kind} {params}"


@dataclass
class Event:
    ts: float
    level: str
    connection: str | None  # connection id, None for the app itself
    name: str  # connection name at the time, APP for the app itself
    kind: str
    params: dict[str, Any]
    count: int = 1
    id: int | None = None
    seq: int = 0  # increases with every emit (also when a summed-up entry is counted on)

    @property
    def message(self) -> str:
        return message(self.kind, self.params)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ts": self.ts,
            "level": self.level,
            "connection": self.connection,
            "name": self.name,
            "kind": self.kind,
            "params": self.params,
            "message": self.message,
            "count": self.count,
            "seq": self.seq,
        }


@dataclass
class _Burst:
    times: deque[float] = field(default_factory=deque)
    row: int | None = None
    summed: int = 0
    last: Event | None = None


class EventLog:
    def __init__(
        self,
        db: Database | None,
        *,
        debounce_count: int = 3,
        debounce_minutes: int = 5,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.db = db
        self.debounce_count = debounce_count
        self.window = debounce_minutes * 60
        self.clock = clock
        self.live: deque[Event] = deque(maxlen=LIVE_SIZE)
        self.listeners: list[Callable[[Event], None]] = []
        self._bursts: dict[tuple[str | None, str], _Burst] = {}
        self.seq = 0

    def emit(
        self,
        level: str,
        kind: str,
        *,
        connection: str | None = None,
        name: str = APP,
        **params: Any,
    ) -> Event:
        now = self.clock()
        self.seq += 1
        event = Event(now, level, connection, name, kind, params, seq=self.seq)
        burst = self._burst(connection, kind, now) if kind in SUMMED else None
        if burst is not None:
            burst.last = event
        if burst is not None and len(burst.times) > self.debounce_count and burst.row:
            burst.summed += 1
            event.count = burst.summed
            event.id = burst.row
            self._store_count(burst.row, now, burst.summed)
        else:
            _LOGGER.log(LEVELS.get(level, logging.INFO), "[%s] %s", name, event.message)
            event.id = self._store(event)
            if burst is not None:
                burst.row, burst.summed = event.id, 1
        self.live.append(event)
        for listener in self.listeners:
            listener(event)
        return event

    def _burst(self, connection: str | None, kind: str, now: float) -> _Burst:
        burst = self._bursts.setdefault((connection, kind), _Burst())
        while burst.times and now - burst.times[0] > self.window:
            burst.times.popleft()
        if not burst.times:
            burst.summed = 0
        burst.times.append(now)
        return burst

    def flush_bursts(self) -> None:
        """Log bursts that are over with their total; called now and then."""
        now = self.clock()
        for burst in self._bursts.values():
            if burst.times and now - burst.times[-1] > self.window and burst.summed > 1:
                if burst.last is not None:
                    _LOGGER.info(
                        "[%s] %s (%s× in a row, summed up)",
                        burst.last.name,
                        burst.last.message,
                        burst.summed,
                    )
                burst.summed = 0
                burst.times.clear()

    def _store(self, event: Event) -> int | None:
        if self.db is None:
            return None
        cursor = self.db.execute(
            "INSERT INTO events (ts, level, connection, name, kind, params, count, last_ts)"
            " VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (
                event.ts,
                event.level,
                event.connection,
                event.name,
                event.kind,
                json.dumps(event.params, ensure_ascii=False),
                event.ts,
            ),
        )
        return cursor.lastrowid

    def _store_count(self, row: int, now: float, count: int) -> None:
        if self.db is not None:
            self.db.execute(
                "UPDATE events SET count = ?, last_ts = ? WHERE id = ?", (count, now, row)
            )

    def history(
        self,
        *,
        connection: str | None = None,
        since: float = 0,
        limit: int = 500,
        kinds: Collection[str] | None = None,
    ) -> list[Event]:
        if self.db is None:
            return []
        sql = (
            "SELECT id, ts, level, connection, name, kind, params, count FROM events WHERE ts >= ?"
        )
        args: list[object] = [since]
        if connection is not None:
            sql += " AND connection = ?"
            args.append(connection)
        if kinds is not None:
            sql += f" AND kind IN ({', '.join('?' * len(kinds))})"
            args.extend(kinds)
        sql += " ORDER BY ts DESC, id DESC LIMIT ?"
        args.append(limit)
        events = []
        for row_id, ts, level, conn, name, kind, params, count in self.db.execute(sql, tuple(args)):
            try:
                values = json.loads(params)
            except ValueError:
                values = {}
            events.append(Event(ts, level, conn, name, kind, values, count, row_id))
        return events

    def since(self, seq: int) -> list[Event]:
        """Live events after the given sequence number (for the web interface)."""
        return [e for e in self.live if e.seq > seq]

    def stats(self, days: int, now: float | None = None) -> dict[str, dict[str, Any]]:
        """Per connection over the last days: drops, time without device, drops per day."""
        now = self.clock() if now is None else now
        start = now - days * 86400
        result: dict[str, dict[str, Any]] = {}
        missing_since: dict[str, float] = {}
        for e in reversed(self.history(since=start - 86400 * 365, limit=100000, kinds=GONE | BACK)):
            if e.connection is None or e.kind not in GONE | BACK:
                continue
            entry = result.setdefault(
                e.connection, {"drops": 0, "missing_seconds": 0.0, "per_day": [0] * days}
            )
            if e.kind in GONE:
                missing_since.setdefault(e.connection, e.ts)
                if e.ts >= start:
                    entry["drops"] += e.count
                    day = min(int((e.ts - start) // 86400), days - 1)
                    entry["per_day"][day] += e.count
            elif e.connection in missing_since:
                began = max(missing_since.pop(e.connection), start)
                entry["missing_seconds"] += max(0.0, e.ts - began)
        for connection, began in missing_since.items():
            result[connection]["missing_seconds"] += now - max(began, start)
        for entry in result.values():
            entry["availability"] = max(0.0, 1 - entry["missing_seconds"] / (days * 86400))
        return result

    def prune(self, days: int) -> int:
        """Remove history older than this many days; returns how many rows went."""
        if self.db is None:
            return 0
        cutoff = self.clock() - days * 86400
        removed = self.db.execute("DELETE FROM events WHERE ts < ?", (cutoff,)).rowcount
        if removed > 1000:
            self.db.execute("VACUUM")
        return removed
