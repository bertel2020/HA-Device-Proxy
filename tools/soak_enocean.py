"""Runs an EnOcean gateway with its fallback for a while, the main gateway failing now and then.

    .venv/bin/python tools/soak_enocean.py [minutes]   (default 5)

Two fake ESP2 gateways (A and its fallback B, the same base ID) hear the same radio: a
telegram with a counter every 50 ms. Every FLAP_EVERY seconds A is away for FLAP_SECONDS;
B stands in, and A takes over again once it ran steadily. Clients read along, send
commands, a few ask for the replay buffer, a few never read at all. The waiting times of the
fallback check are shortened (printed at the start), so that a run of minutes sees many
switches.

At the end every client must have had each telegram at most once, the gateways must have
got whole frames only, nothing may be left over, and the limits below must hold: telegrams
lost per client, how soon B stood in and A took over again, peak memory growth. Exit code 1
when not.
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

from device_proxy import enocean, esp  # noqa: E402
from device_proxy.enocean import REPLAY_REQUEST, EnOceanProxy  # noqa: E402
from device_proxy.model import Connection  # noqa: E402

RNG = random.Random(2)
FLAP_EVERY = 30  # s between A's outages (the first after half of it)
FLAP_SECONDS = 8
RADIO_GAP = 0.05  # s between two telegrams in the air
CLIENTS = 10
SLOW_READERS = 2
SHORTER = {  # the fallback check's waiting times for this run
    "SUPERVISE": 0.2,
    "FALLBACK_PROBE": 2.0,
    "PROBE_TIMEOUT": 0.5,
    "RECONNECT_DELAYS": (0.5, 1, 2),
}
LIMITS = {
    "lost_pct": 5.0,  # telegrams a client did not get, of all sent while it was connected
    "failover_s": 3.0,  # A away → B stands in
    "failback_s": 15.0,  # A back → A takes over again (fallback_stable_s and a probe)
    "memory_mb": 20.0,
}
BASE_ANSWER = bytes.fromhex("A55A8B98FFB7448000000000009D")  # ESP2 base ID FF-B7-44-80
BASE_ID_READ = bytes.fromhex("A55AAB5800000000000000000003")


def esp2(header: int, org: int, data: bytes, sender: bytes, status: int = 0x30) -> bytes:
    body = bytes([header, org]) + data + sender + bytes([status])
    return b"\xa5\x5a" + body + bytes([sum(body) & 0xFF])


def telegram(n: int) -> bytes:
    """A 4BS telegram from a sensor, the counter in its data: each one is unique."""
    return esp2(0x0B, 0x07, n.to_bytes(4, "big"), bytes.fromhex("01802A3B"))


def command(n: int) -> bytes:
    """A client's TRT telegram sent over the air from the base ID range."""
    return esp2(0x6B, 0x07, n.to_bytes(4, "big"), bytes.fromhex("FFB74481"))


def rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return usage / (1 << 20) if sys.platform == "darwin" else usage / 1024  # peak


class Gateway:
    """A fake ESP2 gateway over TCP: answers base ID reads, passes the radio on while up."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.received = bytearray()
        self.writers: set[asyncio.StreamWriter] = set()
        self.server: asyncio.Server | None = None
        self.port = 0

    async def start(self) -> None:
        self.server = await asyncio.start_server(self._client, "127.0.0.1", self.port)
        self.port = self.server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        assert self.server is not None
        self.server.close()
        for writer in list(self.writers):
            writer.transport.abort()
        await self.server.wait_closed()
        self.server = None

    @property
    def up(self) -> bool:
        return self.server is not None

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.writers.add(writer)
        with contextlib.suppress(ConnectionError):
            while data := await reader.read(1024):
                self.received += data
                if BASE_ID_READ in data:
                    writer.write(BASE_ANSWER)
        self.writers.discard(writer)

    def hear(self, frame: bytes) -> None:
        for writer in list(self.writers):
            if not writer.is_closing():
                writer.write(frame)


async def radio(gateways: list[Gateway], stop: asyncio.Event, sent: list[float]) -> None:
    """The air: each telegram reaches every gateway that is up."""
    while not stop.is_set():
        frame = telegram(len(sent))
        sent.append(time.monotonic())
        for gateway in gateways:
            gateway.hear(frame)
        await asyncio.sleep(RADIO_GAP)


async def flapping(a: Gateway, proxy: EnOceanProxy, stop: asyncio.Event, times: dict) -> None:
    await asyncio.sleep(FLAP_EVERY / 2)
    while not stop.is_set():
        print(f"{time.strftime('%H:%M:%S')} A away for {FLAP_SECONDS} s", flush=True)
        await a.stop()
        gone = time.monotonic()
        while proxy.active != "fallback" and time.monotonic() - gone < FLAP_SECONDS:
            await asyncio.sleep(0.05)
        times["failover"].append(time.monotonic() - gone)
        await asyncio.sleep(max(0, FLAP_SECONDS - (time.monotonic() - gone)))
        await a.start()
        back = time.monotonic()
        while proxy.active != "main" and time.monotonic() - back < FLAP_EVERY - FLAP_SECONDS:
            await asyncio.sleep(0.05)
        times["failback"].append(time.monotonic() - back)
        await asyncio.sleep(max(0, FLAP_EVERY - FLAP_SECONDS - (time.monotonic() - back)))


async def client(port: int, stop: asyncio.Event, sent: list[float], result: dict, n: int) -> None:
    """Reads along the whole run and sends a command now and then."""
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    if n % 3 == 0:
        writer.write(REPLAY_REQUEST)  # what came before it: older counters, then the live ones
    first = len(sent)
    seen: set[int] = set()
    duplicates = commands = 0
    splitter = esp.Splitter("esp2")

    async def send() -> None:
        nonlocal commands
        while not stop.is_set():
            await asyncio.sleep(RNG.uniform(0.5, 3))
            writer.write(command(n * 1_000_000 + commands))
            commands += 1

    sender = asyncio.create_task(send())
    try:
        while not stop.is_set():
            try:
                data = await asyncio.wait_for(reader.read(4096), 0.5)
            except TimeoutError:
                continue
            if not data:
                break
            for frame in splitter.feed(data):
                if frame[3] != 0x07 or frame[8:12] != bytes.fromhex("01802A3B"):
                    continue  # not the sensor (answers of the gateway)
                counter = int.from_bytes(frame[4:8], "big")
                if counter in seen and counter >= first:
                    duplicates += 1
                seen.add(counter)
    finally:
        sender.cancel()
        writer.close()
    last = len(sent) - 1
    expected = set(range(first, last))
    result[n] = {
        "lost": len(expected - seen),
        "expected": len(expected),
        "duplicates": duplicates,
        "commands": commands,
    }


async def slow_reader(port: int, stop: asyncio.Event) -> None:
    """Never reads: must hold nobody up (dropped once 256 kB wait for it)."""
    _, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(REPLAY_REQUEST)
    await stop.wait()
    writer.transport.abort()


async def main(minutes: float) -> int:
    for name, value in SHORTER.items():
        setattr(enocean, name, value)
    enocean.BASE_ID_FILE = Path(tempfile.mkdtemp()) / "base_ids.json"
    a_gateway, b_gateway = Gateway("A"), Gateway("B")
    await a_gateway.start()
    await b_gateway.start()
    events: dict[str, int] = {}

    def on_event(level: str, kind: str, **params: object) -> None:
        events[kind] = events.get(kind, 0) + 1

    def proxy(gateway: Gateway, name: str, cid: str, **more: object) -> EnOceanProxy:
        c = Connection(
            name, "", 0, id=cid, kind="enocean", link="tcp", host="127.0.0.1",
            host_port=gateway.port, bind="127.0.0.1", max_clients=CLIENTS + SLOW_READERS + 2,
            send_gap_ms=0, **more,  # type: ignore[arg-type]
        )  # fmt: skip
        return EnOceanProxy(c, "all", on_event, lambda chunk: None)

    a = proxy(
        a_gateway, "A", "0000000a", fallback="0000000b", fallback_probe_s=1, fallback_stable_s=5
    )
    b = proxy(b_gateway, "B", "0000000b")
    b.serves = "A"
    a.attach_fallback(b)
    tasks = [asyncio.create_task(a.run()), asyncio.create_task(b.run())]
    while not (a.listening and a.base_id and b.base_id and a.fallback_ready):
        await asyncio.sleep(0.05)
    port = a.port
    await asyncio.sleep(0.5)
    base = (rss_mb(), len(asyncio.all_tasks()))
    print(f"start: {base[0]:.1f} MB, {base[1]} tasks; {minutes} min; shorter {SHORTER}")

    stop = asyncio.Event()
    sent: list[float] = []
    times: dict[str, list[float]] = {"failover": [], "failback": []}
    result: dict[int, dict[str, int]] = {}
    workers = [
        asyncio.create_task(radio([a_gateway, b_gateway], stop, sent)),
        asyncio.create_task(flapping(a_gateway, a, stop, times)),
    ]
    readers = [asyncio.create_task(client(port, stop, sent, result, n)) for n in range(CLIENTS)]
    readers += [asyncio.create_task(slow_reader(port, stop)) for _ in range(SLOW_READERS)]
    end = time.monotonic() + minutes * 60
    while time.monotonic() < end:
        await asyncio.sleep(min(30, max(0.1, end - time.monotonic())))
        s = a.stats
        print(
            f"{time.strftime('%H:%M:%S')} {rss_mb():.1f} MB · {len(asyncio.all_tasks())} tasks · "
            f"active {a.active} · clients {len(a.clients)} · telegrams {len(sent)} · "
            f"from gateway {s.from_gateway} to gateway {s.to_gateway} relayed {s.relayed} "
            f"from fallback {s.from_fallback} dropped {s.dropped}",
            flush=True,
        )
    stop.set()
    await asyncio.gather(*readers, return_exceptions=True)
    for worker in workers:
        worker.cancel()
    await asyncio.gather(*workers, return_exceptions=True)
    if not a_gateway.up:
        await a_gateway.start()
    await asyncio.sleep(2)  # the proxy notices the closed clients
    after = (rss_mb(), len(asyncio.all_tasks()))

    lost = max(100 * r["lost"] / max(1, r["expected"]) for r in result.values())
    measured = {
        "lost_pct": round(lost, 2),
        "failover_s": round(max(times["failover"], default=0.0), 2),
        "failback_s": round(max(times["failback"], default=0.0), 2),
        "memory_mb": round(after[0] - base[0], 1),
    }
    torn = [
        g.name
        for g in (a_gateway, b_gateway)
        if b"".join(esp.Splitter("esp2").feed(bytes(g.received))) != bytes(g.received)
    ]
    print(
        f"end: {after[0]:.1f} MB, {after[1]} tasks; clients left {len(a.clients)}; "
        f"{len(times['failover'])} outages; measured {measured}; {events}",
        flush=True,
    )
    problems = [f"{k} {measured[k]} > {v}" for k, v in LIMITS.items() if measured[k] > v]
    if any(r["duplicates"] for r in result.values()):
        problems.append(f"duplicates {[r['duplicates'] for r in result.values()]}")
    if len(result) != CLIENTS:
        problems.append(f"only {len(result)} of {CLIENTS} clients ran to the end")
    if torn:
        problems.append(f"torn or mixed frames at {torn}")
    if a.clients:
        problems.append("clients left")
    if after[1] > base[1] + 2:
        problems.append("tasks grew")
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    print("OK" if not problems else f"PROBLEMS: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(float(sys.argv[1]) if len(sys.argv) > 1 else 5)))
