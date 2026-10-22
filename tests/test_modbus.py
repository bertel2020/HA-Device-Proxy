import asyncio
import struct

from device_proxy.modbus import ClientInfo, ModbusProxy, Scheduler, _Job, crc16, rtu_frame
from device_proxy.model import Connection, parse_unit_map


async def _device(rtu: bool, ignore: set[int], connections: int = 1, late_first: bool = False):
    """A Modbus device on a TCP port that takes this many connections and answers slowly;
    holding register n holds n * 10. Requests for units in ignore get no answer; with
    late_first the first answer comes very late."""
    busy = asyncio.Semaphore(connections)
    late = [late_first]

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
                await asyncio.sleep(0.3 if late and late.pop() else 0.02)
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


async def test_several_connections_to_the_device() -> None:
    device = await _device(False, ignore=set(), connections=2)
    c = Connection(
        "Inverter",
        "",
        0,
        kind="modbus",
        host="127.0.0.1",
        bind="127.0.0.1",
        max_clients=10,
        host_port=device.sockets[0].getsockname()[1],
        device_connections=2,
    )
    proxy = ModbusProxy(c, "lan", lambda level, kind, **p: None, lambda ch: None)
    task = asyncio.create_task(proxy.run())
    while proxy._server is None:
        await asyncio.sleep(0.01)
    port = proxy._server.sockets[0].getsockname()[1]
    answers = await asyncio.gather(*(_read(port, n, 1, n) for n in range(8)))
    assert [a[2:4] for a in answers] == [struct.pack(">H", n * 10) for n in range(8)]
    assert proxy.state()["links_open"] == 2 and proxy.stats.failed == 0
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    device.close()


async def test_a_failing_request_does_not_stop_the_proxy() -> None:
    device = await _device(False, ignore=set())
    c = Connection(
        "Inverter",
        "",
        0,
        kind="modbus",
        host="127.0.0.1",
        bind="127.0.0.1",
        host_port=device.sockets[0].getsockname()[1],
    )
    failures = [RuntimeError("a bug")]

    def trace(chunk: object) -> None:
        if failures:
            raise failures.pop()

    proxy = ModbusProxy(c, "lan", lambda level, kind, **p: None, trace)
    task = asyncio.create_task(proxy.run())
    while proxy._server is None:
        await asyncio.sleep(0.01)
    port = proxy._server.sockets[0].getsockname()[1]
    assert await _read(port, 1, 1, 0) == bytes([0x83, 0x0B])  # the bug: an exception ...
    assert (await _read(port, 2, 1, 3))[2:4] == struct.pack(">H", 30)  # ... and on it goes
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    device.close()


async def test_a_late_rtu_answer_is_not_taken_for_the_next_one() -> None:
    device = await _device(True, ignore=set(), late_first=True)
    c = Connection(
        "Bus",
        "",
        0,
        kind="modbus",
        link="rtu_tcp",
        host="127.0.0.1",
        bind="127.0.0.1",
        host_port=device.sockets[0].getsockname()[1],
        request_timeout_ms=100,
        retries=0,
    )
    proxy = ModbusProxy(c, "lan", lambda level, kind, **p: None, lambda ch: None)
    task = asyncio.create_task(proxy.run())
    while proxy._server is None:
        await asyncio.sleep(0.01)
    port = proxy._server.sockets[0].getsockname()[1]
    assert await _read(port, 1, 1, 0) == bytes([0x83, 0x0B])  # too late
    assert (await _read(port, 2, 1, 5))[2:6] == struct.pack(">HH", 50, 60)  # not its answer
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    device.close()


def test_only_known_reads_pass_without_write_access() -> None:
    from device_proxy.modbus import is_write

    assert not is_write(bytes.fromhex("030000000a"))
    assert not is_write(bytes.fromhex("08000012"))  # diagnostics: echo
    assert not is_write(bytes.fromhex("2b0e0100"))  # read device identification
    assert is_write(bytes.fromhex("06000100ff"))
    assert is_write(bytes.fromhex("0800010000"))  # diagnostics: restart
    assert is_write(bytes.fromhex("41000100"))  # a vendor's own function
    assert is_write(bytes.fromhex("2b0d0000"))  # MEI type other than 14


def test_the_write_tool_builds_the_four_write_requests() -> None:
    import pytest

    from device_proxy.modbus import write_pdu

    assert write_pdu(5, 7, [1]).hex() == "050007ff00"
    assert write_pdu(5, 7, [0]).hex() == "0500070000"
    assert write_pdu(6, 40017, [300]).hex() == "069c51012c"
    assert write_pdu(15, 0, [1, 0, 1, 1, 0, 0, 0, 0, 1]).hex() == "0f00000009020d01"
    assert write_pdu(16, 2, [1, 65535]).hex() == "1000020002040001ffff"
    for bad in (
        (3, 0, [1]),
        (6, 0, [65536]),
        (5, 0, [2]),
        (6, 0, [1, 2]),
        (16, 65535, [1, 2]),
        (16, 0, []),
    ):
        with pytest.raises(ValueError):
            write_pdu(*bad)


def test_an_unusual_baud_rate_is_an_error_not_a_crash() -> None:
    import pytest

    from device_proxy.detect import configure

    with pytest.raises(OSError, match="baud rate 12345"):
        configure(0, 12345, 8, "n", 1)
    with pytest.raises(OSError, match="parity"):
        configure(0, 9600, 8, "m", 1)


async def test_clients_get_an_answer_at_once_while_the_device_is_not_reachable() -> None:
    probe = await asyncio.start_server(lambda r, w: None, "127.0.0.1", 0)
    closed_port = probe.sockets[0].getsockname()[1]
    probe.close()
    await probe.wait_closed()  # nothing listens here now
    c = Connection(
        "Inverter",
        "",
        0,
        kind="modbus",
        host="127.0.0.1",
        bind="127.0.0.1",
        retries=3,
        host_port=closed_port,
        request_timeout_ms=100,
    )
    proxy = ModbusProxy(c, "lan", lambda level, kind, **p: None, lambda ch: None)
    task = asyncio.create_task(proxy.run())
    while proxy._server is None:
        await asyncio.sleep(0.01)
    port = proxy._server.sockets[0].getsockname()[1]
    for _ in range(3):  # the first request finds out, the others are turned away at once
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(struct.pack(">HHHBBHH", 1, 0, 6, 1, 3, 0, 1))
        assert await asyncio.wait_for(reader.readexactly(9), 2) == struct.pack(
            ">HHHB", 1, 0, 3, 1
        ) + bytes([0x83, 0x0A])
        writer.close()
    assert proxy.reachable is False and proxy.stats.failed == 3
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


def test_a_termios_error_is_an_oserror(tmp_path: object) -> None:
    import os
    import tempfile

    import pytest

    from device_proxy.detect import configure

    with tempfile.TemporaryFile() as f, pytest.raises(OSError):  # not a tty
        configure(f.fileno(), 9600, 8, "n", 1)
    assert os.name == "posix"


def test_host_names_with_empty_or_long_labels_are_refused() -> None:
    import pytest

    from device_proxy.model import ValidationError

    for host in ("a..b", ".", "a.", "-a", "a" * 64 + ".de"):
        with pytest.raises(ValidationError):
            Connection("WR", "", 15020, kind="modbus", host=host, host_port=502).validate()
    for host in ("wr.local", "192.168.1.5", "a" * 63, "[fd00::1]"):
        Connection("WR", "", 15020, kind="modbus", host=host, host_port=502).validate()
