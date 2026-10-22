"""Modbus proxy: one Modbus device shared by several Modbus TCP clients.

Many Modbus devices take only one connection at a time (inverters, heat pumps, energy
meters), and a serial RS485 bus (Modbus RTU) can only be opened by one program. Each Modbus
connection of the app listens on a TCP port of its own and speaks Modbus TCP to its clients.
Their requests go to the device one after another over one connection; each answer goes back
to the client that asked.

Towards the device:
- "tcp": Modbus TCP, like modbus-proxy. The app numbers the requests itself, so a late
  answer to a request that timed out is never handed to the next one.
- "rtu": Modbus RTU on a serial device (RS485 adapter), like mbusd.
- "rtu_tcp": Modbus RTU over TCP, e.g. an RS485-to-Ethernet converter in transparent mode.

A request the device does not answer gets Modbus exception 0x0B (gateway target device
failed to respond), one that cannot be sent because the device is not reachable 0x0A
(gateway path unavailable), as a Modbus gateway answers; the client stays connected.
Unit 0 on RTU is a broadcast: it is sent, nobody answers.
"""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import logging
import os
import socket
import struct
import termios
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from .detect import configure
from .model import Connection, client_allowed, parse_unit_map
from .trace import Chunk

_LOGGER = logging.getLogger(__name__)

EXC_FUNCTION = 0x01  # illegal function: the answer to a write that is not allowed
EXC_PATH = 0x0A  # gateway path unavailable
EXC_TARGET = 0x0B  # gateway target device failed to respond
LISTEN_RETRY = 10  # seconds between attempts to open the port
LINK_RETRY = 30  # seconds between attempts to reach a device that is not reachable
FAIL_FAST = (
    10  # s a device that could not be connected is not tried again; clients get 0x0A at once
)
SERIAL_RETRY = 5  # seconds between attempts to open a missing serial device
DOWN_AFTER = 3  # requests in a row without an answer: the device counts as not reachable
QUIET_GAP = 0.05  # s of silence that ends an RTU answer of unknown length
SETTLE_MAX = 0.5  # s an RTU line gets after a timeout or a broken answer, for late bytes
BROADCAST_WAIT = 0.1  # s the bus gets after a broadcast
# functions that only read; anything else (also a vendor's own, like 0x41) counts as a write.
# 8 (diagnostics) is one only with sub-function 0 (an echo), 43 only as 14 (read device id)
READ_ONLY_FUNCTIONS = {1, 2, 3, 4, 7, 11, 12, 17, 20, 24}
READ_FUNCTIONS = {1, 2, 3, 4}  # answered from the cache when it is on
CACHE_SIZE = 2000  # answers kept at most
BUFFER_MAX = 1 << 16  # bytes from the device kept unread at most

FUNCTIONS = {
    1: "read coils",
    2: "read discrete inputs",
    3: "read holding registers",
    4: "read input registers",
    5: "write coil",
    6: "write register",
    7: "read exception status",
    8: "diagnostics",
    11: "get comm event counter",
    15: "write coils",
    16: "write registers",
    17: "report server id",
    22: "mask write register",
    23: "read/write registers",
    43: "device identification",
}
EXCEPTIONS = {
    1: "illegal function",
    2: "illegal data address",
    3: "illegal data value",
    4: "server device failure",
    5: "acknowledge",
    6: "server device busy",
    8: "memory parity error",
    10: "gateway path unavailable",
    11: "gateway target failed to respond",
}


class FrameError(Exception):
    """The device sent something that is not the answer to the request."""


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def rtu_frame(unit: int, pdu: bytes) -> bytes:
    body = bytes([unit]) + pdu
    return body + crc16(body).to_bytes(2, "little")


def rtu_length(head: bytes) -> int | None:
    """The length of an RTU answer from its first three bytes; None when they do not tell."""
    function = head[1]
    if function & 0x80:
        return 5
    if function in (1, 2, 3, 4, 12, 17, 20, 21, 23):
        return 3 + head[2] + 2  # byte count
    if function in (5, 6, 8, 11, 15, 16):
        return 8
    if function == 22:
        return 10
    if function == 7:
        return 5
    return None


def describe(unit: int, pdu: bytes, *, request: bool) -> str:
    """One line on a request or answer for the trace."""
    if not pdu:
        return f"unit {unit}"
    function = pdu[0]
    if function & 0x80:
        code = pdu[1] if len(pdu) > 1 else 0
        name = EXCEPTIONS.get(code, "")
        return f"unit {unit} · FC{function & 0x7F:02d} exception {code:02X} {name}".rstrip()
    text = f"unit {unit} · FC{function:02d} {FUNCTIONS.get(function, '')}".rstrip()
    if request and function in (1, 2, 3, 4, 15, 16) and len(pdu) >= 5:
        address, count = struct.unpack(">HH", pdu[1:5])
        text += f" · @{address} ×{count}"
    elif request and function in (5, 6) and len(pdu) >= 5:
        address, value = struct.unpack(">HH", pdu[1:5])
        text += f" · @{address} = {value}"
    elif not request and function in (1, 2, 3, 4, 23) and len(pdu) >= 2:
        text += f" · {pdu[1]} bytes"
    return text


def answers(pdu: bytes, answer: bytes) -> bool:
    """Can this be the answer to the request? RTU has no transaction ids: a late answer to
    an earlier request must not pass for this one's."""
    function = pdu[0]
    if answer[0] & 0x80 or len(pdu) < 5 or len(answer) < 2:
        return True  # an exception, or nothing to compare
    if function in (1, 2):
        return answer[1] == (int.from_bytes(pdu[3:5], "big") + 7) // 8
    if function in (3, 4):
        return answer[1] == int.from_bytes(pdu[3:5], "big") * 2
    if function in (5, 6, 15, 16):
        return answer[1:5] == pdu[1:5]  # the echo of address and value or count
    return True


def is_write(pdu: bytes) -> bool:
    if not pdu:
        return False
    if pdu[0] == 8:
        return pdu[1:3] != b"\x00\x00"  # 0: return query data (an echo)
    if pdu[0] == 43:
        return pdu[1:2] != b"\x0e"
    return pdu[0] not in READ_ONLY_FUNCTIONS


def read_result(function: int, count: int, answer: bytes | None) -> dict[str, Any]:
    """What a read (functions 1–4) brought, for the tools."""
    if not answer:
        return {"ok": False, "exception": None}
    if answer[0] & 0x80:
        code = answer[1] if len(answer) > 1 else 0
        return {"ok": False, "exception": code, "name": EXCEPTIONS.get(code, "")}
    data = answer[2 : 2 + answer[1]] if len(answer) > 1 else b""
    if function in (3, 4):
        values = [int.from_bytes(data[i : i + 2], "big") for i in range(0, len(data) - 1, 2)]
    else:
        values = [(data[i // 8] >> (i % 8)) & 1 for i in range(min(count, len(data) * 8))]
    return {"ok": True, "values": values, "hex": data.hex(" ").upper()}


WRITE_TOOL_FUNCTIONS = (5, 6, 15, 16)


def write_pdu(function: int, address: int, values: list[int]) -> bytes:
    """The request of the write tool: one coil or register (5, 6) or a run of them (15, 16)."""
    if function not in WRITE_TOOL_FUNCTIONS:
        raise ValueError("function 5, 6, 15 or 16")
    if not 0 <= address <= 65535:
        raise ValueError("address 0 to 65535")
    single = function in (5, 6)
    limit = 1 if single else 1968 if function == 15 else 123
    if not 1 <= len(values) <= limit:
        raise ValueError(f"{'one value' if single else f'1 to {limit} values'}")
    if address + len(values) > 65536:
        raise ValueError("address 0 to 65535")
    coils = function in (5, 15)
    if any(not 0 <= v <= (1 if coils else 65535) for v in values):
        raise ValueError("values 0 or 1" if coils else "values 0 to 65535")
    if function == 5:
        return struct.pack(">BHH", 5, address, 0xFF00 if values[0] else 0)
    if function == 6:
        return struct.pack(">BHH", 6, address, values[0])
    if function == 15:
        packed = bytearray((len(values) + 7) // 8)
        for i, v in enumerate(values):
            packed[i // 8] |= v << (i % 8)
        return struct.pack(">BHHB", 15, address, len(values), len(packed)) + bytes(packed)
    return struct.pack(">BHHB", 16, address, len(values), len(values) * 2) + b"".join(
        struct.pack(">H", v) for v in values
    )


def exception(pdu: bytes, code: int) -> bytes:
    return bytes([(pdu[0] if pdu else 0) | 0x80, code])


# links: byte streams to the device


class Link:
    """A byte stream to the device with an input buffer the framers read from."""

    def __init__(self) -> None:
        self.buffer = bytearray()
        self._data = asyncio.Event()
        self.last_activity = 0.0  # loop time of the last byte in or out

    @property
    def is_open(self) -> bool:
        raise NotImplementedError

    async def open(self, timeout: float) -> None:
        raise NotImplementedError

    async def write(self, data: bytes) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError

    def _received(self, data: bytes) -> None:
        if len(self.buffer) > BUFFER_MAX:  # a device that sends without being asked
            self.buffer.clear()
        self.buffer += data
        self.last_activity = asyncio.get_running_loop().time()
        self._data.set()

    def _lost(self) -> None:
        self._data.set()  # wakes up a waiting read, which then sees the link closed

    def discard(self) -> int:
        """Drop what came in without being asked for (a late answer, noise)."""
        count = len(self.buffer)
        self.buffer.clear()
        return count

    async def _wait(self, deadline: float) -> None:
        if not self.is_open:
            raise ConnectionError("connection to the device closed")
        self._data.clear()
        left = deadline - asyncio.get_running_loop().time()
        if left <= 0:
            raise TimeoutError
        await asyncio.wait_for(self._data.wait(), left)

    async def read_some(self, deadline: float) -> bytes:
        """What came in, waiting until something does."""
        while not self.buffer:
            await self._wait(deadline)
        data = bytes(self.buffer)
        self.buffer.clear()
        return data

    async def read_exactly(self, count: int, deadline: float) -> bytes:
        while len(self.buffer) < count:
            await self._wait(deadline)
        data = bytes(self.buffer[:count])
        del self.buffer[:count]
        return data

    async def read_quiet(self, gap: float, deadline: float) -> bytes:
        """Everything until the line has been quiet for gap seconds."""
        loop = asyncio.get_running_loop()
        while not self.buffer:
            await self._wait(deadline)
        while True:
            try:
                await self._wait(min(deadline, loop.time() + gap))
            except TimeoutError:
                break
        data = bytes(self.buffer)
        self.buffer.clear()
        return data


class TcpLink(Link):
    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self._writer: asyncio.StreamWriter | None = None
        self._pump: asyncio.Task[None] | None = None

    @property
    def is_open(self) -> bool:
        return self._writer is not None and self._pump is not None and not self._pump.done()

    async def open(self, timeout: float) -> None:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout
        )
        sock = writer.get_extra_info("socket")
        if sock is not None:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.buffer.clear()
        self._writer = writer
        self._pump = asyncio.create_task(self._read(reader))

    async def _read(self, reader: asyncio.StreamReader) -> None:
        try:
            while data := await reader.read(4096):
                self._received(data)
        except OSError:
            pass
        finally:
            self._lost()

    async def write(self, data: bytes) -> None:
        if self._writer is None:
            raise ConnectionError("not connected")
        self._writer.write(data)
        await self._writer.drain()
        self.last_activity = asyncio.get_running_loop().time()

    async def close(self) -> None:
        if self._pump is not None:
            self._pump.cancel()
        if self._writer is not None:
            self._writer.close()
            with contextlib.suppress(OSError, asyncio.CancelledError):
                await self._writer.wait_closed()
        self._writer = self._pump = None


class SerialLink(Link):
    def __init__(self, device: str, baud: int, data_bits: int, parity: str, stop_bits: int) -> None:
        super().__init__()
        self.device = device
        self.settings = (baud, data_bits, parity, stop_bits)
        self.fd: int | None = None
        bits = 1 + data_bits + (0 if parity == "n" else 1) + stop_bits
        self.char_time = bits / baud
        # Modbus RTU: 3.5 characters of silence between frames, fixed 1.75 ms above 19200 baud
        self.frame_gap = 3.5 * self.char_time if baud <= 19200 else 0.00175

    @property
    def is_open(self) -> bool:
        return self.fd is not None

    async def open(self, timeout: float) -> None:
        fd = os.open(self.device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            fcntl.ioctl(fd, termios.TIOCEXCL)  # no other program opens it meanwhile
            configure(fd, *self.settings)
        except BaseException:
            os.close(fd)
            raise
        self.buffer.clear()
        self.fd = fd
        asyncio.get_running_loop().add_reader(fd, self._readable)

    def _readable(self) -> None:
        if self.fd is None:
            return
        try:
            data = os.read(self.fd, 4096)
        except BlockingIOError:
            return
        except OSError:
            data = b""
        if data:
            self._received(data)
        else:  # unplugged
            self._close_fd()
            self._lost()

    async def write(self, data: bytes) -> None:
        view = memoryview(data)
        while view:
            if self.fd is None:
                raise ConnectionError("device closed")
            try:
                view = view[os.write(self.fd, view) :]
            except BlockingIOError:
                await asyncio.sleep(0.001)
        # the bytes are on their way: the line is busy until they are out
        loop = asyncio.get_running_loop()
        self.last_activity = loop.time() + len(data) * self.char_time

    def _close_fd(self) -> None:
        if self.fd is not None:
            with contextlib.suppress(Exception):
                asyncio.get_running_loop().remove_reader(self.fd)
            with contextlib.suppress(OSError):
                os.close(self.fd)
            self.fd = None

    async def close(self) -> None:
        self._close_fd()


# framers: Modbus over a link


class TcpFramer:
    """Modbus TCP towards the device, with the app's own transaction ids."""

    def __init__(self, link: Link) -> None:
        self.link = link
        self.tid = 0

    async def exchange(
        self,
        unit: int,
        pdu: bytes,
        timeout: float,
        trace: Callable[[str, bytes, str], None],
        settle: float = SETTLE_MAX,
    ) -> bytes | None:
        self.tid = (self.tid + 1) & 0xFFFF
        frame = struct.pack(">HHHB", self.tid, 0, len(pdu) + 1, unit) + pdu
        self.link.discard()
        trace("tx", frame, describe(unit, pdu, request=True))
        await self.link.write(frame)
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            head = await self.link.read_exactly(7, deadline)
            tid, protocol, length, answer_unit = struct.unpack(">HHHB", head)
            if protocol != 0 or not 2 <= length <= 254:
                raise ConnectionError("the device does not speak Modbus TCP")
            body = await self.link.read_exactly(length - 1, deadline)
            trace("rx", head + body, describe(answer_unit, body, request=False))
            if tid == self.tid:
                return body
            # a late answer to an earlier request: wait for the right one


class RtuFramer:
    """Modbus RTU towards the device, over a serial device or a TCP connection."""

    def __init__(self, link: Link, gap: float) -> None:
        self.link = link
        self.gap = gap  # silence before a request, seconds
        self.char_time = getattr(link, "char_time", 0.0)

    async def exchange(
        self,
        unit: int,
        pdu: bytes,
        timeout: float,
        trace: Callable[[str, bytes, str], None],
        settle: float = SETTLE_MAX,
    ) -> bytes | None:
        loop = asyncio.get_running_loop()
        wait = self.link.last_activity + self.gap - loop.time()
        if wait > 0:
            await asyncio.sleep(wait)
        self.link.discard()
        frame = rtu_frame(unit, pdu)
        trace("tx", frame, describe(unit, pdu, request=True))
        await self.link.write(frame)
        if unit == 0:  # broadcast: no answer
            await asyncio.sleep(BROADCAST_WAIT)
            return None
        deadline = loop.time() + len(frame) * self.char_time + timeout
        try:
            head = await self.link.read_exactly(3, deadline)
            length = rtu_length(head)
            if length is None:
                data = head + await self.link.read_quiet(max(QUIET_GAP, self.gap), deadline)
            else:
                data = head + await self.link.read_exactly(length - 3, deadline)
            body = data[1:-2]
            trace("rx", data, describe(data[0], body, request=False))
            if len(data) < 5 or crc16(data[:-2]) != int.from_bytes(data[-2:], "little"):
                raise FrameError("CRC wrong")
            if data[0] != unit or data[1] & 0x7F != pdu[0] or not answers(pdu, body):
                raise FrameError("answer to another request")
        except (TimeoutError, FrameError):
            # what is still on its way (a late answer, the rest of a broken one) must not
            # be taken for the next request's answer
            await asyncio.sleep(settle)
            self.link.discard()
            raise
        return body


# the proxy


@dataclass
class ClientInfo:
    address: str
    since: float
    requests: int = 0
    failed: int = 0
    blocked: int = 0
    bytes_in: int = 0
    bytes_out: int = 0


@dataclass
class Stats:
    requests: int = 0
    answered: int = 0
    exceptions: int = 0  # answered with a Modbus exception by the device
    timeouts: int = 0
    errors: int = 0  # broken answers and lost connections
    failed: int = 0  # requests the clients got 0x0A / 0x0B for
    blocked: int = 0  # writes refused by the write protection
    cached: int = 0  # reads answered from the cache or together with the same request
    probes: int = 0  # the app's own reads to see whether the device answers
    bytes_to_device: int = 0
    bytes_from_device: int = 0
    time_avg: float = 0.0  # seconds, moving average
    time_max: float = 0.0
    queue_max: int = 0
    last_answer: float = 0.0
    last_error: str = ""
    last_error_at: float = 0.0


@dataclass
class UnitStats:
    """The clients' requests to one unit id (one device on an RS485 bus)."""

    requests: int = 0
    answered: int = 0
    exceptions: int = 0
    failed: int = 0
    time_avg: float = 0.0
    last_answer: float = 0.0

    def to_dict(self, unit: int) -> dict[str, Any]:
        return {
            "unit": unit,
            "requests": self.requests,
            "answered": self.answered,
            "exceptions": self.exceptions,
            "failed": self.failed,
            "time_avg_ms": round(self.time_avg * 1000, 1),
            "last_answer": self.last_answer or None,
        }


@dataclass
class _Client:
    info: ClientInfo
    writer: asyncio.StreamWriter
    task: asyncio.Task[Any] | None = field(default=None, repr=False)


EventSink = Callable[..., None]  # (level, kind, **params)
TraceSink = Callable[[Chunk], None]


def restart_key(c: Connection, listen: str) -> Connection:
    """What a running proxy depends on: a change of anything else does not restart it."""
    return replace(
        c,
        name="",
        trace="off",
        notify_missing=False,
        notify_no_client=False,
        silence_minutes=0,
        template="generic",
        low_latency=False,
        remaddr=f"{c.remaddr}|{listen}",
        # read for every request or client: no restart needed
        max_clients=1,
        kickolduser=False,
        timeout=0,
        request_timeout_ms=0,
        retries=0,
        connect_delay_ms=0,
        write_access="all",
        write_clients="",
        cache_ms=0,
        unit_map="",
        probe_seconds=0,
        probe_unit=1,
        probe_function=3,
        probe_address=0,
    )


@dataclass
class _Job:
    unit: int
    pdu: bytes
    client: ClientInfo
    future: asyncio.Future[bytes | None]
    timeout: float | None = None  # seconds, instead of the connection's
    retries: int | None = None


class Scheduler:
    """The requests waiting for the device. The clients take turns (round robin) and each
    client's requests stay in order, so a client that asks without a pause cannot hold up
    the others."""

    def __init__(self) -> None:
        self._queues: dict[str, deque[_Job]] = {}
        self._turn: deque[str] = deque()
        self._ready = asyncio.Event()
        self.size = 0

    def put(self, key: str, job: _Job) -> None:
        queue = self._queues.get(key)
        if queue is None:
            queue = self._queues[key] = deque()
            self._turn.append(key)
        queue.append(job)
        self.size += 1
        self._ready.set()

    async def get(self) -> _Job:
        while not self.size:
            self._ready.clear()
            await self._ready.wait()
        key = self._turn.popleft()
        queue = self._queues[key]
        job = queue.popleft()
        self.size -= 1
        if queue:
            self._turn.append(key)
        else:
            del self._queues[key]
        return job


class _Path:
    """One connection to the device, with its framing."""

    def __init__(self, c: Connection) -> None:
        if c.link == "rtu":
            self.link: Link = SerialLink(c.device, c.baud, c.data_bits, c.parity, c.stop_bits)
        else:
            self.link = TcpLink(c.host, c.host_port)
        if c.link == "tcp":
            self.framer: TcpFramer | RtuFramer = TcpFramer(self.link)
        else:
            gap = getattr(self.link, "frame_gap", 0.0) + c.request_gap_ms / 1000
            self.framer = RtuFramer(self.link, gap)
        self.last_request = 0.0


class ModbusProxy:
    def __init__(
        self, c: Connection, listen: str, on_event: EventSink, on_trace: TraceSink
    ) -> None:
        self.c = c
        self.listen = listen
        self.key = restart_key(c, listen)
        self.on_event = on_event
        self.on_trace = on_trace
        count = 1 if c.link == "rtu" else c.device_connections  # a serial bus has one line
        self.paths = [_Path(c) for _ in range(count)]
        self.gap = c.request_gap_ms / 1000 if c.link == "tcp" else 0.0  # RTU: in the framer
        self.scheduler = Scheduler()
        self.stats = Stats()
        self.clients: dict[str, _Client] = {}
        self.listening = False
        self.listen_error = ""
        self.reachable: bool | None = None
        self.reachable_since = time.time()
        self._failures = 0  # requests in a row without an answer
        self._down_on_connect = False  # not reachable because connecting failed
        self._connect_failed_at = float("-inf")  # loop time of the last failed attempt

        self._server: asyncio.Server | None = None
        self._workers: list[asyncio.Task[None]] = []
        self.units: dict[int, UnitStats] = {}
        self._probe = ClientInfo("probe", time.time())  # the app's own client for probes
        self.tool = ClientInfo("app", time.time())  # ... and for the tools
        self._last_exchange = 0.0
        self._cache: dict[tuple[int, bytes], tuple[float, bytes]] = {}  # → (time, answer)
        self._inflight: dict[tuple[int, bytes], asyncio.Future[bytes | None]] = {}

    # running

    async def run(self) -> None:
        """Listen for clients and keep the device's connection; until cancelled."""
        failed = False
        try:
            while self._server is None:
                try:
                    await self._start_server()
                except OSError as err:
                    self.listen_error = str(err)
                    if not failed:
                        failed = True
                        self.on_event("error", "listen_failed", port=self.c.port, error=str(err))
                    await asyncio.sleep(LISTEN_RETRY)
            self._workers = [asyncio.create_task(self._work(path)) for path in self.paths]
            self._workers.append(asyncio.create_task(self._probe_loop()))
            await asyncio.gather(*self._workers)
        finally:
            for worker in self._workers:
                worker.cancel()
            await asyncio.gather(*self._workers, return_exceptions=True)
            await self._shutdown()

    async def _start_server(self) -> None:
        host = self.c.bind or ("127.0.0.1" if self.listen == "local" else None)
        self._server = await asyncio.start_server(
            self._client, host, self.c.port, reuse_address=True
        )
        self.listening, self.listen_error = True, ""

    async def _work(self, path: _Path) -> None:
        """Takes the waiting requests to the device over one connection, one at a time."""
        idle = SERIAL_RETRY if self.c.link == "rtu" else LINK_RETRY
        await self._keep_link(path)
        while True:
            try:
                job = await asyncio.wait_for(self.scheduler.get(), idle)
            except TimeoutError:
                await self._keep_link(path)
                continue
            if job.future.done():
                continue  # the client went away meanwhile
            try:
                answer = await self._exchange(path, job)
            except Exception:  # a bug must not stop the worker: the proxy would hang
                _LOGGER.exception("%s: request failed", self.c.name)
                await path.link.close()
                answer = exception(job.pdu, EXC_TARGET)
            if not job.future.done():
                job.future.set_result(answer)

    async def _probe_loop(self) -> None:
        """With probes on, read one register after probe_seconds without a request: the
        state stays right without clients, and an idle connection is not closed."""
        while True:
            seconds = self.c.probe_seconds
            if not seconds:
                await asyncio.sleep(SERIAL_RETRY)  # look again: probes may be switched on
                continue

            quiet = asyncio.get_running_loop().time() - self._last_exchange
            if quiet < seconds:
                await asyncio.sleep(seconds - quiet)
                continue
            pdu = struct.pack(">BHH", self.c.probe_function, self.c.probe_address, 1)
            await self._queued(self.c.probe_unit, pdu, self._probe)
            self._last_exchange = asyncio.get_running_loop().time()  # also when it failed

    async def _keep_link(self, path: _Path) -> None:
        """Connect when the device is not known to be reachable (a serial device: always)."""
        if path.link.is_open or (self.c.link != "rtu" and self.reachable is True):
            return  # a device that closed an idle connection is connected on the next request
        try:
            await self._connect(path)
        except Exception as err:  # also a host name that cannot be looked up at all
            self._down(_text(err), connect=True)

    async def _shutdown(self) -> None:
        if self._server is not None:
            self._server.close()
        for client in list(self.clients.values()):
            client.writer.close()
            if client.task is not None:
                client.task.cancel()
        if self._server is not None:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self._server.wait_closed(), 2)
        self._server = None
        self.listening = False
        for path in self.paths:
            await path.link.close()

    # the device

    async def _connect(self, path: _Path) -> None:
        await path.link.open(self.c.request_timeout_ms / 1000)
        _LOGGER.debug("%s: connected to %s", self.c.name, self.c.upstream)
        if self.c.connect_delay_ms:
            await asyncio.sleep(self.c.connect_delay_ms / 1000)
        if self.c.link != "rtu" and (self.reachable is None or self._down_on_connect):
            # reachable again; a device that takes connections but does not answer only
            # counts once it answers (a serial device: always)
            self._up()

    def _up(self) -> None:
        self._failures = 0
        if self.reachable is not True:
            if self.reachable is False:
                self.on_event("info", "modbus_back", target=self.c.upstream)
            self.reachable, self.reachable_since = True, time.time()

    def _down(self, error: str, *, connect: bool = False) -> None:
        self.stats.last_error, self.stats.last_error_at = error, time.time()
        self._down_on_connect = connect
        if connect:
            self._connect_failed_at = asyncio.get_running_loop().time()
        if self.reachable is not False:
            self.reachable, self.reachable_since = False, time.time()
            self.on_event("warning", "modbus_down", target=self.c.upstream, error=error)

    def _trace(self, address: str) -> Callable[[str, bytes, str], None]:
        def write(direction: str, data: bytes, info: str) -> None:
            if direction == "tx":
                self.stats.bytes_to_device += len(data)
            else:
                self.stats.bytes_from_device += len(data)
            self.on_trace(Chunk(time.time(), direction, data, info=f"{info} · {address}"))

        return write

    async def request(self, unit: int, pdu: bytes, client: ClientInfo) -> bytes | None:
        """The device's answer (PDU) to a request; None for a broadcast.

        With the cache on, a read is answered from an answer to the same read that is at
        most cache_ms old, and the same read while one is on its way waits for that one.
        A write empties the cache."""
        if not (self.c.cache_ms and pdu and pdu[0] in READ_FUNCTIONS):
            answer = await self._queued(unit, pdu, client)
            if self._cache and is_write(pdu):
                self._cache.clear()
            return answer
        key = (unit, pdu)
        now = asyncio.get_running_loop().time()
        hit = self._cache.get(key)
        if hit is not None and now - hit[0] <= self.c.cache_ms / 1000:
            self.stats.cached += 1
            client.requests += 1
            return hit[1]
        pending = self._inflight.get(key)
        if pending is not None:
            try:
                answer = await asyncio.shield(pending)
            except asyncio.CancelledError:
                if not pending.cancelled():
                    raise  # this client went away
            else:
                self.stats.cached += 1
                client.requests += 1
                return answer
        future: asyncio.Future[bytes | None] = asyncio.get_running_loop().create_future()
        self._inflight[key] = future
        try:
            answer = await self._queued(unit, pdu, client)
            future.set_result(answer)
        finally:
            if not future.done():
                future.cancel()
            self._inflight.pop(key, None)
        if answer and not answer[0] & 0x80:
            if len(self._cache) >= CACHE_SIZE:
                self._cache.clear()
            self._cache[key] = (asyncio.get_running_loop().time(), answer)
        return answer

    async def _queued(
        self,
        unit: int,
        pdu: bytes,
        client: ClientInfo,
        *,
        timeout: float | None = None,
        retries: int | None = None,
    ) -> bytes | None:
        future: asyncio.Future[bytes | None] = asyncio.get_running_loop().create_future()
        self.scheduler.put(client.address, _Job(unit, pdu, client, future, timeout, retries))
        self.stats.queue_max = max(self.stats.queue_max, self.scheduler.size)
        try:
            return await future
        finally:
            if not future.done():
                future.cancel()  # the worker skips it

    async def _exchange(self, path: _Path, job: _Job) -> bytes | None:
        """One request to the device, with the retries. The app's own requests (probe,
        tools) are not counted as the clients'; the tools' do not change the state."""
        loop = asyncio.get_running_loop()
        stats, client, unit, pdu = self.stats, job.client, job.unit, job.pdu
        probe, tool = client is self._probe, client is self.tool
        counted = not (probe or tool)
        per_unit = self.units.setdefault(unit, UnitStats()) if counted else UnitStats()
        if probe:
            stats.probes += 1
        elif not tool:
            stats.requests += 1
            client.requests += 1
            per_unit.requests += 1
        if self.gap and (wait := path.last_request + self.gap - loop.time()) > 0:
            await asyncio.sleep(wait)
        timeout = job.timeout or self.c.request_timeout_ms / 1000
        # a scan asks units that are not there: no late answers to wait for
        settle = min(timeout, SETTLE_MAX) if job.timeout else SETTLE_MAX
        retries = self.c.retries if job.retries is None else job.retries
        code = EXC_TARGET
        trace = self._trace(client.address)
        error = ""
        if (
            not path.link.is_open
            and self._down_on_connect
            and not (probe or tool)
            and loop.time() - self._connect_failed_at < FAIL_FAST
        ):  # the device was just tried: do not make the client wait for it again
            stats.failed += 1
            client.failed += 1
            per_unit.failed += 1
            return exception(pdu, EXC_PATH)
        for _ in range(1 + retries):
            if not path.link.is_open:
                try:
                    await self._connect(path)
                except Exception as err:
                    self._down(_text(err), connect=True)
                    code = EXC_PATH
                    break  # connecting again at once would only make the client wait longer
            started, error = loop.time(), ""
            try:
                answer = await path.framer.exchange(unit, pdu, timeout, trace, settle)

            except TimeoutError:
                stats.timeouts += not tool
                error, code = "no answer", EXC_TARGET
                if self.c.link == "tcp" and not tool:
                    await path.link.close()  # start over with a fresh connection
                continue
            except FrameError as err:
                stats.errors += 1
                error, code = str(err), EXC_TARGET
                continue
            except (OSError, ConnectionError) as err:
                stats.errors += 1
                error, code = _text(err), EXC_PATH
                await path.link.close()
                continue
            finally:
                path.last_request = self._last_exchange = loop.time()
                if error and not tool:
                    self._error(error)
            elapsed = loop.time() - started
            if not tool:
                stats.last_answer = time.time()
                stats.time_avg = (
                    elapsed if not stats.time_avg else stats.time_avg * 0.9 + elapsed * 0.1
                )
                stats.time_max = max(stats.time_max, elapsed)
            if counted:
                stats.answered += 1
                per_unit.answered += 1
                per_unit.last_answer = time.time()
                per_unit.time_avg = (
                    elapsed if not per_unit.time_avg else per_unit.time_avg * 0.9 + elapsed * 0.1
                )
                if answer and answer[0] & 0x80:
                    stats.exceptions += 1
                    per_unit.exceptions += 1
            self._up()
            return answer
        if tool:
            return exception(pdu, code)
        if not probe:
            stats.failed += 1
            client.failed += 1
            per_unit.failed += 1
        self._failures += 1
        if probe or self._failures >= DOWN_AFTER:  # a probe has had its retries already
            self._down(stats.last_error or "no answer")
        return exception(pdu, code)

    async def ask(
        self, unit: int, pdu: bytes, *, timeout: float | None = None, retries: int | None = None
    ) -> bytes | None:
        """A request of the app's tools: in turn with the clients, not counted for them."""
        return await self._queued(unit, pdu, self.tool, timeout=timeout, retries=retries)

    def _error(self, text: str) -> None:
        self.stats.last_error, self.stats.last_error_at = text, time.time()
        _LOGGER.debug("%s: %s", self.c.name, text)

    # the clients

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername") or ("?", 0)
        host = str(peer[0])
        address = f"[{host}]:{peer[1]}" if ":" in host else f"{host}:{peer[1]}"
        if not client_allowed(self.c.remaddr, self.listen, host):
            _LOGGER.info("%s: client %s refused (not an allowed network)", self.c.name, address)
            writer.close()
            return
        if len(self.clients) >= self.c.max_clients:
            if not self.c.kickolduser:
                self.on_event("warning", "client_refused", address=address)
                writer.close()
                return
            oldest = min(self.clients.values(), key=lambda cl: cl.info.since)
            oldest.writer.close()
        client = _Client(ClientInfo(address, time.time()), writer, asyncio.current_task())
        self.clients[address] = client
        self.on_event("info", "client_connected", address=address)
        try:
            await self._serve(reader, writer, client.info, host)
        except (asyncio.IncompleteReadError, ConnectionError, OSError, TimeoutError):
            pass
        except ValueError as err:
            _LOGGER.info("%s: client %s closed: %s", self.c.name, address, err)
        finally:
            if self.clients.get(address) is client:
                self.clients.pop(address)
            writer.close()
            self.on_event("info", "client_disconnected", address=address)

    def may_write(self, host: str) -> bool:
        access = self.c.write_access
        if access == "listed":
            return bool(self.c.write_clients) and client_allowed(self.c.write_clients, "all", host)
        return access == "all"

    async def _serve(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        info: ClientInfo,
        host: str,
    ) -> None:
        idle = self.c.timeout or None
        mapped: tuple[str, dict[int, int]] = ("", {})
        while True:
            head = await asyncio.wait_for(reader.readexactly(7), idle)
            tid, protocol, length, unit = struct.unpack(">HHHB", head)
            if protocol != 0 or not 2 <= length <= 254:
                raise ValueError("not Modbus TCP")
            pdu = await reader.readexactly(length - 1)
            info.bytes_in += len(head) + len(pdu)
            if mapped[0] != self.c.unit_map:  # changes without a restart
                mapped = (self.c.unit_map, parse_unit_map(self.c.unit_map))
            device_unit = mapped[1].get(unit, unit)
            if is_write(pdu) and not self.may_write(host):
                self.stats.blocked += 1
                info.blocked += 1
                self.on_event("warning", "write_blocked", address=info.address, function=pdu[0])
                answer: bytes | None = exception(pdu, EXC_FUNCTION)
            else:
                answer = await self.request(device_unit, pdu, info)

            if answer is None:
                continue
            frame = struct.pack(">HHHB", tid, 0, len(answer) + 1, unit) + answer
            writer.write(frame)
            await writer.drain()
            info.bytes_out += len(frame)

    # state

    def state(self) -> dict[str, Any]:
        s = self.stats
        return {
            "listening": self.listening,
            "listen_error": self.listen_error,
            "reachable": self.reachable,
            "reachable_since": self.reachable_since,
            "linked": any(path.link.is_open for path in self.paths),
            "links_open": sum(path.link.is_open for path in self.paths),
            "requests": s.requests,
            "answered": s.answered,
            "exceptions": s.exceptions,
            "timeouts": s.timeouts,
            "errors": s.errors,
            "failed": s.failed,
            "blocked": s.blocked,
            "cached": s.cached,
            "probes": s.probes,
            "units": [self.units[u].to_dict(u) for u in sorted(self.units)],
            "time_avg_ms": round(s.time_avg * 1000, 1),
            "time_max_ms": round(s.time_max * 1000, 1),
            "queue": self.scheduler.size,
            "queue_max": s.queue_max,
            "last_answer": s.last_answer or None,
            "last_error": s.last_error,
            "last_error_at": s.last_error_at or None,
        }


def _text(err: BaseException) -> str:
    if isinstance(err, TimeoutError):
        return "no answer"
    return str(err) or type(err).__name__


# what the app shows of a Modbus connection (kinds.py)


def loaded(c: Connection) -> dict[str, Any]:
    """The values of the "modbus_loaded" event at start."""
    return {
        "link": c.link.upper().replace("_", " over "),
        "target": c.upstream,
        "port": c.port,
        "max_clients": c.max_clients,
    }


def client_row(client: _Client) -> dict[str, Any]:
    info = client.info
    return {
        "address": info.address,
        "since": info.since,
        "bytes_to_client": info.bytes_out,
        "bytes_from_client": info.bytes_in,
        "requests": info.requests,
        "blocked": info.blocked,
        "failed": info.failed,
        "queued": 0,
        "stuck": False,
    }


def mqtt_entities(
    prefix: str, connection_id: str, entity: Callable[..., dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    key = f"device_proxy_{connection_id}"
    return {
        f"{prefix}/binary_sensor/{key}/reachable/config": entity(
            "reachable",
            value_template="{{ 'ON' if value_json.reachable else 'OFF' }}",
            device_class="connectivity",
        ),
        f"{prefix}/sensor/{key}/requests/config": entity(
            "requests",
            value_template="{{ value_json.requests }}",
            state_class="total_increasing",
            icon="mdi:swap-horizontal",
        ),
        f"{prefix}/sensor/{key}/failed/config": entity(
            "failed",
            value_template="{{ value_json.failed }}",
            state_class="total_increasing",
            icon="mdi:alert-circle-outline",
            entity_category="diagnostic",
        ),
        f"{prefix}/sensor/{key}/answer_time/config": entity(
            "answer_time",
            value_template="{{ value_json.answer_time }}",
            unit_of_measurement="ms",
            device_class="duration",
            state_class="measurement",
            entity_category="diagnostic",
        ),
    }


def mqtt_state(state: dict[str, Any]) -> dict[str, Any]:
    """The entities' values from the proxy's state()."""
    return {
        "reachable": state["reachable"] is True,
        "requests": state["requests"],
        "failed": state["failed"],
        "answer_time": state["time_avg_ms"] if state["answered"] else None,
    }
