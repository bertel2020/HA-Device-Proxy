"""Checks the parts that behave differently on Linux, in a container like the app's:

    docker run --rm -v "$PWD":/src -w /src python:3.14-alpine sh -c \
        "pip install -q PyYAML pytest pytest-asyncio pytest-timeout && python tools/linux_check.py"

The serial device is a pseudo terminal: TIOCEXCL keeps a second program out, speed and
stop bits arrive (a pseudo terminal keeps no parity), a Modbus RTU request goes through
SerialLink. The port check of the form
sees free ports, ports taken on every address and ports taken on one address only. Exit
code 1 when one of them fails.
"""

from __future__ import annotations

import asyncio
import errno
import os
import socket
import sys
import tempfile
import termios
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "device_proxy" / "app"))

from device_proxy.controller import Controller  # noqa: E402
from device_proxy.db import Database  # noqa: E402
from device_proxy.events import EventLog  # noqa: E402
from device_proxy.modbus import RtuFramer, SerialLink, rtu_frame  # noqa: E402
from device_proxy.model import Connection  # noqa: E402
from device_proxy.store import Store  # noqa: E402
from device_proxy.trace import TraceHub  # noqa: E402

failed: list[str] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    print(f"{'ok  ' if ok else 'FAIL'} {name}{f': {detail}' if detail else ''}")
    if not ok:
        failed.append(name)


async def serial() -> None:
    master, slave = os.openpty()
    path = os.ttyname(slave)
    link = SerialLink(path, 19200, 8, "n", 2)
    await link.open(1)
    try:
        os.close(os.open(path, os.O_RDWR | os.O_NOCTTY))
        check("TIOCEXCL keeps a second program out", False, "second open worked")
    except OSError as err:
        check("TIOCEXCL keeps a second program out", err.errno == errno.EBUSY, err)
    assert link.fd is not None
    attrs = termios.tcgetattr(link.fd)
    cflag = attrs[2]
    check(
        "line settings 19200 8N2 arrive",  # a pseudo terminal always keeps 8N: no parity
        attrs[4] == attrs[5] == termios.B19200
        and cflag & termios.CSIZE == termios.CS8
        and bool(cflag & termios.CSTOPB),
        f"speed {attrs[4]}, cflag {cflag:o}",
    )
    framer = RtuFramer(link, link.frame_gap)
    answer_body = bytes([3, 2, 0x12, 0x34])

    def device() -> None:  # answers once the request is complete
        data = os.read(master, 64)
        if len(data) >= 8:
            asyncio.get_running_loop().remove_reader(master)
            os.write(master, rtu_frame(1, answer_body))

    asyncio.get_running_loop().add_reader(master, device)
    try:
        pdu = await asyncio.wait_for(
            framer.exchange(1, bytes([3, 0, 0, 0, 1]), 1.0, lambda *a: None), 3
        )
        check("Modbus RTU request over the serial device", pdu == answer_body, (pdu or b"").hex())
    except Exception as err:  # noqa: BLE001
        check("Modbus RTU request over the serial device", False, repr(err))
    await link.close()
    os.close(master)
    os.close(slave)


async def ports() -> None:
    folder = Path(tempfile.mkdtemp())
    db = Database(folder / "history.db")
    controller = Controller(
        Store(db, folder / "config.json"),
        EventLog(db),
        folder / "ser2net.yaml",
        custom_file=folder / "own.yaml",
        trace=TraceHub(folder / "trace", folder / "shm"),
    )

    def problem(port: int, bind: str = "") -> str | None:
        c = Connection("x", "", port, kind="modbus", host="1.2.3.4", bind=bind)
        return controller.port_problem(c)

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free = probe.getsockname()[1]
    check("free port", problem(free) is None, problem(free))
    for address, label in (("0.0.0.0", "every address"), ("127.0.0.1", "loopback only")):
        other = await asyncio.start_server(lambda r, w: None, address, 0)
        taken = other.sockets[0].getsockname()[1]
        result = problem(taken)
        check(f"port taken on {label}", result == "in use by another program", result)
        other.close()
        await other.wait_closed()
    result = problem(free, "192.0.2.1")
    check("bind address not on this host", result == "the bind address is not on this host", result)


async def main() -> int:
    print(f"{os.uname().sysname} {os.uname().release}, Python {sys.version.split()[0]}")
    await serial()
    await ports()
    print("OK" if not failed else f"FAILED: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
