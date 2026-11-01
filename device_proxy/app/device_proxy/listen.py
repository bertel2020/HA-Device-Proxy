"""Listening to an RS485 bus that has a master already, without ever sending on it.

Many devices sit on a bus whose master polls them all the time: an inverter its energy
meter, a heat pump's controller its modules. A second master would disturb them. Here the
app only listens (link "rtu_listen"): it splits the bytes into frames by their CRC (pauses
between frames get lost behind USB adapters), pairs each read with its answer and keeps the
registers. Modbus TCP clients read them from there; nothing they send reaches the bus.

A read is answered when every register asked for was heard within listen_max_age_s; else
the client gets exception 0x0B (the target did not answer), as from a gateway whose device
is away. Writes are refused with exception 0x01.
"""

from __future__ import annotations

import asyncio
import struct
import time
from typing import Any

from .modbus import (
    EXC_FUNCTION,
    EXC_TARGET,
    SERIAL_RETRY,
    ClientInfo,
    ModbusProxy,
    UnitStats,
    crc16,
    describe,
    exception,
    is_write,
)
from .trace import Chunk

SILENT_AFTER = 30.0  # s without a valid frame: the bus counts as silent
JUNK_MAX = 300  # bytes kept while no frame fits, before the first is dropped
READ_FUNCTIONS = (3, 4)  # holding and input registers


def _lengths(buffer: bytes | bytearray) -> list[int]:
    """The lengths a frame starting here could have, request or answer."""
    if len(buffer) < 3:
        return []
    function = buffer[1]
    if function & 0x80:
        return [5]
    if function in (1, 2, 3, 4):
        return [8, 5 + buffer[2]]  # read request, answer with its byte count
    if function in (5, 6):
        return [8]  # request and its echo
    if function in (15, 16):
        return [8] + ([9 + buffer[6]] if len(buffer) > 6 else [])
    if function == 23:
        return [5 + buffer[2]] + ([13 + buffer[10]] if len(buffer) > 10 else [])
    return []


class BusSniffer:
    """Frames out of the bytes heard on the bus, and the registers out of the frames."""

    def __init__(self) -> None:
        self.buffer = bytearray()
        self.pending: dict[int, tuple[int, int, int]] = {}  # unit → (function, address, count)
        self.writes: dict[int, tuple[int, list[int]]] = {}  # unit → (address, values) asked
        self.registers: dict[tuple[int, int, int], tuple[int, float]] = {}  # → (value, time)
        self.frames = 0
        self.dropped = 0  # bytes that fitted no frame (noise, a frame heard in part)

    def feed(self, data: bytes, now: float | None = None) -> list[bytes]:
        """The complete frames in the bytes heard so far (the rest waits for more)."""
        now = time.time() if now is None else now
        self.buffer += data
        frames = []
        while len(self.buffer) >= 4:
            frame, waiting = self._frame()
            if frame is not None:
                del self.buffer[: len(frame)]
                frames.append(frame)
                self.frames += 1
                self._observe(frame, now)
            elif waiting and len(self.buffer) < JUNK_MAX:
                break
            else:
                del self.buffer[0]
                self.dropped += 1
        return frames

    def _frame(self) -> tuple[bytes | None, bool]:
        waiting = False
        for length in sorted(set(_lengths(self.buffer))):
            if len(self.buffer) < length:
                waiting = True
                continue
            candidate = bytes(self.buffer[:length])
            if crc16(candidate[:-2]) == int.from_bytes(candidate[-2:], "little"):
                return candidate, False
        return None, waiting

    def _observe(self, frame: bytes, now: float) -> None:
        unit, function = frame[0], frame[1]
        if function & 0x80:
            self.pending.pop(unit, None)
            return
        if function in READ_FUNCTIONS:
            if len(frame) == 8:  # a request (an answer has an odd length)
                address, count = struct.unpack(">HH", frame[2:6])
                self.pending[unit] = (function, address, count)
                return
            asked = self.pending.pop(unit, None)
            if asked is None or asked[0] != function or frame[2] != 2 * asked[2]:
                return
            data = frame[3:-2]
            for i in range(asked[2]):
                value = int.from_bytes(data[2 * i : 2 * i + 2], "big")
                self.registers[(unit, function, asked[1] + i)] = (value, now)
        elif function == 6 and len(frame) == 8:  # a write the master made: request = echo
            address, value = struct.unpack(">HH", frame[2:6])
            self.registers[(unit, 3, address)] = (value, now)
        elif function == 16:
            if len(frame) > 8:
                address, count = struct.unpack(">HH", frame[2:6])
                data = frame[7:-2]
                values = [int.from_bytes(data[i : i + 2], "big") for i in range(0, 2 * count, 2)]
                self.writes[unit] = (address, values)
            elif (asked_write := self.writes.pop(unit, None)) is not None:  # the device's OK
                for i, value in enumerate(asked_write[1]):
                    self.registers[(unit, 3, asked_write[0] + i)] = (value, now)

    def read(
        self, unit: int, function: int, address: int, count: int, max_age: float, now: float
    ) -> list[int] | None:
        """The registers as heard, or None when one of them was not heard in time."""
        values = []
        for a in range(address, address + count):
            heard = self.registers.get((unit, function, a))
            if heard is None or now - heard[1] > max_age:
                return None
            values.append(heard[0])
        return values

    def ranges(self) -> list[dict[str, Any]]:
        """What is known, as runs of addresses per unit and function, for the status page."""
        result: list[dict[str, Any]] = []
        keys = sorted(self.registers)
        for unit, function, address in keys:
            last = result[-1] if result else None
            if (
                last
                and (last["unit"], last["function"]) == (unit, function)
                and (last["last"] + 1 == address)
            ):
                last["last"] = address
                last["heard"] = max(last["heard"], self.registers[(unit, function, address)][1])
            else:
                result.append(
                    {
                        "unit": unit,
                        "function": function,
                        "first": address,
                        "last": address,
                        "heard": self.registers[(unit, function, address)][1],
                    }
                )
        return result


class ListenProxy(ModbusProxy):
    """A Modbus TCP server fed by what the bus's own master asks and gets."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.sniffer = BusSniffer()
        self.last_frame = 0.0

    async def run(self) -> None:
        try:
            await self._listen_for_clients()
            self._workers = [asyncio.create_task(self._sniff())]
            await asyncio.gather(*self._workers)
        finally:
            for worker in self._workers:
                worker.cancel()
            await asyncio.gather(*self._workers, return_exceptions=True)
            await self._shutdown()

    async def _listen_for_clients(self) -> None:
        failed = False
        while self._server is None:
            try:
                await self._start_server()
            except OSError as err:
                self.listen_error = str(err)
                if not failed:
                    failed = True
                    self.on_event("error", "listen_failed", port=self.c.port, error=str(err))
                await asyncio.sleep(SERIAL_RETRY)

    async def _sniff(self) -> None:
        """Read the bus and nothing else: the adapter is opened but never written to."""
        link = self.paths[0].link
        loop = asyncio.get_running_loop()
        while True:
            if not link.is_open:
                try:
                    await link.open(1.0)
                except Exception as err:  # the adapter is away
                    self._down(str(err) or type(err).__name__, connect=True)
                    await asyncio.sleep(SERIAL_RETRY)
                    continue
            try:
                data = await link.read_some(loop.time() + SILENT_AFTER)
            except (TimeoutError, ConnectionError, OSError):
                data = b""
            if not link.is_open:
                self._down("the adapter was closed")
                continue
            if not data:
                self._down("no traffic on the bus")
                continue
            self.stats.bytes_from_device += len(data)
            for frame in self.sniffer.feed(data):
                self.last_frame = time.time()
                self._up()
                function = frame[1]
                request = len(frame) == 8 and function in (1, 2, 3, 4)
                info = describe(frame[0], frame[1:-2], request=request) + " · bus"
                self.on_trace(Chunk(time.time(), "tx" if request else "rx", frame, info=info))

    async def request(self, unit: int, pdu: bytes, client: ClientInfo) -> bytes | None:
        """A client's read, answered from what was heard; nothing goes to the bus."""
        self.stats.requests += 1
        client.requests += 1
        stats = self.units.setdefault(unit, UnitStats())
        stats.requests += 1
        if is_write(pdu) or not pdu or pdu[0] not in READ_FUNCTIONS or len(pdu) != 5:
            stats.exceptions += 1
            self.stats.exceptions += 1
            return exception(pdu or b"\x00", EXC_FUNCTION)
        address, count = struct.unpack(">HH", pdu[1:5])
        values = self.sniffer.read(
            unit, pdu[0], address, count, self.c.listen_max_age_s, time.time()
        )
        if values is None:
            stats.failed += 1
            client.failed += 1
            self.stats.failed += 1
            return exception(pdu, EXC_TARGET)
        self.stats.answered += 1
        self.stats.cached += 1
        stats.answered += 1
        stats.last_answer = self.stats.last_answer = time.time()
        return bytes([pdu[0], 2 * count]) + b"".join(v.to_bytes(2, "big") for v in values)

    async def ask(
        self, unit: int, pdu: bytes, *, timeout: float | None = None, retries: int | None = None
    ) -> bytes | None:
        return await self.request(unit, pdu, self.tool)

    def state(self) -> dict[str, Any]:
        return {
            **super().state(),
            "listen": {
                "frames": self.sniffer.frames,
                "dropped": self.sniffer.dropped,
                "last_frame": self.last_frame or None,
                "registers": len(self.sniffer.registers),
                "ranges": self.sniffer.ranges()[:50],
            },
        }
