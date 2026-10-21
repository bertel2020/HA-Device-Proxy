"""Runs the Modbus proxy for a while under load against a device that misbehaves.

    .venv/bin/python tools/soak_test.py [minutes] [link]     (default 10, tcp; or rtu_tcp)

The device answers after a random delay, sometimes not at all, sometimes late, now and then
drops the connection or sends garbage. Clients poll in random patterns, write, ask the same
registers (cache), some go away in the middle of a request. Every 30 s a line shows memory,
open files, tasks and the proxy's queues; at the end, with all clients gone, nothing may be
left over (waiting requests, requests on their way, clients) and memory, files and tasks
must be back near where they started. Exit code 1 when not.
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


def rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return usage / (1 << 20) if sys.platform == "darwin" else usage / 1024  # peak


def open_files() -> int:
    for folder in ("/proc/self/fd", "/dev/fd"):
        if os.path.isdir(folder):
            return len(os.listdir(folder))
    return -1


async def device(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, rtu: bool) -> None:
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
            if pdu[0] in (5, 6):
                body = pdu  # a write is echoed
            else:
                address, count = struct.unpack(">HH", pdu[1:5])
                body = bytes([pdu[0], count * 2]) + b"".join(
                    struct.pack(">H", (unit * 1000 + address + i) & 0xFFFF) for i in range(count)
                )
            if roll < 0.05:
                writer.write(os.urandom(RNG.randint(1, 20)))  # garbage
            elif rtu:
                writer.write(rtu_frame(unit, body))
            else:
                writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
            await writer.drain()
    except (asyncio.IncompleteReadError, ConnectionError):
        writer.close()


async def client(port: int, stop: asyncio.Event, stats: dict[str, int]) -> None:
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
                if RNG.random() < 0.01:
                    stats["walked_away"] += 1
                    break  # goes away in the middle of a request
                head = await asyncio.wait_for(reader.readexactly(7), 30)
                got, _, length, _ = struct.unpack(">HHHB", head)
                body = await reader.readexactly(length - 1)
                stats["answers" if not body[0] & 0x80 else "exceptions"] += 1
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
    c = Connection(
        "Soak",
        "",
        0,
        kind="modbus",
        link=link,
        host="127.0.0.1",
        host_port=server.sockets[0].getsockname()[1],
        bind="127.0.0.1",
        max_clients=30,
        request_timeout_ms=200,
        retries=1,
        cache_ms=300,
        probe_seconds=5,
        device_connections=1 if rtu else 2,
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
    clients = [asyncio.create_task(client(port, stop, stats)) for _ in range(20)]
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
    problems = [k for k, v in left.items() if v]
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
