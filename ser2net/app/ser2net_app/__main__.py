"""Entry point of the app: writes the ser2net configuration and keeps ser2net running."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path

from .config import Connection, render
from .process import Ser2Net

OPTIONS = Path("/data/options.json")
CONFIG = Path("/data/ser2net.yaml")


def connections() -> list[Connection]:
    # Step 1 of the plan: no connections yet, ser2net runs with its admin port only.
    # The connections and the web interface follow in the next steps.
    return []


async def main(options_path: Path = OPTIONS, config_path: Path = CONFIG) -> int:
    try:
        options = json.loads(options_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        options = {}
    logging.basicConfig(
        level=getattr(logging, str(options.get("log_level", "info")).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.info("Ser2Net app %s", os.environ.get("APP_VERSION", "dev"))
    try:
        text = render(connections())
        config_path.write_text(text, encoding="utf-8")
    except (OSError, ValueError) as err:
        logging.error("Configuration: %s", err)
        return 1
    logging.debug("Configuration for ser2net:\n%s", text)
    ser2net = Ser2Net(config_path)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    await ser2net.run(stop)
    logging.info("Stopped")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
