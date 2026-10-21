"""Runs the app's web interface on a desktop, without ser2net and Home Assistant.

    .venv/bin/python tools/dev_server.py [port]    then open http://127.0.0.1:8399/

Three serial example connections, a simulated smart meter in the trace (the first one), a
Modbus TCP device simulated on 127.0.0.1 with a client polling it through the proxy, a
Modbus device that is not reachable, and some events. Nothing is shared on the network;
ser2net shows as not running. Data lives in a temporary folder that is removed at the end.
"""

from __future__ import annotations

import asyncio
import logging
import struct
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "device_proxy" / "app"))

from device_proxy import controller as controller_module  # noqa: E402
from device_proxy import process  # noqa: E402
from device_proxy.controller import Controller  # noqa: E402
from device_proxy.db import Database  # noqa: E402
from device_proxy.events import EventLog  # noqa: E402
from device_proxy.meter import crc_x25  # noqa: E402
from device_proxy.model import AppConfig, Connection  # noqa: E402
from device_proxy.store import Store  # noqa: E402
from device_proxy.trace import TraceHub  # noqa: E402
from device_proxy.web import WebServer  # noqa: E402


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


async def modbus_device(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Units 1 and 2; holding register n holds n * 10 (an inverter's power, say)."""
    try:
        while True:
            tid, _, length, unit = struct.unpack(">HHHB", await reader.readexactly(7))
            pdu = await reader.readexactly(length - 1)
            if unit not in (1, 2):
                continue  # nobody there
            address, count = struct.unpack(">HH", pdu[1:5])

            body = bytes([3, count * 2]) + b"".join(
                struct.pack(">H", (address + i) * 10 % 65536) for i in range(count)
            )
            await asyncio.sleep(0.015)
            writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
    except (asyncio.IncompleteReadError, ConnectionError):
        writer.close()


async def modbus_client(port: int, stop: asyncio.Event) -> None:
    await asyncio.sleep(1)
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    tid = 0
    while not stop.is_set():
        tid += 1
        writer.write(struct.pack(">HHHBBHH", tid, 0, 6, 1, 3, 40000 + tid % 50, 4))
        head = await reader.readexactly(7)
        await reader.readexactly(struct.unpack(">HHHB", head)[2] - 1)
        await asyncio.sleep(2)


async def main(port: int) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    process.RESTART_DELAYS = (3600,)  # no ser2net here: do not retry
    controller_module.STATUS_POLL = 3600
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        device = await asyncio.start_server(modbus_device, "127.0.0.1", 0)
        device_port = device.sockets[0].getsockname()[1]
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
                Connection(
                    "SolarEdge Wechselrichter",
                    "",
                    15020,
                    kind="modbus",
                    template="modbus",
                    host="127.0.0.1",
                    host_port=device_port,
                    max_clients=10,
                    bind="127.0.0.1",
                    trace="both",
                ),
                Connection(
                    "Wärmepumpe",
                    "",
                    15021,
                    kind="modbus",
                    template="modbus",
                    host="127.0.0.1",
                    host_port=1,
                    max_clients=10,
                    bind="127.0.0.1",
                ),
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
        poller = asyncio.create_task(modbus_client(15020, stop))
        print(f"Open http://127.0.0.1:{port}/  (Ctrl+C ends)")
        try:
            await asyncio.Event().wait()
        finally:
            stop.set()
            feeder.cancel()
            poller.cancel()
            device.close()
            await task
            await web.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 8399))
    except KeyboardInterrupt:
        pass
