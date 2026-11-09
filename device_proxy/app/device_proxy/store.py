"""The app configuration on disk (/data/config.json) and its last versions for undo."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

from .db import Database
from .model import AppConfig, ValidationError

_LOGGER = logging.getLogger(__name__)

PATH = Path("/data/config.json")
KEEP_VERSIONS = 25
SECRET_SETTINGS = {"mqtt_user", "mqtt_password"}  # the history names them, never the value
# changes that touch no connection: no version in the history, no "last change" to go back from
QUIET_SETTINGS = frozenset({"client_names", "notify_new_clients"})
PASSWORD_KEPT = "••••••••"  # the browser gets this for a set password; sent back: unchanged


def hidden(settings: dict[str, Any], keys: set[str] | frozenset[str], mask: str) -> dict[str, Any]:
    """The settings with the set values of these keys replaced by the mask."""
    return {k: (mask if k in keys and v else v) for k, v in settings.items()}


Change = dict[str, Any]  # {"connection": name | None, "change": ..., "fields": [...]}


def changes(old: AppConfig, new: AppConfig) -> list[Change]:
    """What changed between two configurations, for the history (the UI words it)."""
    before = {c.id: c for c in old.connections}
    after = {c.id: c for c in new.connections}
    items: list[Change] = []
    items += [
        {"connection": after[i].name, "change": "added"} for i in after.keys() - before.keys()
    ]
    items += [
        {"connection": before[i].name, "change": "removed"} for i in before.keys() - after.keys()
    ]
    for i in before.keys() & after.keys():
        if before[i] == after[i]:
            continue
        old_d, new_d = before[i].to_dict(), after[i].to_dict()
        keys = [k for k in new_d if old_d.get(k) != new_d[k]]
        if keys == ["enabled"]:
            change = "enabled" if after[i].enabled else "disabled"
            items.append({"connection": after[i].name, "change": change})
        else:
            items.append({"connection": after[i].name, "change": "changed", "fields": keys})
    if old.settings != new.settings:
        old_s, new_s = old.settings.to_dict(), new.settings.to_dict()
        keys = [k for k in new_s if old_s[k] != new_s[k]]
        values = {k: new_s[k] for k in keys if k not in SECRET_SETTINGS}
        items.append({"connection": None, "change": "settings", "fields": keys, "values": values})
    return sorted(items, key=lambda item: (item["connection"] or "", item["change"]))


def quiet(items: list[Change]) -> bool:
    """Only settings that are not worth a version changed."""
    return bool(items) and all(
        item["connection"] is None and QUIET_SETTINGS.issuperset(item.get("fields", []))
        for item in items
    )


def summary(items: list[Change]) -> str:
    """The English line for the app log."""
    parts = []
    for item in items:
        who = item["connection"] or "settings"
        if item.get("fields"):
            parts.append(f"{who}: {', '.join(item['fields'])}")
        else:
            parts.append(f"{who} {item['change']}")
    return "; ".join(parts) or "no change"


class SaveError(OSError):
    """The configuration could not be written (a full disk, for one): nothing changed."""


class Store:
    def __init__(self, db: Database | None, path: Path = PATH) -> None:
        self.db = db
        self.path = path
        self.problems: list[tuple[str, dict[str, Any]]] = []  # for the events, after the start

    def _problem(self, kind: str, **params: Any) -> None:
        if (kind, params) not in self.problems:  # the configuration is loaded more than once
            self.problems.append((kind, params))

    def load(self) -> AppConfig:
        """The saved configuration; when the file is missing, unreadable or invalid, the
        latest saved version, and an empty one when there is none."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return self._latest_version() or AppConfig()
        except (OSError, ValueError) as err:
            _LOGGER.error("Configuration %s unreadable (%s)", self.path, err)
            latest = self._latest_version()
            if latest is None:
                self._problem("config_lost")
            return latest or AppConfig()
        try:
            return AppConfig.from_dict(data)
        except ValidationError as err:
            _LOGGER.error("Configuration %s invalid (%s)", self.path, err)
            self.path.replace(self.path.with_suffix(f".invalid-{int(time.time())}"))
        latest = self._latest_version()
        if latest is not None:
            return latest
        # the saved versions are invalid as well (checks became stricter): keep what is valid
        config, dropped = AppConfig.salvage(data)
        for item in dropped:
            _LOGGER.error("Configuration: left out %s", item)
        self._problem("config_salvaged", dropped=len(dropped))
        try:
            self._write(config)  # the next start finds it (the invalid file is set aside)
        except SaveError as err:
            _LOGGER.error("%s", err)
        return config

    def latest_id(self) -> int | None:
        """The id of the last saved version: the configuration as it is now."""
        if self.db is None:
            return None
        try:
            row = self.db.execute(
                "SELECT id FROM config_versions ORDER BY id DESC LIMIT 1"
            ).fetchone()
        except sqlite3.Error:  # no way back offered, saving goes on
            return None
        return int(row[0]) if row else None

    def _latest_version(self) -> AppConfig | None:
        if self.db is None:
            return None
        try:
            row = self.db.execute(
                "SELECT id FROM config_versions ORDER BY id DESC LIMIT 1"
            ).fetchone()
            config = self.version(row[0]) if row else None
        except Exception as err:  # a damaged database must not keep the app from starting
            _LOGGER.error("Latest saved version not readable (%s)", err)
            return None
        if config is not None:
            _LOGGER.warning("Using the latest saved version of the configuration")
            self._problem("config_restored")
        return config

    def save(self, old: AppConfig, new: AppConfig, source: str) -> list[Change]:
        """Write the configuration and keep it as a version; returns what changed."""
        text = self._write(new)
        items = changes(old, new)
        if self.db is not None and items and not quiet(items):  # no change: no new version
            try:
                self.db.execute(
                    "INSERT INTO config_versions (ts, source, summary, changes, config)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (
                        time.time(),
                        source,
                        summary(items),
                        json.dumps(items, ensure_ascii=False),
                        text,
                    ),
                )
                self.db.execute(
                    "DELETE FROM config_versions WHERE id NOT IN"
                    " (SELECT id FROM config_versions ORDER BY id DESC LIMIT ?)",
                    (KEEP_VERSIONS,),
                )
            except sqlite3.Error as err:  # the file is saved: the change counts, without history
                _LOGGER.warning("Configuration saved, but not kept in the history: %s", err)
        return items

    def _write(self, config: AppConfig) -> str:
        text = json.dumps(config.to_dict(), ensure_ascii=False, indent=1)
        tmp = self.path.with_suffix(".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())  # a power cut right after saving must not leave half a file
            os.replace(tmp, self.path)
        except OSError as err:
            tmp.unlink(missing_ok=True)
            raise SaveError(err.errno, f"configuration not saved: {err.strerror or err}") from err
        return text

    def versions(self) -> list[dict[str, Any]]:
        if self.db is None:
            return []
        rows = self.db.execute(
            "SELECT id, ts, source, summary, changes FROM config_versions ORDER BY id DESC"
        ).fetchall()
        return [
            {"id": r[0], "ts": r[1], "source": r[2], "summary": r[3], "changes": json.loads(r[4])}
            for r in rows
        ]

    def version(self, version_id: int) -> AppConfig | None:
        if self.db is None:
            return None
        row = self.db.execute(
            "SELECT config FROM config_versions WHERE id = ?", (version_id,)
        ).fetchone()
        return AppConfig.from_dict(json.loads(row[0])) if row else None
