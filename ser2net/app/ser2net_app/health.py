"""Docker HEALTHCHECK: ser2net answers on its admin port."""

from __future__ import annotations

import socket
import sys

from .config import ADMIN_PORT


def healthy(port: int = ADMIN_PORT) -> bool:
    try:
        socket.create_connection(("127.0.0.1", port), timeout=3).close()
    except OSError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(0 if healthy() else 1)
