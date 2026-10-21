"""Docker HEALTHCHECK: ser2net answers on its admin socket, and every active EnOcean gateway
takes clients on its port (the EnOcean Eltako integration relies on them)."""

from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

from .model import ADMIN_SOCKET
from .store import PATH


def healthy(path: str = ADMIN_SOCKET, config: Path = PATH) -> bool:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            sock.connect(path)
    except OSError:
        return False
    return all(_listening(host, port) for host, port in enocean_ports(config))


def enocean_ports(config: Path = PATH) -> list[tuple[str, int]]:
    """(address, port) of the active EnOcean connections in the saved configuration."""
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []  # nothing saved yet
    ports = []
    for c in data.get("connections", []):
        if isinstance(c, dict) and c.get("kind") == "enocean" and c.get("enabled", True):
            bind = c.get("bind") or ""
            host = bind if bind and bind not in ("0.0.0.0", "::") else "127.0.0.1"
            ports.append((host, int(c.get("port", 0))))
    return ports


def _listening(host: str, port: int) -> bool:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.settimeout(3)
        return sock.connect_ex((host, port)) == 0


if __name__ == "__main__":
    sys.exit(0 if healthy() else 1)
