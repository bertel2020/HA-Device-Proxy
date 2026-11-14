"""SQLite file for the event history and the configuration history.

Small and rarely written: events as they happen, counter snapshots every few minutes. A
damaged file is moved aside and a new one started; a file that cannot be used for another
reason (locked, a full or read-only disk) is left as it is and the history kept in memory
until the next start. ser2net keeps running either way.
"""

from __future__ import annotations

import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

PATH = Path("/data/history.db")
VERSION = 1  # PRAGMA user_version; lift older files in _open() when this grows
DAMAGED = re.compile(r"malformed|not a database|file is encrypted|database corrupt")
TABLES = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    ts REAL NOT NULL,
    level TEXT NOT NULL,
    connection TEXT,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    params TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    last_ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS events_ts ON events (ts);
CREATE INDEX IF NOT EXISTS events_connection ON events (connection, ts);
CREATE TABLE IF NOT EXISTS config_versions (
    id INTEGER PRIMARY KEY,
    ts REAL NOT NULL,
    source TEXT NOT NULL,
    summary TEXT NOT NULL,
    changes TEXT NOT NULL,
    config TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS client_sessions (
    id INTEGER PRIMARY KEY,
    host TEXT NOT NULL,
    connection TEXT NOT NULL,
    name TEXT NOT NULL,
    start REAL NOT NULL,
    end REAL,
    count INTEGER NOT NULL DEFAULT 1,
    to_client INTEGER NOT NULL DEFAULT 0,
    from_client INTEGER NOT NULL DEFAULT 0,
    refused TEXT,
    unknown INTEGER NOT NULL DEFAULT 0,
    updated REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS client_sessions_host ON client_sessions (host, start);
"""


class Database:
    def __init__(self, path: Path = PATH) -> None:
        self.path = path
        self.problems: list[tuple[str, dict[str, Any]]] = []  # for the events (they live here)
        self.generation = 0  # one up with each new file: row ids from before are gone
        self.conn = self._open()

    def _open(self) -> sqlite3.Connection:
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.executescript(TABLES)
            conn.execute(f"PRAGMA user_version = {VERSION}")
            conn.execute("PRAGMA quick_check").fetchone()
        except sqlite3.DatabaseError as err:
            if conn is not None:
                conn.close()
            if DAMAGED.search(str(err)):
                return self._recreate(err)
            return self._in_memory(err)  # locked, a full disk: the file itself is fine
        return conn

    def _recreate(self, err: Exception) -> sqlite3.Connection:
        self.generation += 1
        aside = self.path.with_name(f"{self.path.name}.damaged-{int(time.time())}")
        try:
            for suffix in ("", "-wal", "-shm"):
                source = Path(f"{self.path}{suffix}")
                if source.exists():
                    source.replace(Path(f"{aside}{suffix}"))
            conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(TABLES)
        except (OSError, sqlite3.Error) as new_err:  # e.g. a read-only disk
            return self._in_memory(new_err)
        _LOGGER.error("History database damaged (%s), moved to %s, starting a new one", err, aside)
        self.problems.append(("history_damaged", {"file": aside.name}))
        return conn

    def _in_memory(self, err: Exception) -> sqlite3.Connection:
        _LOGGER.error("History database not usable (%s), keeping the history in memory", err)
        self.problems.append(("history_unavailable", {"error": str(err)}))
        conn = sqlite3.connect(":memory:", isolation_level=None, check_same_thread=False)
        conn.executescript(TABLES)
        return conn

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> sqlite3.Cursor:
        try:
            return self.conn.execute(sql, params)
        except sqlite3.DatabaseError as err:
            if not DAMAGED.search(str(err)):  # e.g. a full disk: the history itself is fine
                raise
            self.conn.close()
            self.conn = self._recreate(err)
            return self.conn.execute(sql, params)

    def checkpoint(self) -> None:
        """Write the WAL into the main file, e.g. right before a backup."""
        self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def close(self) -> None:
        self.conn.close()
