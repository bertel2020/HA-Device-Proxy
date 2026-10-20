"""Runs the app's web interface on a desktop, without ser2net and Home Assistant.

    .venv/bin/python tools/dev_server.py [port]    then open http://127.0.0.1:8399/

Three example connections, a simulated smart meter in the trace (the first connection) and
some events. Nothing is shared on the network; ser2net shows as not running. Data lives in a
temporary folder that is removed at the end.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ser2net" / "app"))

from ser2net_app import controller as controller_module  # noqa: E402
from ser2net_app import process  # noqa: E402
from ser2net_app.controller import Controller  # noqa: E402
from ser2net_app.db import Database  # noqa: E402
from ser2net_app.events import EventLog  # noqa: E402
from ser2net_app.meter import crc_x25  # noqa: E402
from ser2net_app.model import AppConfig, Connection  # noqa: E402
from ser2net_app.store import Store  # noqa: E402
from ser2net_app.trace import TraceHub  # noqa: E402
from ser2net_app.web import WebServer  # noqa: E402


def _sml() -> bytes:
    """One SML telegram with a meter reading (1.8.0 = 18 450 282.7 Wh) and a right CRC."""
    body = bytes.fromhex("7707 0100010800ff 6500 1c0104 01 621e 52ff 69000000000aff4a2b 01")
    data = bytes.fromhex("1b1b1b1b01010101") + body + bytes.fromhex("1b1b1b1b1a00")
    crc = crc_x25(data)
    return data + bytes([crc & 0xFF, crc >> 8])


SML = _sml()


async def meter(trace: TraceHub, alias: str, stop: asyncio.Event) -> None:
    path = trace.shm_dir / f"{alias}.trace"
    while not stop.is_set():
        stamp = time.strftime("%Y/%m/%d %H:%M:%S").encode()
        lines = []
        for i in range(0, len(SML), 8):
            part = SML[i : i + 8]
            text = "".join(chr(b) if 32 <= b < 127 else "." for b in part)
            lines.append(stamp + b" term " + part.hex(" ").encode() + b" |" + text.encode() + b"|")
        with path.open("ab") as f:
            f.write(b"\n".join(lines) + b"\n")
        await asyncio.sleep(1)


async def main(port: int) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    process.RESTART_DELAYS = (3600,)  # no ser2net here: do not retry
    controller_module.STATUS_POLL = 3600
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        db = Database(data / "history.db")
        events = EventLog(db)
        store = Store(db, data / "config.json")
        config = AppConfig(
            connections=(
                Connection(
                    "eHZ Stromzähler",
                    "/dev/null",
                    3335,
                    template="ehz_sml",
                    max_clients=5,
                    trace="rx",
                ),
                Connection(
                    "Z-Wave-Gateway",
                    "/dev/zero",
                    3333,
                    baud=115200,
                    max_clients=2,
                    nodelay=True,
                    template="zwave",
                ),
                Connection("BWT AQA perla", "/dev/ttyMISSING0", 3334, baud=19200, max_clients=2),
            )
        )
        store.save(AppConfig(), config, "test")
        trace = TraceHub(record_dir=data / "trace", shm_dir=data / "shm")
        controller = Controller(
            store,
            events,
            data / "ser2net.yaml",
            custom_file=data / "own.yaml",
            import_dir=data / "import",
            trace=trace,
        )
        web = WebServer(controller, port=port, hosts=("127.0.0.1",), peers=None, version="dev")
        await web.start()
        stop = asyncio.Event()
        task = asyncio.create_task(controller.start(stop))
        await asyncio.sleep(0.5)
        alias = controller.config.connections[0].alias
        feeder = asyncio.create_task(meter(trace, alias, stop))
        print(f"Open http://127.0.0.1:{port}/  (Ctrl+C ends)")
        try:
            await asyncio.Event().wait()
        finally:
            stop.set()
            feeder.cancel()
            await task
            await web.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 8399))
    except KeyboardInterrupt:
        pass
