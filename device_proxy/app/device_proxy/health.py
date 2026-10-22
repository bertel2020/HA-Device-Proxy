"""Docker HEALTHCHECK: ser2net answers on its admin socket, and every active EnOcean gateway
takes clients on its port (the EnOcean Eltako integration relies on them).

The gateways are not asked over their ports: a connection there is a client like any other
(it takes a place, may push out the integration with kickolduser and lands in the history).
The app writes their state to HEALTH_FILE instead; a file that is not renewed means the app
hangs."""

from __future__ import annotations

import json
import socket
import sys
import time
from pathlib import Path

from .model import ADMIN_SOCKET

HEALTH_FILE = Path("/dev/shm/device_proxy_health.json")
STALE = 120  # seconds without a renewed HEALTH_FILE


def healthy(path: str = ADMIN_SOCKET, state: Path = HEALTH_FILE) -> bool:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            sock.connect(path)
    except OSError:
        return False
    return proxies_ok(state)


def proxies_ok(state: Path = HEALTH_FILE) -> bool:
    """The app's last word on its EnOcean gateways; fine while it has not written one yet."""
    try:
        data = json.loads(state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True  # just started
    if not isinstance(data, dict) or time.time() - float(data.get("time", 0)) > STALE:
        return False
    return not data.get("not_listening")


def write(names: list[str], state: Path = HEALTH_FILE) -> None:
    """Called by the app every few seconds: the EnOcean gateways that do not listen."""
    tmp = state.with_suffix(".tmp")
    tmp.write_text(json.dumps({"time": time.time(), "not_listening": names}), encoding="utf-8")
    tmp.replace(state)


if __name__ == "__main__":
    sys.exit(0 if healthy() else 1)
