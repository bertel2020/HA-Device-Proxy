import asyncio
import struct

from device_proxy.modbus import ClientInfo, ModbusProxy, Scheduler, _Job, crc16, rtu_frame
from device_proxy.model import Connection, parse_unit_map


async def _device(rtu: bool, ignore: set[int]):
    """A Modbus device on a TCP port that takes one connection and answers slowly; holding
    register n holds n * 10. Requests for units in ignore get no answer."""
    busy = asyncio.Lock()

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        if busy.locked():
            writer.close()
            return
        async with busy:
            while True:
                try:
                    if rtu:
                        frame = await reader.readexactly(8)
                        unit, pdu = frame[0], frame[1:6]
                    else:
                        head = await reader.readexactly(7)
                        tid, _, length, unit = struct.unpack(">HHHB", head)
                        pdu = await reader.readexactly(length - 1)
                except asyncio.IncompleteReadError:
                    return
                if unit in ignore:
                    continue
                await asyncio.sleep(0.02)
                address, count = struct.unpack(">HH", pdu[1:5])
                body = bytes([3, count * 2]) + b"".join(
                    struct.pack(">H", (address + i) * 10) for i in range(count)
                )
                if rtu:
                    writer.write(rtu_frame(unit, body))
                else:
                    writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
                await writer.drain()

    return await asyncio.start_server(handle, "127.0.0.1", 0)


async def _read(port: int, tid: int, unit: int, address: int) -> bytes:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(struct.pack(">HHHBBHH", tid, 0, 6, unit, 3, address, 2))
    head = await reader.readexactly(7)
    got_tid, _, length, _ = struct.unpack(">HHHB", head)
    body = await reader.readexactly(length - 1)
    writer.close()
    assert got_tid == tid
    return body


def test_crc_of_a_known_frame() -> None:
    assert crc16(bytes.fromhex("010300000001")).to_bytes(2, "little") == bytes.fromhex("840a")


async def _run(link: str) -> None:
    device = await _device(link == "rtu_tcp", ignore={9})
    device_port = device.sockets[0].getsockname()[1]
    c = Connection(
        "Inverter",
        "",
        0,
        kind="modbus",
        link=link,
        host="127.0.0.1",
        host_port=device_port,
        max_clients=10,
        bind="127.0.0.1",
        request_timeout_ms=300,
        retries=0,
        unit_map="2=1",  # clients asking unit 2 reach unit 1
    )
    events: list[str] = []
    proxy = ModbusProxy(c, "lan", lambda level, kind, **p: events.append(kind), lambda ch: None)
    task = asyncio.create_task(proxy.run())
    for _ in range(50):
        if proxy._server is not None:
            break
        await asyncio.sleep(0.02)
    assert proxy._server is not None
    port = proxy._server.sockets[0].getsockname()[1]

    # several clients at once over the device's single connection, each gets its own answer
    answers = await asyncio.gather(*(_read(port, 100 + n, 1 + n % 2, n) for n in range(6)))
    for n, body in enumerate(answers):
        assert body == bytes([3, 4]) + struct.pack(">HH", n * 10, (n + 1) * 10)
    # no answer from the device: a gateway exception, and the next request works again
    assert await _read(port, 7, 9, 0) == bytes([0x83, 0x0B])
    assert (await _read(port, 8, 1, 5))[2:4] == struct.pack(">H", 50)
    assert proxy.stats.answered == 7 and proxy.stats.timeouts == 1
    assert (proxy.units[1].answered, proxy.units[9].failed) == (7, 1)
    assert events.count("client_connected") == 8
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    device.close()


async def test_modbus_tcp_device_for_several_clients() -> None:
    await _run("tcp")


async def test_modbus_rtu_over_tcp() -> None:
    await _run("rtu_tcp")


async def test_writes_are_refused_without_write_access() -> None:
    c = Connection(
        "Inverter",
        "",
        0,
        kind="modbus",
        host="127.0.0.1",
        host_port=1,
        bind="127.0.0.1",
        write_access="listed",
        write_clients="192.168.1.5",
    )
    proxy = ModbusProxy(c, "lan", lambda level, kind, **p: None, lambda ch: None)
    task = asyncio.create_task(proxy.run())
    while proxy._server is None:
        await asyncio.sleep(0.01)
    port = proxy._server.sockets[0].getsockname()[1]
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(struct.pack(">HHHBBHH", 1, 0, 6, 1, 6, 100, 7))  # write register 100 = 7
    assert await reader.readexactly(9) == struct.pack(">HHHB", 1, 0, 3, 1) + bytes([0x86, 1])
    writer.close()
    assert proxy.stats.blocked == 1 and proxy.stats.requests == 0
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def test_cache_answers_the_same_read_once() -> None:
    device = await _device(False, ignore=set())
    c = Connection(
        "Inverter",
        "",
        0,
        kind="modbus",
        host="127.0.0.1",
        bind="127.0.0.1",
        max_clients=10,
        host_port=device.sockets[0].getsockname()[1],
        cache_ms=1000,
    )
    proxy = ModbusProxy(c, "lan", lambda level, kind, **p: None, lambda ch: None)
    task = asyncio.create_task(proxy.run())
    while proxy._server is None:
        await asyncio.sleep(0.01)
    port = proxy._server.sockets[0].getsockname()[1]
    answers = await asyncio.gather(*(_read(port, n, 1, 4) for n in range(5)))  # at once
    answers.append(await _read(port, 9, 1, 4))  # a moment later
    assert len(set(answers)) == 1
    assert proxy.stats.requests == 1 and proxy.stats.cached == 5
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    device.close()


async def test_clients_take_turns() -> None:
    scheduler = Scheduler()
    loop = asyncio.get_running_loop()
    for key, n in [("busy", 1), ("busy", 2), ("busy", 3), ("other", 1)]:
        scheduler.put(key, _Job(n, b"", ClientInfo(key, 0), loop.create_future()))
    order = [(job.client.address, job.unit) for job in [await scheduler.get() for _ in range(4)]]
    assert order == [("busy", 1), ("other", 1), ("busy", 2), ("busy", 3)]


async def test_probe_finds_a_device_that_stops_answering() -> None:
    device = await _device(False, ignore={1})  # takes the connection, never answers unit 1
    c = Connection(
        "Inverter",
        "",
        0,
        kind="modbus",
        host="127.0.0.1",
        bind="127.0.0.1",
        retries=0,
        host_port=device.sockets[0].getsockname()[1],
        request_timeout_ms=100,
        probe_seconds=5,
    )
    events: list[str] = []
    proxy = ModbusProxy(c, "lan", lambda level, kind, **p: events.append(kind), lambda ch: None)
    task = asyncio.create_task(proxy.run())  # quiet since the start: probes at once
    for _ in range(100):
        if proxy.reachable is False:
            break
        await asyncio.sleep(0.05)
    assert proxy.reachable is False and proxy.stats.probes == 1 and proxy.stats.requests == 0
    assert "modbus_down" in events
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    device.close()


def test_unit_map() -> None:
    assert parse_unit_map("1=3, 2->5") == {1: 3, 2: 5}
