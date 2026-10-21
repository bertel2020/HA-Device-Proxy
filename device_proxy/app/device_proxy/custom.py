"""The user's own ser2net.yaml, used as it is instead of the forms.

It lives in the app's config folder (/config/ser2net.yaml, in Home Assistant under
/addon_configs/<slug>/), so it can be edited there too. The app adds its admin socket when it
hands the file to ser2net; the file itself must not have an admin section. Status, events,
the history and MQTT keep working, with ser2net's connection names as names.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .importer import ReadError, parse, split_top
from .legacy import looks_legacy
from .model import ADMIN_SOCKET, RESERVED_PORTS

PATH = Path("/config/ser2net.yaml")

Note = dict[str, Any]


@dataclass
class CustomCheck:
    version: int = 1
    errors: list[Note] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    connections: list[dict[str, Any]] = field(default_factory=list)  # alias, port, enabled

    @property
    def ok(self) -> bool:
        return not self.errors


def _port(accepter: str) -> int | None:
    numbers = [t for t in split_top(accepter) if t.isdigit()]
    return int(numbers[-1]) if numbers else None


def check(text: str) -> CustomCheck:
    result = CustomCheck()
    if looks_legacy(text):
        result.errors.append({"code": "legacy_format"})  # ser2net 4 reads YAML only
        return result
    try:
        result.version, raw, notes = parse(text)
    except ReadError as err:
        result.errors.append(err.note)
        return result
    for note in notes:
        if note["code"] == "admin_ignored":
            result.errors.append({"code": "admin_present"})
        else:
            result.notes.append(note)
    seen: dict[int, str] = {}
    for alias, definition in raw:
        port = _port(definition.get("accepter", ""))
        if port is not None and port in seen:
            result.errors.append({"code": "port_twice", "port": port, "names": [seen[port], alias]})
        if port is not None and port in RESERVED_PORTS:
            result.errors.append({"code": "port_reserved", "port": port, "name": alias})
        if port is not None:
            seen.setdefault(port, alias)
        enabled = definition.get("enable", "on").lower() not in ("off", "false", "0")
        result.connections.append({"alias": alias, "port": port, "enabled": enabled})
    if not raw:
        result.errors.append({"code": "no_connections"})
    return result


def runtime(text: str, version: int, admin_socket: str = ADMIN_SOCKET) -> str:
    """The user's file plus the app's admin socket, in the file's own version."""
    lines = text.rstrip().splitlines()
    while lines and lines[-1].strip() == "...":
        lines.pop()
    body = "\n".join(lines)
    accepter = f"unix(delsock,umode=6,gmode=0,omode=0),{admin_socket}"
    if version == 2:
        return f"{body}\n---\nadmins:\n  device_proxy:\n    accepter: {accepter}\n"
    return f"{body}\n\nadmin:\n  accepter: {accepter}\n"


def blocks(text: str) -> dict[str, str]:
    """Connection name → its definition, to tell which connections a change touches."""
    try:
        _, raw, _ = parse(text)
    except ReadError:
        return {}
    return {alias: json.dumps(d, sort_keys=True) for alias, d in raw}
