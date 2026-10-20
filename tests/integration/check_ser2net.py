"""Checks the app against the real ser2net inside the built image (run by CI).

docker run --rm -v "$PWD/tests/integration:/test:ro" <image> \
    sh -c "apk add --no-cache socat && python3 /test/check_ser2net.py"

Two pseudo-terminal pairs stand in for serial devices: ser2net opens /dev/ttyV0 and
/dev/ttyV2, the test plays the device on /dev/ttyV1 and /dev/ttyV3. socat ends when the last
user of a pty side closes it, but ser2net closes the device when its last client leaves, so
the test keeps an idle handle on ser2net's side open (it never reads from it). Not a pytest
file: it needs ser2net, socat and root, which only the image has.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, "/app")

from ser2net_app.controller import Controller  # noqa: E402
from ser2net_app.db import Database  # noqa: E402
from ser2net_app.events import EventLog  # noqa: E402
from ser2net_app.model import AppConfig, Connection, Settings  # noqa: E402
from ser2net_app.store import Store  # noqa: E402
from ser2net_app.trace import TraceHub  # noqa: E402

PAIRS = (("/dev/ttyV0", "/dev/ttyV1"), ("/dev/ttyV2", "/dev/ttyV3"))
A_PORT, B_PORT = 4100, 4101


def pty_pairs() -> list[subprocess.Popen[bytes]]:
    procs = [
        subprocess.Popen(
            ["socat", f"pty,raw,echo=0,link={a}", f"pty,raw,echo=0,link={b}"],
            stderr=subprocess.DEVNULL,
        )
        for a, b in PAIRS
    ]
    deadline = time.time() + 10
    while not all(os.path.exists(p) for pair in PAIRS for p in pair):
        assert time.time() < deadline, "socat did not create the ptys"
        time.sleep(0.1)
    return procs


def open_ptys() -> dict[str, int]:
    return {p: os.open(p, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK) for pair in PAIRS for p in pair}


async def device_read(fd: int, size: int, timeout: float = 5) -> bytes:
    data = b""
    deadline = time.time() + timeout
    while len(data) < size and time.time() < deadline:
        try:
            data += os.read(fd, size - len(data))
        except BlockingIOError:
            await asyncio.sleep(0.05)
    return data


async def until(check: Callable[[], object], what: str, timeout: float = 10) -> None:
    deadline = time.time() + timeout
    while not check():
        assert time.time() < deadline, f"timed out waiting for: {what}"
        await asyncio.sleep(0.1)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    procs = pty_pairs()
    fds = open_ptys()
    dev_a, dev_b = fds[PAIRS[0][1]], fds[PAIRS[1][1]]
    data = Path(tempfile.mkdtemp())
    db = Database(data / "history.db")
    events = EventLog(db)
    controller = Controller(
        Store(db, data / "config.json"),
        events,
        data / "ser2net.yaml",
        custom_file=data / "own.yaml",
        import_dir=data / "import",
        trace=TraceHub(record_dir=data / "trace"),
    )
    stop = asyncio.Event()
    task = asyncio.create_task(controller.start(stop))
    try:
        await asyncio.wait_for(controller.admin.connected.wait(), 20)
        print("ok: ser2net runs, admin socket in YAML mode")

        a = Connection("A", PAIRS[0][0], A_PORT, max_clients=3, keep_open=True)
        b = Connection("B", PAIRS[1][0], B_PORT, max_clients=2)
        await controller.apply(AppConfig(Settings(listen="lan"), (a, b)), "test")

        await until(
            lambda: a.id in controller.activity and controller.activity[a.id].kept_open,
            "A kept open by the app",
        )
        reader_a, writer_a = await asyncio.open_connection("127.0.0.1", A_PORT)
        await until(
            lambda: any(e.kind == "client_connected" and e.connection == a.id for e in events.live),
            "client_connected event for A",
        )
        own = [e for e in events.live if e.kind == "client_connected" and e.connection == a.id]
        assert len(own) == 1, f"the app's own client was reported: {own}"
        print("ok: client events pushed by ser2net, own keep-open client left out")

        os.write(dev_a, b"hello")
        assert await asyncio.wait_for(reader_a.readexactly(5), 5) == b"hello"
        writer_a.write(b"ping")
        await writer_a.drain()
        assert await device_read(dev_a, 4) == b"ping"
        await until(lambda: controller.activity[a.id].bytes_kept >= 5, "keep-open client reads")
        print("ok: data both ways, keep-open client counts the device's data")

        def traced() -> set[tuple[str, bytes]]:
            return {(c.direction, c.data) for c in controller.live(a.id)}

        await until(lambda: {("rx", b"hello"), ("tx", b"ping")} <= traced(), "trace read along")
        result = await controller.apply(
            controller.config.with_connection(replace(a, trace="both")), "test"
        )
        assert result.disconnected == [] and result.rebuilt == [], result
        os.write(dev_a, b"rec")
        assert await asyncio.wait_for(reader_a.readexactly(3), 5) == b"rec"
        await until(
            lambda: (
                (data / "trace" / "a.log").exists()
                and " RX 72 65 63" in (data / "trace" / "a.log").read_text()
            ),
            "recording written",
        )
        snapshot = controller.snapshot()
        json.dumps(snapshot)
        print("ok: trace live and recorded; switching the recording disconnected nobody")

        await controller.read_status()
        port_a = controller.status[a.alias]
        assert len(port_a.clients) == 2, port_a
        assert port_a.bytes_from_device >= 5, port_a
        print("ok: showport parsed:", [c.address for c in port_a.clients])

        reader_b, writer_b = await asyncio.open_connection("127.0.0.1", B_PORT)
        await asyncio.sleep(0.5)
        result = await controller.apply(
            controller.config.with_connection(replace(b, baud=19200)), "test"
        )
        assert result.disconnected == ["B"], result
        assert await asyncio.wait_for(reader_b.read(), 5) == b"", "B's client stays connected"
        os.write(dev_a, b"still")
        assert await asyncio.wait_for(reader_a.readexactly(5), 5) == b"still"
        print("ok: a change to B disconnects only B's clients, A keeps its client")

        await controller.apply(
            controller.config.with_connection(replace(b, baud=19200, remaddr="10.0.0.0/8")),
            "test",
        )
        reader_c, _ = await asyncio.open_connection("127.0.0.1", B_PORT)
        os.write(dev_b, b"secret")
        assert b"secret" not in await asyncio.wait_for(reader_c.read(), 5)
        assert not (await controller.admin.showport(b.alias))[0].clients
        print("ok: remaddr with a network refuses a client outside it")

        current_b = controller.config.connection(b.id)
        assert current_b is not None
        await controller.apply(
            controller.config.with_connection(replace(current_b, enabled=False)), "test"
        )
        ports = {p.alias: p for p in await controller.admin.showport()}
        assert not ports[b.alias].enabled, ports[b.alias]
        print("ok: disabling a connection")
        writer_a.close()

        own_file = f"""%YAML 1.1
---
connections:
  mine:
    accepter: tcp,{B_PORT + 1}
    connector: serialdev,{PAIRS[1][0]},9600n81,local
"""
        await controller.save_custom(own_file, use=True)
        reader_d, writer_d = await asyncio.open_connection("127.0.0.1", B_PORT + 1)
        await until(
            lambda: any(e.kind == "client_connected" and e.name == "mine" for e in events.live),
            "client event with the own file's connection name",
        )
        os.write(dev_b, b"own")
        assert await asyncio.wait_for(reader_d.readexactly(3), 5) == b"own"
        assert {p.alias for p in await controller.admin.showport()} == {"mine"}
        writer_d.close()
        print("ok: own ser2net.yaml (version 2) with the app's admin socket added")
    finally:
        stop.set()
        await task
        for fd in fds.values():
            os.close(fd)
        for proc in procs:
            proc.terminate()
    print("all checks passed")


if __name__ == "__main__":
    asyncio.run(main())
