"""Entry point of the app: loads the configuration and keeps ser2net running."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from .controller import Controller
from .db import Database
from .events import EventLog
from .store import Store
from .web import WebServer

CONFIG_FILE = Path("/data/ser2net.yaml")


async def main() -> int:
    # the log level is a setting of the app (web interface); applied once it is loaded
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    version = os.environ.get("APP_VERSION", "dev")
    logging.info("Device Proxy app %s", version)
    db = Database()
    store = Store(db)
    settings = store.load().settings
    events = EventLog(
        db, debounce_count=settings.debounce_count, debounce_minutes=settings.debounce_minutes
    )
    controller = Controller(store, events, CONFIG_FILE)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    web = WebServer(controller, version=version)
    await web.start()
    try:
        await controller.start(stop)
    finally:
        await web.stop()
        db.checkpoint()
        db.close()
    logging.info("Stopped")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
