"""Runs the 1-Wire proxy under load for a while, the owserver failing now and then.

    .venv/bin/python tools/soak_onewire.py [minutes]   (default 5)

A fake owserver with a few devices answers every read with the path it was asked for and a
counter, so an answer that went to the wrong client shows. Clients as Home Assistant's
integration (a connection for each read), a few with persistent connections, one that
writes, and a few that drop their connection in the middle of a request. Every
OUTAGE_EVERY seconds the owserver is away for OUTAGE_SECONDS, taking turns: not listening,
or listening and never answering (a DS2490 that hangs). The proxy's waiting times are
shortened (printed at the start).

At the end no answer may have reached the wrong client, the proxy and the owserver must
have no connection left, the hosts must have gone after their idle time, the lists the proxy
keeps must stay within their limits, and the limits below must hold: failed reads outside
the outages, peak memory growth. Exit code 1 when not.
"""

from __future__ import annotations

import asyncio
import contextlib
import random
import resource
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "device_proxy" / "app"))

from device_proxy import onewire, onewire_bus  # noqa: E402
from device_proxy.model import Connection  # noqa: E402
from device_proxy.onewire import HEADER, PERSISTENCE, OneWireProxy, answer  # noqa: E402

RNG = random.Random(3)
DEVICES = [f"28.{n:012X}" for n in range(1, 9)] + ["3A.112233445566", "81.0000005F2A1B"]
OUTAGE_EVERY = 40  # s between two outages of the owserver (the first after half of it)
OUTAGE_SECONDS = 6
CLIENTS = 8  # a connection for each read, as pyownet
PERSISTENT = 2
DROPPERS = 2  # connect, send part of a request or all of it, and go
READ_GAP = (0.05, 0.3)  # s between two reads of a client
SHORTER = {
    "PROBE_SECONDS": 1.0,
    "PROBE_TIMEOUT": 1.0,
    "CONNECT_TIMEOUT": 1.0,
    "STATISTICS_SECONDS": 2.0,
    "IDLE_AFTER": 3.0,
    "SWEEP": 1.0,
}
LIMITS = {
    "failed_pct": 2.0,  # reads that failed outside the outages, of all reads then
    "memory_mb": 20.0,
}
MSG_READ, MSG_WRITE = 2, 3


def rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return usage / (1 << 20) if sys.platform == "darwin" else usage / 1024  # peak


class Owserver:
    """A fake owserver: DIRALL, statistics, and reads answered with "<path>|<counter>"."""

    def __init__(self) -> None:
        self.mode = "up"  # "up", "down" (not listening), "hang" (listening, no answers)
        self.server: asyncio.Server | None = None
        self.port = 0
        self.writers: set[asyncio.StreamWriter] = set()
        self.reads = 0

    async def start(self) -> None:
        self.server = await asyncio.start_server(self._serve, "127.0.0.1", self.port)
        self.port = self.server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        if self.server is None:
            return
        self.server.close()
        for writer in list(self.writers):
            writer.transport.abort()
        await self.server.wait_closed()
        self.server = None

    async def _serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.writers.add(writer)
        try:
            while True:
                data, kind, flags, path = await onewire.read_request(reader)
                keep = flags & PERSISTENCE
                while self.mode == "hang":
                    await asyncio.sleep(0.2)
                if RNG.random() < 0.05:  # the bus is slow: the owserver says it is still busy
                    writer.write(HEADER.pack(0, -1, 0, 0, 0, 0))
                    await asyncio.sleep(0.05)
                if kind == 7:
                    body = answer(0, ",".join(f"/{d}" for d in DEVICES).encode() + b"\0", keep)
                elif kind == MSG_READ and path.startswith("/statistics/"):
                    body = answer(2, b"12", keep)
                elif kind == MSG_READ:
                    self.reads += 1
                    value = f"{path}|{self.reads}".encode()
                    body = answer(len(value), value, keep)
                elif kind == MSG_WRITE:
                    body = answer(0, b"", keep)
                else:
                    body = answer(-22, b"", keep)  # EINVAL
                writer.write(body)
                await writer.drain()
                if not keep:
                    break
        except (asyncio.IncompleteReadError, ConnectionError, onewire.ProtocolError):
            pass
        finally:
            self.writers.discard(writer)
            writer.close()


class Tally:
    def __init__(self) -> None:
        self.ok = 0
        self.failed = 0
        self.failed_outside = 0
        self.wrong = 0  # an answer for another path: someone else's
        self.outside = 0  # reads done outside the outages


async def ask(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, path: str,
              flags: int = 0) -> bytes:  # fmt: skip
    writer.write(onewire.request(MSG_READ, path, flags, 64))
    await writer.drain()
    while True:
        head = await reader.readexactly(HEADER.size)
        _version, length, ret, _flags, _size, _offset = HEADER.unpack(head)
        if length == -1:
            continue
        payload = await reader.readexactly(length)
        if ret < 0:
            raise ConnectionError(f"error {ret}")
        return payload


def count(tally: Tally, owserver: Owserver, path: str, value: bytes | None) -> None:
    calm = owserver.mode == "up"
    if calm:
        tally.outside += 1
    if value is None:
        tally.failed += 1
        tally.failed_outside += calm
    elif not value.startswith(f"{path}|".encode()):
        tally.wrong += 1
    else:
        tally.ok += 1


async def one_shot(port: int, owserver: Owserver, stop: asyncio.Event, tally: Tally) -> None:
    """A read on a connection of its own, as Home Assistant's integration does it."""
    while not stop.is_set():
        path = f"/{RNG.choice(DEVICES)}/temperature"
        value = None
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            try:
                value = await asyncio.wait_for(ask(reader, writer, path), 5)
            finally:
                writer.close()
        except (OSError, TimeoutError, asyncio.IncompleteReadError):
            pass
        count(tally, owserver, path, value)
        await asyncio.sleep(RNG.uniform(*READ_GAP))


async def persistent(port: int, owserver: Owserver, stop: asyncio.Event, tally: Tally) -> None:
    """Many reads on one connection, as owhttpd does it; connects again when it is gone."""
    while not stop.is_set():
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
        except OSError:
            await asyncio.sleep(0.5)
            continue
        try:
            while not stop.is_set():
                path = f"/{RNG.choice(DEVICES)}/temperature"
                try:
                    value = await asyncio.wait_for(ask(reader, writer, path, PERSISTENCE), 5)
                except (OSError, TimeoutError, asyncio.IncompleteReadError):
                    count(tally, owserver, path, None)
                    await asyncio.sleep(0.5)  # as a program would, before connecting again
                    break
                count(tally, owserver, path, value)
                await asyncio.sleep(RNG.uniform(*READ_GAP))
        finally:
            writer.close()


async def writer_client(port: int, stop: asyncio.Event, done: list[int]) -> None:
    """Switches an output now and then."""
    while not stop.is_set():
        with contextlib.suppress(OSError, TimeoutError, asyncio.IncompleteReadError):
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            payload = b"/3A.112233445566/PIO.A\x00" + RNG.choice((b"0", b"1"))
            writer.write(HEADER.pack(0, len(payload), MSG_WRITE, 0, 1, 0) + payload)
            await asyncio.wait_for(reader.readexactly(HEADER.size), 5)
            writer.close()
            done.append(1)
        await asyncio.sleep(1.0)


async def dropper(port: int, stop: asyncio.Event) -> None:
    """Goes away in the middle of a request, or right after sending one."""
    while not stop.is_set():
        with contextlib.suppress(OSError):
            _reader, writer = await asyncio.open_connection("127.0.0.1", port)
            message = onewire.request(MSG_READ, f"/{RNG.choice(DEVICES)}/temperature")
            writer.write(message[: RNG.randint(1, len(message))])
            await asyncio.sleep(RNG.uniform(0, 0.2))
            writer.transport.abort()
        await asyncio.sleep(RNG.uniform(0.1, 0.5))


async def outages(owserver: Owserver, stop: asyncio.Event, seen: list[str]) -> None:
    await asyncio.sleep(OUTAGE_EVERY / 2)
    turn = 0
    while not stop.is_set():
        kind = ("down", "hang")[turn % 2]
        turn += 1
        seen.append(kind)
        owserver.mode = kind
        if kind == "down":
            await owserver.stop()
        await asyncio.sleep(OUTAGE_SECONDS)
        if kind == "down":
            await owserver.start()
        owserver.mode = "up"
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), OUTAGE_EVERY)


async def main(minutes: float) -> int:
    for name, value in SHORTER.items():
        setattr(onewire, name, value)
    onewire_bus.KNOWN_FILE = Path(tempfile.mkdtemp()) / "onewire_devices.json"
    owserver = Owserver()
    await owserver.start()
    events: dict[str, int] = {}

    def on_event(level: str, kind: str, **params: object) -> None:
        events[kind] = events.get(kind, 0) + 1

    c = Connection(
        "1-Wire", "", 0, id="0000000a", kind="onewire", link="owserver", host="127.0.0.1",
        host_port=owserver.port, bind="127.0.0.1", max_clients=5,
    )  # fmt: skip
    proxy = OneWireProxy(c, "all", on_event, lambda chunk: None)
    task = asyncio.create_task(proxy.run())
    while not (proxy.listening and proxy.reachable):
        await asyncio.sleep(0.05)
    port = proxy.port
    await asyncio.sleep(0.5)
    base = (rss_mb(), len(asyncio.all_tasks()))
    print(f"start: {base[0]:.1f} MB, {base[1]} tasks; {minutes} min; shorter {SHORTER}")

    stop = asyncio.Event()
    tally = Tally()
    writes: list[int] = []
    seen: list[str] = []
    workers = [asyncio.create_task(outages(owserver, stop, seen))]
    workers += [asyncio.create_task(one_shot(port, owserver, stop, tally)) for _ in range(CLIENTS)]
    workers += [
        asyncio.create_task(persistent(port, owserver, stop, tally)) for _ in range(PERSISTENT)
    ]
    workers += [asyncio.create_task(dropper(port, stop)) for _ in range(DROPPERS)]
    workers.append(asyncio.create_task(writer_client(port, stop, writes)))
    end = time.monotonic() + minutes * 60
    while time.monotonic() < end:
        await asyncio.sleep(min(30, max(0.1, end - time.monotonic())))
        s = proxy.state()
        print(
            f"{time.strftime('%H:%M:%S')} {rss_mb():.1f} MB · {len(asyncio.all_tasks())} tasks · "
            f"owserver {owserver.mode} · reachable {s['reachable']} · open {s['connections']} · "
            f"reads ok {tally.ok} failed {tally.failed} wrong {tally.wrong} · writes {len(writes)}",
            flush=True,
        )
    stop.set()
    owserver.mode = "up"
    for worker in workers:
        worker.cancel()
    await asyncio.gather(*workers, return_exceptions=True)
    if owserver.server is None:
        await owserver.start()
    await asyncio.sleep(SHORTER["IDLE_AFTER"] + 3 * SHORTER["SWEEP"] + 1)  # hosts go idle
    after = (rss_mb(), len(asyncio.all_tasks()))
    state = proxy.state()

    measured = {
        "failed_pct": round(100 * tally.failed_outside / max(1, tally.outside), 2),
        "memory_mb": round(after[0] - base[0], 1),
    }
    print(
        f"end: {after[0]:.1f} MB, {after[1]} tasks; {len(seen)} outages {seen}; "
        f"reads {tally.ok + tally.failed + tally.wrong}; measured {measured}; {events}",
        flush=True,
    )
    problems = [f"{k} {measured[k]} > {v}" for k, v in LIMITS.items() if measured[k] > v]
    if tally.wrong:
        problems.append(f"{tally.wrong} answers reached the wrong client")
    if not tally.ok:
        problems.append("no read went through")
    if state["connections"] or proxy._open:
        problems.append(f"{state['connections']} client connections left at the proxy")
    if owserver.writers:
        problems.append(f"{len(owserver.writers)} connections left at the owserver")
    if proxy.clients:
        problems.append(f"hosts not gone after their idle time: {list(proxy.clients)}")
    if not proxy.reachable:
        problems.append("the owserver is back, the proxy does not say so")
    if len(proxy.writes) > onewire.WRITES_KEPT or not writes:
        problems.append(f"write log {len(proxy.writes)}, writes done {len(writes)}")
    if any(len(d.values) > onewire_bus.VALUES_MAX for d in proxy.bus.devices.values()):
        problems.append("values per device over the limit")
    if state["missing"]:
        problems.append(f"devices missing at the end: {state['missing']}")
    if after[1] > base[1] + 2:
        problems.append("tasks grew")
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    await owserver.stop()
    print("OK" if not problems else f"PROBLEMS: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(float(sys.argv[1]) if len(sys.argv) > 1 else 5)))
