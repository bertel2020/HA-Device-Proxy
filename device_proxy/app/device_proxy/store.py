"""The app configuration on disk (/data/config.json) and its last versions for undo."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from .db import Database
from .model import AppConfig, ValidationError

_LOGGER = logging.getLogger(__name__)

PATH = Path("/data/config.json")
KEEP_VERSIONS = 25
SECRET_SETTINGS = {"mqtt_user", "mqtt_password"}  # the history names them, never the value
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


class Store:
    def __init__(self, db: Database | None, path: Path = PATH) -> None:
        self.db = db
        self.path = path

    def load(self) -> AppConfig:
        """The saved configuration; when the file is missing, unreadable or invalid, the
        latest saved version, and an empty one when there is none."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return self._latest_version() or AppConfig()
        except (OSError, ValueError) as err:
            _LOGGER.error("Configuration %s unreadable (%s)", self.path, err)
            return self._latest_version() or AppConfig()
        try:
            return AppConfig.from_dict(data)
        except ValidationError as err:
            _LOGGER.error("Configuration %s invalid (%s)", self.path, err)
            self.path.replace(self.path.with_suffix(f".invalid-{int(time.time())}"))
            return self._latest_version() or AppConfig()

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
        return config

    def save(self, old: AppConfig, new: AppConfig, source: str) -> list[Change]:
        """Write the configuration and keep it as a version; returns what changed."""
        text = json.dumps(new.to_dict(), ensure_ascii=False, indent=1)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())  # a power cut right after saving must not leave half a file
        os.replace(tmp, self.path)
        items = changes(old, new)
        if self.db is not None and items:  # saving without a change is no new version
            self.db.execute(
                "INSERT INTO config_versions (ts, source, summary, changes, config)"
                " VALUES (?, ?, ?, ?, ?)",
                (time.time(), source, summary(items), json.dumps(items, ensure_ascii=False), text),
            )
            self.db.execute(
                "DELETE FROM config_versions WHERE id NOT IN"
                " (SELECT id FROM config_versions ORDER BY id DESC LIMIT ?)",
                (KEEP_VERSIONS,),
            )
        return items

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
