"""Run by the Supervisor before a backup: writes the history's WAL into its main file."""

from __future__ import annotations

import sqlite3
import sys

from .db import PATH


def main() -> int:
    if not PATH.exists():
        return 0
    try:
        conn = sqlite3.connect(PATH, timeout=10)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
    except sqlite3.Error as err:
        print(f"History checkpoint before the backup failed: {err}", file=sys.stderr)
    return 0  # never block the backup


if __name__ == "__main__":
    sys.exit(main())
