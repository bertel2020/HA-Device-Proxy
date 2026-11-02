"""Runs the Modbus proxy for a while under load against a device that misbehaves.

    .venv/bin/python tools/soak_test.py [minutes] [link]   (default 10, tcp; rtu_tcp or rtu)

rtu runs over a pseudo terminal as the serial device (Linux, see tools/linux_check.py).

The device answers after a random delay, sometimes not at all, sometimes late, now and then
drops the connection or sends garbage, and every OUTAGE_EVERY seconds it is away for
OUTAGE_SECONDS. Clients poll in random patterns, write, ask the same registers (cache), some
go away in the middle of a request; a few slow readers send requests and never read the
answers. Every 30 s a line shows memory, open files, tasks and the proxy's queues.

At the end, with all clients gone, nothing may be left over (waiting requests, requests on
their way, clients), files and tasks must be back near where they started, and the limits
below must hold: answer times of the normal clients, peak memory growth, and how soon after
an outage the device answers again through the proxy. Exit code 1 when not.
"""

from __future__ import annotations

import asyncio
import os
import random
import resource
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "device_proxy" / "app"))

from device_proxy.modbus import ModbusProxy, rtu_frame  # noqa: E402
from device_proxy.model import Connection  # noqa: E402

RNG = random.Random(1)
OUTAGE_EVERY = 90  # s between the device's outages (the first after half of it)
OUTAGE_SECONDS = 10
SLOW_READERS = 3
LIMITS = {  # what the normal clients and the app must stay within
    "p95_s": 1.0,  # answer time of 95 % of the requests (Modbus TCP, two device connections)
    "max_s": 5.0,  # the slowest answer
    "memory_mb": 20.0,  # growth of the peak memory
    "recovery_s": 35.0,  # device back → its first answer through the proxy
}
RTU_LIMITS = {"p95_s": 3.0, "max_s": 8.0}  # over RTU every request waits its turn on one line
DEVICE = {"up": True, "writers": set()}  # the fake device: away or not, its connections


def rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return usage / (1 << 20) if sys.platform == "darwin" else usage / 1024  # peak


def open_files() -> int:
    for folder in ("/proc/self/fd", "/dev/fd"):
        if os.path.isdir(folder):
            return len(os.listdir(folder))
    return -1


def reply(unit: int, pdu: bytes) -> bytes:
    if pdu[0] in (5, 6):
        return pdu  # a write is echoed
    address, count = struct.unpack(">HH", pdu[1:5])
    return bytes([pdu[0], count * 2]) + b"".join(
        struct.pack(">H", (unit * 1000 + address + i) & 0xFFFF) for i in range(count)
    )


def serial_device(master: int) -> None:
    """The device on the other end of a pseudo terminal: no answer, late, garbage, as below."""
    loop = asyncio.get_running_loop()
    buffer = bytearray()

    def readable() -> None:
        try:
            buffer.extend(os.read(master, 4096))
        except OSError:  # the proxy has the serial side closed right now
            loop.remove_reader(master)
            loop.call_later(0.1, loop.add_reader, master, readable)
            return
        while len(buffer) >= 8:  # every request here is 8 bytes
            frame = bytes(buffer[:8])
            del buffer[:8]
            roll = RNG.random()
            if roll < 0.04:
                continue  # no answer
            data = (
                os.urandom(RNG.randint(1, 20))
                if roll < 0.05
                else rtu_frame(frame[0], reply(frame[0], frame[1:6]))
            )
            delay = RNG.uniform(0.002, 0.04) if roll > 0.06 else 0.5
            loop.call_later(delay, write, data)

    def write(data: bytes) -> None:
        try:
            os.write(master, data)
        except OSError:
            pass

    loop.add_reader(master, readable)


async def device(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, rtu: bool) -> None:
    if not DEVICE["up"]:
        writer.close()  # away: takes no connection
        return
    DEVICE["writers"].add(writer)  # type: ignore[attr-defined]
    try:
        while True:
            if rtu:
                frame = await reader.readexactly(8)
                tid, unit, pdu = 0, frame[0], frame[1:6]
            else:
                tid, _, length, unit = struct.unpack(">HHHB", await reader.readexactly(7))
                pdu = await reader.readexactly(length - 1)
            roll = RNG.random()
            if roll < 0.01:
                writer.close()  # drops the connection
                return
            if roll < 0.04:
                continue  # no answer
            await asyncio.sleep(RNG.uniform(0.002, 0.04) if roll > 0.06 else 0.5)  # or late
            body = reply(unit, pdu)
            if roll < 0.05:
                writer.write(os.urandom(RNG.randint(1, 20)))  # garbage
            elif rtu:
                writer.write(rtu_frame(unit, body))
            else:
                writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
            await writer.drain()
    except (asyncio.IncompleteReadError, ConnectionError):
        writer.close()
    finally:
        DEVICE["writers"].discard(writer)  # type: ignore[attr-defined]


async def outages(stop: asyncio.Event, back: list[float]) -> None:
    """The device goes away now and then (its connections drop, new ones are refused)."""
    await asyncio.sleep(OUTAGE_EVERY / 2)
    while not stop.is_set():
        DEVICE["up"] = False
        for writer in list(DEVICE["writers"]):  # type: ignore[call-overload]
            writer.transport.abort()
        print(f"{time.strftime('%H:%M:%S')} device away for {OUTAGE_SECONDS} s", flush=True)
        await asyncio.sleep(OUTAGE_SECONDS)
        DEVICE["up"] = True
        back.append(time.monotonic())
        await asyncio.sleep(OUTAGE_EVERY - OUTAGE_SECONDS)


async def slow_reader(port: int, stop: asyncio.Event) -> None:
    """Polls like a normal client but never takes an answer: once the buffers are full the
    proxy stops reading it, and it must hold nobody else up."""
    try:
        _, writer = await asyncio.open_connection("127.0.0.1", port)
    except OSError:
        return
    tid = 0
    while not stop.is_set():
        tid = (tid + 1) & 0xFFFF
        writer.write(struct.pack(">HHHBBHH", tid, 0, 6, 1, 3, 0, 120))
        await asyncio.sleep(0.02)
        if writer.transport.get_write_buffer_size() > 1 << 16:
            await asyncio.sleep(1)  # its own side is full too: the proxy holds it back
    writer.transport.abort()


async def client(
    port: int, stop: asyncio.Event, stats: dict[str, int], times: list[float], ok_at: list[float]
) -> None:
    tid = 0
    while not stop.is_set():
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
        except OSError:
            stats["connect_failed"] += 1
            await asyncio.sleep(1)
            continue
        try:
            for _ in range(RNG.randint(1, 200)):
                if stop.is_set():
                    break
                tid = (tid + 1) & 0xFFFF
                unit = RNG.choice((1, 1, 1, 2, 3))
                if RNG.random() < 0.05:
                    pdu = struct.pack(">BHH", 6, RNG.randint(0, 10), RNG.randint(0, 99))
                else:
                    pdu = struct.pack(">BHH", 3, RNG.choice((0, 0, 100, 200)), RNG.randint(1, 10))
                expected = (
                    pdu
                    if pdu[0] == 6
                    else bytes([3, pdu[4] * 2])
                    + b"".join(
                        struct.pack(">H", (unit * 1000 + pdu[2] + i) & 0xFFFF)
                        for i in range(pdu[4])
                    )
                )
                writer.write(struct.pack(">HHHB", tid, 0, len(pdu) + 1, unit) + pdu)
                await writer.drain()
                sent = time.monotonic()
                if RNG.random() < 0.01:
                    stats["walked_away"] += 1
                    break  # goes away in the middle of a request
                head = await asyncio.wait_for(reader.readexactly(7), 30)
                got, _, length, _ = struct.unpack(">HHHB", head)
                body = await reader.readexactly(length - 1)
                times.append(time.monotonic() - sent)
                stats["answers" if not body[0] & 0x80 else "exceptions"] += 1
                if not body[0] & 0x80 and unit == 1:
                    ok_at.append(time.monotonic())
                if got != tid:
                    stats["wrong_tid"] += 1
                if not body[0] & 0x80 and body != expected:
                    stats["wrong_answer"] += 1  # an answer to another request
                await asyncio.sleep(RNG.uniform(0, 0.3))
        except (OSError, asyncio.IncompleteReadError, TimeoutError):
            stats["client_errors"] += 1
        finally:
            writer.close()
        await asyncio.sleep(RNG.uniform(0, 1))


async def main(minutes: float, link: str) -> int:
    rtu = link == "rtu_tcp"
    server = await asyncio.start_server(lambda r, w: device(r, w, rtu), "127.0.0.1", 0)
    path = ""
    if link == "rtu":
        master, slave = os.openpty()
        path = os.ttyname(slave)
        os.close(slave)  # the proxy opens it, exclusively
        serial_device(master)
    c = Connection(
        "Soak",
        path,
        0,
        kind="modbus",
        link=link,
        baud=115200,
        host="127.0.0.1",
        host_port=server.sockets[0].getsockname()[1],
        bind="127.0.0.1",
        max_clients=30,
        request_timeout_ms=200,
        retries=1,
        cache_ms=300,
        probe_seconds=5,
        device_connections=2 if link == "tcp" else 1,
        write_access="listed",
        write_clients="127.0.0.1",
    )
    events: dict[str, int] = {}

    def on_event(level: str, kind: str, **params: object) -> None:
        events[kind] = events.get(kind, 0) + 1

    proxy = ModbusProxy(c, "lan", on_event, lambda chunk: None)
    task = asyncio.create_task(proxy.run())
    while proxy._server is None:
        await asyncio.sleep(0.01)
    port = proxy._server.sockets[0].getsockname()[1]
    await asyncio.sleep(0.5)
    base = (rss_mb(), open_files(), len(asyncio.all_tasks()))
    stats = {
        k: 0
        for k in (
            "answers",
            "exceptions",
            "wrong_tid",
            "wrong_answer",
            "client_errors",
            "walked_away",
            "connect_failed",
        )
    }
    stop = asyncio.Event()
    times: list[float] = []
    ok_at: list[float] = []
    back: list[float] = []
    clients = [asyncio.create_task(client(port, stop, stats, times, ok_at)) for _ in range(20)]
    clients += [asyncio.create_task(slow_reader(port, stop)) for _ in range(SLOW_READERS)]
    clients.append(asyncio.create_task(outages(stop, back)))
    end = time.monotonic() + minutes * 60
    print(f"start: {base[0]:.1f} MB, {base[1]} files, {base[2]} tasks; {minutes} min, {link}")
    while time.monotonic() < end:
        await asyncio.sleep(min(30, max(0.1, end - time.monotonic())))
        s = proxy.stats
        print(
            f"{time.strftime('%H:%M:%S')} {rss_mb():.1f} MB · {open_files()} files · "
            f"{len(asyncio.all_tasks())} tasks · clients {len(proxy.clients)} · "
            f"queue {proxy.scheduler.size} · inflight {len(proxy._inflight)} · "
            f"cache {len(proxy._cache)} · requests {s.requests} answered {s.answered} "
            f"cached {s.cached} timeouts {s.timeouts} errors {s.errors} failed {s.failed} "
            f"blocked {s.blocked} probes {s.probes} · {stats}",
            flush=True,
        )
    stop.set()
    await asyncio.wait_for(asyncio.gather(*clients, return_exceptions=True), 60)
    await asyncio.sleep(2)  # the proxy notices the closed clients
    left = {
        "clients": len(proxy.clients),
        "queue": proxy.scheduler.size,
        "inflight": len(proxy._inflight),
    }
    after = (rss_mb(), open_files(), len(asyncio.all_tasks()))
    print(f"end: {after[0]:.1f} MB, {after[1]} files, {after[2]} tasks; left {left}; {events}")
    times.sort()
    p95 = times[int(len(times) * 0.95)] if times else 0.0
    slowest = times[-1] if times else 0.0
    # each time the device came back: until a client got an answer from it again
    recovery = [next((t for t in ok_at if t >= b), float("inf")) - b for b in back]
    measured = {
        "p95_s": round(p95, 3),
        "max_s": round(slowest, 3),
        "memory_mb": round(after[0] - base[0], 1),
        "recovery_s": round(max(recovery), 1) if recovery else 0.0,
    }
    print(f"measured {measured} · {len(back)} outages", flush=True)
    problems = [k for k, v in left.items() if v]
    limits = {**LIMITS, **(RTU_LIMITS if link != "tcp" else {})}
    problems += [f"{k} {measured[k]} > {v}" for k, v in limits.items() if measured[k] > v]
    if stats["wrong_tid"]:
        problems.append("answers with a wrong transaction id")
    if stats["wrong_answer"]:
        problems.append("answers to other requests")
    if after[1] > base[1] + 5:
        problems.append("open files grew")
    if after[2] > base[2] + 2:
        problems.append("tasks grew")
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    server.close()
    print("OK" if not problems else f"PROBLEMS: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 10
    link = sys.argv[2] if len(sys.argv) > 2 else "tcp"
    sys.exit(asyncio.run(main(minutes, link)))
