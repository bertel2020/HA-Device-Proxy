"""When which computer was connected to which connection, for the card Clients.

The events are no source for this: repeats of one kind on one connection are summed up without
their address, so a client that keeps reconnecting would hide the others. A row here is one
host on one connection from start to end, with what went through it.

A short visit followed by the next within a minute continues the row, however often: a client
that polls or keeps dropping out is one row with a count, not thousands. Once such a client
stays, the row ends where that visit began and a new one goes on. Refused attempts are rows
too, summed up the same way. A row that repeats is written at most every few minutes, the
others when they begin and end.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .clients import host_of, plain_host
from .db import Database

_LOGGER = logging.getLogger(__name__)

SHORT_SECONDS = 120  # a visit shorter than this may be continued by the next one
MERGE_SECONDS = 60  # ... that comes within this time
REFUSED_MERGE_SECONDS = 600  # refused attempts this close together are one row
GONE_SECONDS = 60  # just connected, maybe not in the status yet
FLUSH_SECONDS = 300  # a row that changes all the time is written this often

Traffic = tuple[int, int]  # bytes to the client, bytes from the client


@dataclass
class _Visit:
    """One socket of a host."""

    since: float
    to_client: int = 0
    from_client: int = 0


@dataclass
class _Row:
    id: int | None
    host: str
    connection: str
    name: str
    start: float
    refused: str | None = None  # why the attempts were refused; None: a real connection
    end: float | None = None
    count: int = 1
    to_client: int = 0  # visits that are over
    from_client: int = 0
    last_short: bool = False  # the visit that ended this row was a short one
    visits: dict[str, _Visit] = field(default_factory=dict)
    dirty: bool = False
    written: float = 0.0


class ClientSessions:
    def __init__(self, db: Database | None, *, clock: Callable[[], float] = time.time) -> None:
        self.db = db
        self.clock = clock
        self._rows: dict[tuple[str, str, str | None], _Row] = {}
        # still open from the last run: it ended without a word (a power cut), somewhen after
        # the row was last written
        self._execute(
            "UPDATE client_sessions SET end = updated, unknown = 1 WHERE end IS NULL",
        )

    def _execute(self, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Cursor | None:
        if self.db is None:
            return None
        try:
            return self.db.execute(sql, params)
        except sqlite3.Error as err:  # a full disk must not stop who reports the connection
            _LOGGER.warning("Client history not written: %s", err)
            return None

    def _insert(self, row: _Row) -> None:
        cursor = self._execute(
            "INSERT INTO client_sessions (host, connection, name, start, end, refused, updated)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (row.host, row.connection, row.name, row.start, row.end, row.refused, self.clock()),
        )
        row.id = cursor.lastrowid if cursor is not None else None
        row.written = self.clock()

    def _write(self, row: _Row) -> None:
        now = self.clock()
        to_client = row.to_client + sum(v.to_client for v in row.visits.values())
        from_client = row.from_client + sum(v.from_client for v in row.visits.values())
        self._execute(
            "UPDATE client_sessions SET end = ?, count = ?, to_client = ?, from_client = ?,"
            " updated = ? WHERE id = ?",
            (row.end, row.count, to_client, from_client, now, row.id),
        )
        row.dirty, row.written = False, now

    def connected(self, address: str, connection: str, name: str) -> None:
        host = plain_host(host_of(address))
        now = self.clock()
        key = (host, connection, None)
        row = self._rows.get(key)
        if row is not None and (
            row.visits or (row.last_short and row.end and now - row.end <= MERGE_SECONDS)
        ):
            row.count += 1
            row.end, row.dirty = None, True
        else:
            if row is not None and row.dirty:
                self._write(row)
            row = self._open(host, connection, name, now)
            self._rows[key] = row
        row.visits[address] = _Visit(now)

    def _open(self, host: str, connection: str, name: str, start: float) -> _Row:
        row = _Row(None, host, connection, name, start)
        self._insert(row)
        return row

    def disconnected(
        self,
        address: str,
        connection: str,
        to_client: int | None = None,
        from_client: int | None = None,
    ) -> None:
        """A client left; the proxies know its exact traffic, for ser2net the last status counts."""
        row = self._rows.get((plain_host(host_of(address)), connection, None))
        if row is None or address not in row.visits:
            return
        visit = row.visits[address]
        if to_client is not None and from_client is not None:
            visit.to_client, visit.from_client = to_client, from_client
        self._leave(row, address, visit)

    def _leave(self, row: _Row, address: str, visit: _Visit) -> None:
        del row.visits[address]
        row.to_client += visit.to_client
        row.from_client += visit.from_client
        if row.visits:
            row.dirty = True
            return
        now = self.clock()
        row.end, row.last_short = now, now - visit.since < SHORT_SECONDS
        if row.count == 1:
            self._write(row)
        else:
            row.dirty = True

    def refused(self, address: str, connection: str, name: str, reason: str) -> None:
        host = plain_host(host_of(address))
        now = self.clock()
        key = (host, connection, reason)
        row = self._rows.get(key)
        if row is not None and row.end and now - row.end <= REFUSED_MERGE_SECONDS:
            row.count += 1
            row.end, row.dirty = now, True
            return
        if row is not None and row.dirty:
            self._write(row)
        row = _Row(None, host, connection, name, now, refused=reason, end=now)
        self._insert(row)
        self._rows[key] = row

    def tick(self, live: Mapping[tuple[str, str], Traffic], *, check_gone: bool = True) -> None:
        """Every few seconds: the clients as the status knows them, (connection, address) →
        traffic. One it no longer lists has left without a word (ser2net restarted)."""
        now = self.clock()
        for key, row in list(self._rows.items()):
            for address, visit in list(row.visits.items()):
                traffic = live.get((row.connection, address))
                if traffic is not None:
                    if traffic != (visit.to_client, visit.from_client):
                        visit.to_client, visit.from_client = traffic
                        row.dirty = True
                elif check_gone and now - visit.since > GONE_SECONDS:
                    self._leave(row, address, visit)
            row = self._settled(key, row, now)
            if row.dirty and now - row.written >= FLUSH_SECONDS:
                self._write(row)
            keep = REFUSED_MERGE_SECONDS if row.refused else MERGE_SECONDS
            if not row.visits and row.end and now - row.end > keep:
                if row.dirty:
                    self._write(row)
                del self._rows[key]

    def _settled(self, key: tuple[str, str, str | None], row: _Row, now: float) -> _Row:
        """A client that kept coming back has stayed: the series is over, a new row goes on."""
        if row.count < 2 or len(row.visits) != 1:
            return row
        address, visit = next(iter(row.visits.items()))
        if visit.since <= row.start or now - visit.since < SHORT_SECONDS:
            return row
        row.visits = {}
        row.count -= 1
        row.end = visit.since
        self._write(row)
        settled = self._open(row.host, row.connection, row.name, visit.since)
        settled.visits[address] = visit
        settled.dirty = True  # what this visit has already carried
        self._rows[key] = settled
        return settled

    def shutdown(self) -> None:
        """The app ends, and with it every connection."""
        now = self.clock()
        for row in self._rows.values():
            if row.visits:
                row.to_client += sum(v.to_client for v in row.visits.values())
                row.from_client += sum(v.from_client for v in row.visits.values())
                row.visits, row.end = {}, now
                row.dirty = True
            if row.dirty:
                self._write(row)

    def history(self, host: str, since: float) -> list[dict[str, Any]]:
        """The rows of this host that reach into the time from since on, newest first."""
        for row in self._rows.values():
            if row.host == host and row.dirty:
                self._write(row)
        cursor = self._execute(
            "SELECT id, connection, name, start, end, count, to_client, from_client, refused,"
            " unknown FROM client_sessions WHERE host = ? AND (end IS NULL OR end >= ?)"
            " ORDER BY start DESC, id DESC LIMIT 2000",
            (host, since),
        )
        if cursor is None:
            return []
        keys = (
            "id",
            "connection",
            "name",
            "start",
            "end",
            "count",
            "to_client",
            "from_client",
            "refused",
        )
        return [
            {**dict(zip(keys, values[:-1], strict=True)), "unknown": bool(values[-1])}
            for values in cursor
        ]

    def forget(self, host: str) -> None:
        """Taken off the list: its history goes too."""
        for key in [k for k in self._rows if k[0] == host]:
            del self._rows[key]
        self._execute("DELETE FROM client_sessions WHERE host = ?", (host,))

    def prune(self, days: int) -> None:
        cutoff = self.clock() - days * 86400
        self._execute(
            "DELETE FROM client_sessions WHERE end IS NOT NULL AND end < ?",
            (cutoff,),
        )
