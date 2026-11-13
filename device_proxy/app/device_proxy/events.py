"""Events of the app: written to the app log, kept for the live log and stored as history.

An event is a kind plus values (`client_connected`, {"address": "192.168.1.20:50114"}); the
web interface words it in its own language, MESSAGES gives the English line for the app
log. The same event repeating quickly (a stick that keeps dropping out) is summed up: after
debounce_count of one kind for one connection and one client within debounce_minutes, further
ones only raise the count of the last entry and are logged once more when the burst is over.
"""

from __future__ import annotations

import contextlib
import json
import logging
import sqlite3
import time
from collections import deque
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from typing import Any

from .clients import host_of
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
    "enocean_failover",
    "enocean_failback",
    "client_refused",
    "client_refused_network",
    "client_refused_exclusive",
    "client_refused_blocked",
    "write_blocked",
    "write_blocked_register",
    "mqtt_connected",
    "mqtt_lost",
    "ser2net_start_failed",
    "proxy_failed",
    "proxy_restarted",
    "auto_restart_failed",
}
GONE = {"device_missing", "modbus_down", "enocean_down"}  # the device is away (for the history) ...
BACK = {"device_back", "device", "modbus_back", "enocean_back"}  # ... and there again
LIFE = {"app_started", "app_stopped"}  # nobody watches in between; a device still away says so
APP = "App"  # the name of events that belong to no connection
# values that entries written by an older version do not have
DEFAULTS: dict[str, dict[str, Any]] = {"app_started": {"version": "–"}}

MESSAGES = {
    "app_started": "Started version {version} with {connections} connections, {active} active",
    "app_stopped": "Stopped",
    "entity_ids_renamed": "Entity IDs changed to device_proxy_…: {count}, not changed: {failed}",
    "config_restored": "The configuration could not be used, running on the latest saved version",
    "config_lost": (
        "The configuration could not be read and no version is saved: started without connections"
    ),
    "config_salvaged": "The configuration could not be used, {dropped} part(s) left out",
    "history_damaged": "The history was damaged and started anew, the old file: {file}",
    "blocked_unreadable": "The blocked clients could not be read: no client is blocked now",
    "mqtt_connected": "MQTT connected to {broker}",
    "mqtt_lost": "MQTT not connected to {broker}: {error}",
    "mqtt_no_broker": "MQTT is on, but Home Assistant names no broker: the entities are off",
    "ser2net_start_failed": "ser2net cannot be started: {error}, trying again in {delay} s",
    "proxy_failed": "Connection stopped by an internal error: {error}, starting again in {delay} s",
    "proxy_restarted": "Connection started again after an internal error",
    "auto_restart_failed": "Automatic restart failed: {error}",
    "capture_full": "Recording ended, the file is full: {file}, {frames} frames",
    "capture_failed": "Recording ended, writing failed: {file}, {frames} frames: {error}",
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
    "enocean_failover": (
        "Goes on through the fallback {fallback} ({reason}), {unanswered} commands unanswered"
    ),
    "enocean_failback": "Back on its own gateway, the fallback {fallback} rests ({reason})",
    "enocean_fallback_ready": "Fallback {fallback} ready",
    "enocean_fallback_unready": "Fallback {fallback} not ready: {reason}",
    "enocean_fallback_promoted": (
        "The fallback's hardware became this gateway's: {new}; the old one ({old}): {action}"
    ),
    "duty_cycle_high": "{of_limit} % of the 1 % duty cycle used in the last hour",
    "client_dropped": "Client {address} stopped reading and was disconnected ({queued} bytes)",
    "base_id_set": "Base ID changed to {base_id}",
    "base_id_failed": "Base ID {base_id} not set: {result}",
    "capture_started": "Recording into {file}",
    "capture_locked": "Recording into {file}, only {peer} may send",
    "capture_stopped": "Recording ended: {file}, {frames} frames",
    "listen_failed": "Port {port} cannot be opened: {error}",
    "client_refused": "Client refused, all places taken: {address}",
    "client_refused_network": "Client refused, not from an allowed network: {address}",
    "client_refused_exclusive": "Client refused, maintenance only for {only}: {address}",
    "client_refused_blocked": "Blocked client refused: {address}",
    "client_new": "New client, never seen before: {address}",
    "client_blocked": "Client blocked, kept out of every connection: {address}",
    "client_blocked_not_custom": (
        "Client blocked, kept out of the app's Modbus and EnOcean connections, "
        "not of the ports of the own ser2net.yaml: {address}"
    ),
    "client_unblocked": "Client released: {address}",
    "clients_disconnected": "{count} client(s) disconnected ({by})",
    "connection_restarted": "Connection restarted ({by})",
    "usb_reset_failed": "USB reset failed: {error}",
    "power_cycled": "Power cycled with {switch}",
    "power_cycle_failed": "Power cycle with {switch} failed: {error}",
    "auto_restart_gave_up": (
        "Still no data after {count} automatic restarts: no further restarts until data comes"
    ),
    "write_blocked_register": (
        "Write refused (function {function}, register {register}) from {address}: outside the "
        "allowed registers"
    ),
    "exclusive_on": "Maintenance: only {host} may connect for {minutes} minutes",
    "exclusive_off": "Maintenance over ({reason}): all allowed clients may connect again",
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
    last_ts: float = 0.0  # when a summed-up entry last repeated

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
            "last_ts": self.last_ts or self.ts,
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
        self._bursts: dict[tuple[str | None, str, str], _Burst] = {}
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
        client = host_of(str(params.get("address", "")))  # each port is a new one: the host counts
        burst = self._burst((connection, kind, client), now) if kind in SUMMED else None
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

    def _burst(self, key: tuple[str | None, str, str], now: float) -> _Burst:
        burst = self._bursts.setdefault(key, _Burst())
        while burst.times and now - burst.times[0] > self.window:
            burst.times.popleft()
        if not burst.times:
            burst.summed = 0
        burst.times.append(now)
        return burst

    def flush_bursts(self) -> None:
        """Log bursts that are over with their total; called now and then."""
        now = self.clock()
        for key, burst in list(self._bursts.items()):
            if burst.times and now - burst.times[-1] <= self.window:
                continue
            if burst.summed > 1 and burst.last is not None:
                _LOGGER.info(
                    "[%s] %s (%s× in a row, summed up)",
                    burst.last.name,
                    burst.last.message,
                    burst.summed,
                )
            del self._bursts[key]  # a scan of the network must not stay in memory

    def _store(self, event: Event) -> int | None:
        if self.db is None:
            return None
        try:
            return self._insert(event)
        except sqlite3.Error as err:  # a full disk must not stop who reports the event
            _LOGGER.warning("Event not kept in the history: %s", err)
            return None

    def _insert(self, event: Event) -> int | None:
        assert self.db is not None
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
            with contextlib.suppress(sqlite3.Error):
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
        contains: str | None = None,
    ) -> list[Event]:
        if self.db is None:
            return []
        sql = (
            "SELECT id, ts, level, connection, name, kind, params, count, last_ts"
            " FROM events WHERE ts >= ?"
        )
        args: list[object] = [since]
        if connection is not None:
            sql += " AND connection = ?"
            args.append(connection)
        if kinds is not None:
            sql += f" AND kind IN ({', '.join('?' * len(kinds))})"
            args.extend(kinds)
        if contains:  # in the values, e.g. everything of one client
            escaped = contains.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            sql += " AND params LIKE ? ESCAPE '\\'"
            args.append(f"%{escaped}%")
        sql += " ORDER BY ts DESC, id DESC LIMIT ?"
        args.append(limit)
        events = []
        rows = self.db.execute(sql, tuple(args))
        for row_id, ts, level, conn, name, kind, params, count, last_ts in rows:
            try:
                values = json.loads(params)
            except ValueError:
                values = {}
            values = {**DEFAULTS.get(kind, {}), **values}
            events.append(Event(ts, level, conn, name, kind, values, count, row_id, 0, last_ts))
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
        kinds = GONE | BACK | LIFE
        for e in reversed(self.history(since=start - 86400 * 365, limit=100000, kinds=kinds)):
            if e.kind in LIFE:  # a proxy reports no return after a restart, only a new loss
                for connection, began in missing_since.items():
                    result[connection]["missing_seconds"] += max(0.0, e.ts - max(began, start))
                missing_since.clear()
                continue
            if e.connection is None:
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
