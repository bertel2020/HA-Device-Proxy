"""A ZIP for bug reports: versions, configuration, status, devices, recent events.

IP addresses are replaced (of clients and the host; only the default private ranges and
loopback stay), and clients are counted, not listed, so the file can be attached to an issue.
"""

from __future__ import annotations

import io
import ipaddress
import json
import os
import platform
import re
import shutil
import time
import zipfile
from typing import Any

IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6 = re.compile(r"[0-9A-Fa-f]*:[0-9A-Fa-f:]*:[0-9A-Fa-f]*")
KEEP = {"127.0.0.0", "127.0.0.1", "10.0.0.0", "172.16.0.0", "192.168.0.0", "0.0.0.0"}
KEEP6 = {"::1", "::", "fc00::", "fe80::"}


def _v6(match: re.Match[str]) -> str:
    text = match.group(0)
    try:
        ipaddress.IPv6Address(text)
    except ValueError:
        return text  # a time, a MAC or the like
    return text if text in KEEP6 else "x:x::x"


def redact(value: Any) -> Any:
    if isinstance(value, str):
        text = IPV4.sub(lambda m: m.group(0) if m.group(0) in KEEP else "x.x.x.x", value)
        return IPV6.sub(_v6, text)
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [redact(v) for v in value]
    return value


def build(
    *,
    version: str,
    ser2net_version: str,
    snapshot: dict[str, Any],
    config: dict[str, Any],
    runtime_yaml: str,
    events: list[dict[str, Any]],
) -> bytes:
    snapshot = dict(snapshot)
    for c in snapshot.get("connections", []):
        c["clients"] = len(c.get("clients", []))  # how many, not who
        c.pop("addresses", None)
    snapshot.pop("lan_ip", None)
    shm = shutil.disk_usage("/dev/shm") if os.path.isdir("/dev/shm") else None
    about = {
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "app": version,
        "ser2net": ser2net_version,
        "python": platform.python_version(),
        "system": platform.platform(),
        "dev_shm_free_mb": round(shm.free / 2**20, 1) if shm else None,
    }
    files = {
        "about.json": about,
        "status.json": snapshot,
        "config.json": config,
        "events.json": events,
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(
                name, json.dumps(redact(data), ensure_ascii=False, indent=1, default=str)
            )
        archive.writestr("ser2net.yaml", redact(runtime_yaml))
    return buffer.getvalue()
