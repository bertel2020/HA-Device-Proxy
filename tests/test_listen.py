import asyncio
import struct
import time
from dataclasses import replace

import pytest

from device_proxy.listen import BusSniffer, ListenProxy
from device_proxy.modbus import ClientInfo, rtu_frame
from device_proxy.model import Connection


def _read(unit: int, function: int, address: int, count: int) -> bytes:
    return rtu_frame(unit, struct.pack(">BHH", function, address, count))


def _answer(unit: int, function: int, values: list[int]) -> bytes:
    data = b"".join(struct.pack(">H", v) for v in values)
    return rtu_frame(unit, bytes([function, len(data)]) + data)


def test_the_sniffer_pairs_reads_and_answers_across_merged_and_split_chunks() -> None:
    sniffer = BusSniffer()
    bus = (
        b"\x00\x13"  # the tail of a frame heard in part
        + _read(1, 4, 30000, 3)
        + _answer(1, 4, [230, 231, 232])
        + _read(2, 3, 100, 2)
        + _answer(2, 3, [7, 8])
        + rtu_frame(2, struct.pack(">BHH", 6, 101, 9))  # the master writes ...
        + rtu_frame(2, struct.pack(">BHH", 6, 101, 9))  # ... and the device echoes
    )
    frames = []
    for i in range(0, len(bus), 5):  # as a USB adapter delivers them: in pieces
        frames += sniffer.feed(bus[i : i + 5], now=100.0)
    assert len(frames) == 6 and sniffer.dropped == 2
    assert sniffer.read(1, 4, 30000, 3, 60, 120.0) == [230, 231, 232]
    assert sniffer.read(2, 3, 100, 2, 60, 120.0) == [7, 9]  # 101 written since
    assert sniffer.read(1, 4, 30000, 4, 60, 120.0) is None  # 30003 never heard
    assert sniffer.read(1, 4, 30000, 3, 10, 120.0) is None  # too old
    assert [(r["unit"], r["first"], r["last"]) for r in sniffer.ranges()] == [
        (1, 30000, 30002),
        (2, 100, 101),
    ]


async def test_clients_read_what_was_heard_and_cannot_write() -> None:
    c = Connection(
        "Meter on the inverter's bus", "/dev/null", 1502, kind="modbus", link="rtu_listen"
    )
    c.validate()
    proxy = ListenProxy(c, "lan", lambda *a, **k: None, lambda ch: None)
    proxy.sniffer.feed(_read(1, 3, 0, 2) + _answer(1, 3, [5, 6]))
    client = ClientInfo("127.0.0.1:1", 0)
    assert await proxy.request(1, struct.pack(">BHH", 3, 0, 2), client) == bytes([3, 4, 0, 5, 0, 6])
    assert await proxy.request(1, struct.pack(">BHH", 3, 0, 3), client) == bytes([0x83, 0x0B])
    assert await proxy.request(1, struct.pack(">BHH", 6, 0, 1), client) == bytes([0x86, 0x01])
    assert proxy.state()["listen"]["registers"] == 2
    proxy.sniffer.registers.update({(1, 3, a): (0, time.time()) for a in range(100, 230)})
    for count in (0, 126, 130):  # more than one answer carries: refused, not a crash
        assert await proxy.request(1, struct.pack(">BHH", 3, 100, count), client) == bytes(
            [0x83, 0x03]
        )
    await asyncio.sleep(0)


async def test_listening_on_a_serial_line_end_to_end() -> None:
    import os
    import pty

    master, slave = pty.openpty()
    c = Connection(
        "Bus", os.ttyname(slave), 1502, kind="modbus", link="rtu_listen", bind="127.0.0.1"
    )
    c = replace(c, port=0)  # any free port (port 0 passes no validation, so after it)
    proxy = ListenProxy(c, "lan", lambda *a, **k: None, lambda ch: None)
    task = asyncio.create_task(proxy.run())
    try:
        for _ in range(100):
            if proxy._server is not None and proxy.paths[0].link.is_open:
                break
            await asyncio.sleep(0.02)
        os.write(master, _read(3, 4, 10, 1) + _answer(3, 4, [4242]))
        for _ in range(100):
            if proxy.sniffer.registers:
                break
            await asyncio.sleep(0.02)
        assert proxy._server is not None
        port = proxy._server.sockets[0].getsockname()[1]
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(struct.pack(">HHHBBHH", 9, 0, 6, 3, 4, 10, 1))
        assert await reader.readexactly(11) == struct.pack(">HHHBBBH", 9, 0, 5, 3, 4, 2, 4242)
        writer.close()
        os.set_blocking(master, False)
        with pytest.raises(BlockingIOError):
            os.read(master, 100)  # the proxy never wrote to the bus
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        os.close(master)
        os.close(slave)
