"""Docker HEALTHCHECK: ser2net answers on its admin socket."""

from __future__ import annotations

import socket
import sys

from .model import ADMIN_SOCKET


def healthy(path: str = ADMIN_SOCKET) -> bool:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            sock.connect(path)
    except OSError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(0 if healthy() else 1)
