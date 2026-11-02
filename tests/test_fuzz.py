"""Random and broken input for everything that reads bytes from outside: what a client, a
device or a bus sends must never raise where the proxies do not expect it. The seeds are
fixed, so a failure can be repeated."""

import asyncio
import random
import struct

import pytest

from device_proxy import esp, meter
from device_proxy.listen import JUNK_MAX, BusSniffer
from device_proxy.modbus import (
    ModbusProxy,
    answers,
    crc16,
    describe,
    device_id,
    in_ranges,
    is_sunspec,
    is_write,
    read_result,
    rtu_frame,
    rtu_length,
    sunspec_common,
    write_span,
    written_values,
)
from device_proxy.model import Connection

ROUNDS = 3000
FUNCTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 15, 16, 17, 20, 22, 23, 24, 43, 0x83, 0x90, 0xFF]


def _bytes(rng: random.Random, most: int) -> bytes:
    return rng.randbytes(rng.randint(0, most))


def _pdu(rng: random.Random) -> bytes:
    """Mostly a known function with a body of any length, sometimes anything."""
    if rng.random() < 0.2:
        return _bytes(rng, 260)
    return bytes([rng.choice(FUNCTIONS)]) + _bytes(rng, rng.choice([0, 1, 2, 4, 5, 8, 40, 252]))


def _chunks(rng: random.Random, data: bytes) -> list[bytes]:
    """The bytes as they may come from a socket: cut anywhere."""
    cuts = sorted(rng.sample(range(1, len(data)), min(len(data) - 1, rng.randint(0, 8))))
    return [data[a:b] for a, b in zip([0, *cuts], [*cuts, len(data)], strict=True)]


def test_modbus_requests_and_answers_of_any_shape() -> None:
    rng = random.Random(1)
    for _ in range(ROUNDS):
        pdu, answer, unit = _pdu(rng), _pdu(rng), rng.randint(0, 255)
        describe(unit, pdu, request=True)
        describe(unit, answer, request=False)
        if is_write(pdu):  # what the write log takes of it
            span = write_span(pdu)
            in_ranges(span, [(0, 100), (40000, 40100)])
            written_values(pdu)
        if pdu and answer:
            answers(pdu, answer)
        if len(answer) >= 3:
            rtu_length(answer[:3])
        read_result(rng.randint(1, 4), rng.randint(0, 2000), answer)
        device_id(answer)
        is_sunspec(answer)
        sunspec_common(answer)


def test_a_broken_read_counts_as_a_write() -> None:
    """Only a read of the exact length passes where writing is not allowed."""
    rng = random.Random(2)
    for _ in range(ROUNDS):
        pdu = bytes([rng.choice([1, 2, 3, 4])]) + _bytes(rng, 8)
        assert is_write(pdu) == (len(pdu) != 5)


def _good_bus_frame(rng: random.Random) -> bytes:
    """A frame a master or a slave sends: a read and its answer, a write and its echo, an
    exception."""
    unit, kind = rng.randint(1, 247), rng.randint(0, 3)
    if kind == 0:
        function, address, count = rng.choice([3, 4]), rng.randint(0, 65535), rng.randint(1, 125)
        request = rtu_frame(unit, struct.pack(">BHH", function, address, count))
        return request + rtu_frame(unit, bytes([function, count * 2]) + rng.randbytes(count * 2))
    if kind == 1:
        return rtu_frame(unit, struct.pack(">BHH", 6, rng.randint(0, 65535), rng.randint(0, 65535)))
    if kind == 2:
        count = rng.randint(1, 123)
        head = struct.pack(">BHHB", 16, rng.randint(0, 65535), count, count * 2)
        return rtu_frame(unit, head + rng.randbytes(count * 2))
    return rtu_frame(unit, bytes([rng.choice([0x83, 0x84, 0x86, 0x90]), rng.randint(1, 11)]))


def _bus_frame(rng: random.Random) -> bytes:
    """A right CRC around anything: a frame of a function the app does not know, a broken one."""
    if rng.random() < 0.6:
        return _good_bus_frame(rng)
    return rtu_frame(rng.randint(0, 255), bytes([rng.randint(0, 255)]) + _bytes(rng, 30))


def test_listening_to_a_bus_of_noise_and_frames() -> None:
    rng = random.Random(3)
    for _ in range(300):
        sniffer = BusSniffer()
        stream = b"".join(
            _bus_frame(rng) if rng.random() < 0.6 else _bytes(rng, 20) for _ in range(30)
        )
        now = 1000.0
        for chunk in _chunks(rng, stream):
            for frame in sniffer.feed(chunk, now):
                assert crc16(frame[:-2]) == int.from_bytes(frame[-2:], "little")
            assert len(sniffer.buffer) < JUNK_MAX
            now += 0.01
        sniffer.ranges()
        for unit in range(3):
            sniffer.read(unit, 3, rng.randint(0, 65535), rng.randint(0, 130), 60, now)


def test_listening_finds_every_frame_however_the_bytes_come() -> None:
    rng = random.Random(4)
    for _ in range(300):
        frames = [_good_bus_frame(rng) for _ in range(10)]
        heard = []
        sniffer = BusSniffer()
        for chunk in _chunks(rng, b"".join(frames)):
            heard += sniffer.feed(chunk, 1000.0)
        assert b"".join(heard) == b"".join(frames)


def _esp_frame(rng: random.Random, protocol: str) -> bytes:
    if protocol == "esp2":
        return b"\xa5\x5a" + rng.randbytes(12)
    data, optional = _bytes(rng, 40), _bytes(rng, 10)
    header = len(data).to_bytes(2, "big") + bytes([len(optional), rng.choice([1, 2, 3, 5, 9, 10])])
    return (
        b"\x55"
        + header
        + bytes([esp.crc8(header)])
        + data
        + optional
        + bytes([esp.crc8(data + optional)])
    )


def _what_a_frame_is(protocol: str, frame: bytes) -> None:
    """Everything the proxy asks of a frame (enocean.py)."""
    esp.is_radio(protocol, frame)
    esp.is_response(protocol, frame)
    esp.expects_response(protocol, frame)
    esp.radio_info(protocol, frame)
    esp.signal(protocol, frame)
    esp.radio_key(protocol, frame)
    esp.airtime_ms(protocol, frame)
    esp.is_base_id_request(protocol, frame)
    esp.base_id(protocol, frame)
    esp.base_id(protocol, frame, esp.base_id_request(protocol))
    esp.base_id_writes_left(protocol, frame, None)
    esp.base_id_write_result(protocol, frame)
    esp.describe(protocol, frame)


@pytest.mark.parametrize("protocol", ["esp2", "esp3"])
def test_enocean_streams_of_noise_and_frames(protocol: str) -> None:
    rng = random.Random(5)
    for _ in range(300):
        splitter = esp.Splitter(protocol, clock=lambda: 0.0)
        stream = b"".join(
            _esp_frame(rng, protocol) if rng.random() < 0.6 else _bytes(rng, 30) for _ in range(20)
        )
        for chunk in _chunks(rng, stream):
            for frame in splitter.feed(chunk):
                if protocol == "esp2":
                    assert len(frame) == esp.ESP2_FRAME and frame[:2] == b"\xa5\x5a"
                else:
                    assert esp.crc8(frame[1:5]) == frame[5]
                    assert esp.crc8(frame[6:-1]) == frame[-1]
                _what_a_frame_is(protocol, frame)
            assert len(splitter._buffer) <= esp.ESP3_HEADER + esp.ESP3_MAX_DATA + 1 + len(chunk)


@pytest.mark.parametrize("protocol", ["esp2", "esp3"])
def test_enocean_frames_come_out_whole_however_the_bytes_come(protocol: str) -> None:
    rng = random.Random(6)
    for _ in range(300):
        frames = [_esp_frame(rng, protocol) for _ in range(10)]
        splitter = esp.Splitter(protocol, clock=lambda: 0.0)
        out = [f for chunk in _chunks(rng, b"".join(frames)) for f in splitter.feed(chunk)]
        assert out == frames


def test_meter_analysis_of_noise_and_broken_telegrams() -> None:
    rng = random.Random(7)
    start, end = b"\x1b\x1b\x1b\x1b\x01\x01\x01\x01", b"\x1b\x1b\x1b\x1b\x1a"
    for _ in range(1000):
        body = _bytes(rng, 200)
        data = rng.choice([body, start + body + end + _bytes(rng, 3), b"/ABC5\r\n" + body])
        meter.analyze(data)
        meter.score(data)
        meter.sml_readings(body)


async def _robust_device() -> asyncio.Server:
    """A Modbus TCP device that answers whatever comes: registers for a read, else
    exception 1."""

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while True:
                tid, _, length, unit = struct.unpack(">HHHB", await reader.readexactly(7))
                pdu = await reader.readexactly(length - 1)
                if pdu[0] in (3, 4) and len(pdu) == 5:
                    count = min(int.from_bytes(pdu[3:5], "big"), 125)
                    body = bytes([pdu[0], count * 2]) + bytes(count * 2)
                else:
                    body = bytes([pdu[0] | 0x80, 1])
                writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
        except (asyncio.IncompleteReadError, ConnectionError):
            writer.close()

    return await asyncio.start_server(handle, "127.0.0.1", 0)


async def _garbage_client(port: int, rng: random.Random) -> None:
    """Noise, broken headers, odd requests of any length; then gone, mid-frame or not."""
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
    except OSError:
        return
    try:
        for _ in range(rng.randint(1, 6)):
            kind = rng.random()
            if kind < 0.3:
                data = _bytes(rng, 300)
            else:
                pdu = _pdu(rng)[:253] or b"\x03"
                length = len(pdu) + 1 if kind < 0.8 else rng.randint(0, 65535)
                data = (
                    struct.pack(">HHHB", rng.randint(0, 65535), 0, length, rng.randint(0, 255))
                    + pdu
                )
                if rng.random() < 0.2:
                    data = data[: rng.randint(1, len(data))]  # gone in the middle
            writer.write(data)
            await writer.drain()
            await asyncio.sleep(rng.random() * 0.01)
        if rng.random() < 0.5:
            await asyncio.wait_for(reader.read(4096), 0.2)
    except (OSError, TimeoutError):
        pass
    finally:
        writer.transport.abort()


async def test_a_modbus_proxy_keeps_serving_while_clients_send_garbage() -> None:
    device = await _robust_device()
    c = Connection(
        "Inverter",
        "",
        0,
        kind="modbus",
        host="127.0.0.1",
        host_port=device.sockets[0].getsockname()[1],
        max_clients=20,
        bind="127.0.0.1",
        request_timeout_ms=300,
        retries=0,
        write_access="all",  # odd functions reach the device too
    )
    proxy = ModbusProxy(c, "lan", lambda level, kind, **p: None, lambda ch: None)
    task = asyncio.create_task(proxy.run())
    try:
        async with asyncio.timeout(3):
            while proxy._server is None:
                await asyncio.sleep(0.02)
        port = proxy._server.sockets[0].getsockname()[1]
        rng = random.Random(8)
        for _ in range(10):
            await asyncio.gather(*(_garbage_client(port, rng) for _ in range(15)))
            assert not task.done()
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(struct.pack(">HHHBBHH", 7, 0, 6, 1, 3, 100, 2))
            async with asyncio.timeout(2):
                assert await reader.readexactly(13) == struct.pack(
                    ">HHHBBB", 7, 0, 7, 1, 3, 4
                ) + bytes(4)
            writer.close()
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        device.close()
