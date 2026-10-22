"""SQLite file for the event history and the configuration history.

Small and rarely written: events as they happen, counter snapshots every few minutes. A
damaged file is moved aside and a new one started; ser2net keeps running either way.
"""

from __future__ import annotations

import logging
import re
import sqlite3
import time
from pathlib import Path

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
"""


class Database:
    def __init__(self, path: Path = PATH) -> None:
        self.path = path
        self.conn = self._open()

    def _open(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.executescript(TABLES)
            conn.execute(f"PRAGMA user_version = {VERSION}")
            conn.execute("PRAGMA quick_check").fetchone()
        except sqlite3.DatabaseError as err:
            return self._recreate(err)
        return conn

    def _recreate(self, err: Exception) -> sqlite3.Connection:
        aside = self.path.with_name(f"{self.path.name}.damaged-{int(time.time())}")
        _LOGGER.error("History database damaged (%s), moved to %s, starting a new one", err, aside)
        for suffix in ("", "-wal", "-shm"):
            source = Path(f"{self.path}{suffix}")
            if source.exists():
                source.replace(Path(f"{aside}{suffix}"))
        conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
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
