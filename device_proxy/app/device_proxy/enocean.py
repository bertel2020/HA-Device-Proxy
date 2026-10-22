"""EnOcean proxy: one EnOcean gateway (ESP2 or ESP3) shared by several TCP clients.

Taken over from the EnOcean Proxy app (HA-Enocean-Proxy 0.6.2); its clients (the
enocean_eltako integration, eo_man, PCT14 over the network ...) see the same behaviour.

Every telegram from the gateway goes to every client. Frames from clients are queued and
written one at a time with a short gap (send_gap_ms), so two programs never interleave on
the line. The gateway's answer to a command goes back to the client that sent it (ESP3
answers every packet in order; ESP2 answers gateway commands); unsolicited messages go to
everyone, FAM14 bus traffic (ESP2 ORG >= 0xF0) too. Frames a client sends are not echoed to
the other clients. For a client that only knows ser2net, the proxy is just another raw TCP
gateway.

Replay (used by the enocean_eltako integration): a client that sends the line
"EOPX REPLAY" first gets the radio telegrams that arrived while no replaying client was
connected, e.g. during a Home Assistant restart, in their original order. Only radio
telegrams are kept (no FAM14 polling), at most replay_size and none older than
replay_max_age_s. With "EOPX REPLAY TS" the replay comes as a text block with the
reception time of each telegram ("EOPX TS <n>", n lines "<unix time> <hex>", "EOPX END"),
then the binary stream continues.

With replay_persist the buffer is written to /data when the app stops and read again at the
next start, so telegrams received while Home Assistant restarts survive an app restart too.

A client that stops reading is disconnected before its unsent data grows without bound.
While a capture reserves the gateway for one program (exclusive_peer, PCT14 with a FAM14),
the frames of the others are held back.

Fallback: a second gateway (B) with the same base ID can stand in for this one (A). B is an
EnOcean connection of its own that the controller attaches here; while it serves A it has no
port and no clients (serves). A reads its base ID every MAIN_PROBE seconds; when its
connection is gone, or (fallback_trigger "probe") FALLBACK_MISSES reads stay unanswered, A's
clients go on through B: their frames are queued at B, B's answers and radio telegrams come
back to them. A goes back once it has run steadily for FALLBACK_STABLE seconds and nothing
waits at B (fallback_return "auto"), or by hand. B is only used when it is connected, has
answered lately and reports A's base ID (the actuators know A's sender IDs). With
fallback_listen the clients get the radio telegrams of both gateways: the second copy of a
telegram within DUPLICATE_WINDOW is dropped, and so is what the passive gateway hears from
the own sender IDs (base ID … +127: the other gateway's own sending).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import socket
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from . import esp
from .modbus import Link, SerialLink, TcpLink
from .model import Connection, client_allowed
from .trace import Chunk

_LOGGER = logging.getLogger(__name__)

REPLAY_REQUEST = b"EOPX REPLAY\n"
REPLAY_REQUEST_TS = b"EOPX REPLAY TS\n"
CONTROL_PREFIX = b"EOPX"
CONTROL_LINE_MAX = 64
DUTY_CYCLE_LIMIT = 0.01  # 868 MHz band: 1 % of the time
DUTY_WINDOW = 3600.0  # seconds the duty cycle is measured over
DUTY_WARN = 0.8  # warn at 80 % of the limit
RECONNECT_DELAYS = (1, 2, 5, 10, 30)  # seconds between attempts to reach the gateway
LISTEN_RETRY = 10  # seconds between attempts to open the port
OPEN_TIMEOUT = 10.0  # seconds for connecting to a network gateway
RESPONSE_TIMEOUT = 2.0  # seconds a client waits for the gateway's answer
BASE_ID_WRITE_TIMEOUT = 5.0  # the gateway writes its flash first
CLIENT_BUFFER_LIMIT = 256 * 1024  # bytes not yet delivered to a client before it is dropped
CLIENT_QUEUE_MAX = 32  # frames of one client waiting for the gateway: then it is not read
CLOSE_TIMEOUT = 2.0  # seconds to wait for the clients when stopping
REPLAY_DIR = Path("/data/replay")  # the kept replay buffers, one file per connection id
BASE_ID_FILE = Path("/data/enocean_base_ids.json")  # last base ID of each gateway, for B's check
SUPERVISE = 1.0  # seconds between two looks at the fallback
MAIN_PROBE = 10.0  # seconds between base ID reads of a gateway that has a fallback
FALLBACK_PROBE = 60.0  # seconds between base ID reads of a fallback gateway
FALLBACK_MISSES = 3  # unanswered reads in a row: the gateway counts as failed
FALLBACK_STABLE = 60.0  # seconds a failed gateway must run steadily before it takes over again
DUPLICATE_WINDOW = 0.2  # seconds: the same telegram from the other gateway is a duplicate
PROBE_TIMEOUT = 2.0  # seconds for the answer to a base ID read of the fallback check

EventSink = Callable[..., None]  # (level, kind, **params)
TraceSink = Callable[[Chunk], None]


@dataclass
class Stats:
    from_gateway: int = 0  # frames
    to_gateway: int = 0
    dropped: int = 0  # client frames while the gateway was not connected
    replayed: int = 0
    refused: int = 0  # clients outside the allowed networks
    slow_clients: int = 0  # clients disconnected because they stopped reading
    locked: int = 0  # client frames held back while another program had the gateway alone
    relayed: int = 0  # client frames sent through the fallback gateway
    from_fallback: int = 0  # frames from the fallback gateway passed to the clients
    bytes_to_device: int = 0
    bytes_from_device: int = 0
    last_error: str = ""
    last_error_at: float = 0.0


@dataclass(eq=False)
class _Client:
    address: str  # "192.168.1.20:50114"
    host: str
    since: float
    writer: asyncio.StreamWriter | None  # None: the app itself (tools)
    splitter: esp.Splitter
    inbox: asyncio.Queue[bytes] | None = None  # the app's own requests get answers here
    sink: Callable[[bytes], None] | None = None  # a frame relayed for another gateway's client
    own: bool = False  # the app asks this very gateway (base ID reads, tools): never relayed
    replay: bool = False
    pending: bytearray = field(default_factory=bytearray)
    started: bool = False  # the replay request is only accepted as the very first bytes
    bytes_in: int = 0
    bytes_out: int = 0
    queued: int = 0  # frames waiting in the outgoing queue


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
        # read for every client or frame: no restart needed
        max_clients=1,
        kickolduser=False,
        timeout=0,
        send_gap_ms=0,
        replay_max_age_s=0,
        replay_persist=False,
        # the fallback gateway is attached by the controller, its settings read live
        fallback="",
        fallback_trigger="probe",
        fallback_return="auto",
        fallback_listen=False,
    )


class EnOceanProxy:
    def __init__(
        self,
        c: Connection,
        listen: str,
        on_event: EventSink,
        on_trace: TraceSink,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.c = c
        self.listen = listen
        self.key = restart_key(c, listen)
        self.on_event = on_event
        self.on_trace = on_trace
        self.protocol = c.esp_protocol
        self.link: Link = (
            SerialLink(c.device, c.baud, 8, "n", 1)
            if c.uses_device
            else TcpLink(c.host, c.host_port)
        )
        self.stats = Stats()
        self.clients: dict[str, _Client] = {}
        self.listening = False
        self.listen_error = ""
        self.reachable: bool | None = None
        self.reachable_since = time.time()
        self.connected_since: float | None = None
        self.base_id: str | None = None  # learnt from the gateway's answers
        self.base_id_writes_left: int | None = None  # ESP3 tells it with the base ID
        self.ask_base_id = True  # read it once per connection (tests switch it off)
        self.exclusive_peer: str | None = None  # only this host may send (PCT14 capture)
        # (direction, frame, client address) of every frame, e.g. for a capture
        self.observers: list[Callable[[str, bytes, str], None]] = []
        self._clock = clock
        self._outgoing: asyncio.Queue[tuple[_Client, bytes]] = asyncio.Queue()
        self._awaiting: deque[tuple[_Client, float, bytes]] = deque()  # who gets the answer
        self._replay: deque[tuple[float, float, bytes]] = deque(maxlen=c.replay_size)
        self._airtime: deque[tuple[float, float]] = deque()  # (time, ms) of sent telegrams
        self._duty_warned = 0.0
        self._server: asyncio.Server | None = None
        self.port = c.port  # the port listened on (tests: the one the system picked for 0)
        # fallback (see the module's text); B: serves is the name of the gateway it stands in for
        self.serves = ""
        self.listeners: list[Callable[[bytes], None]] = []  # B: A gets B's frames here
        self.fallback: EnOceanProxy | None = None  # A: B, attached by the controller
        self.fallback_label = ""  # A: B's name, also while B is switched off
        self.active = "main"  # A: "main" or "fallback", whose gateway the clients use
        self.active_since = time.time()
        self.switch_reason = ""
        self.manual = False  # switched by hand: no automatic return
        self.fallback_ready = False
        self.fallback_reason = "none"  # why B is not ready
        self.answered_at: float | None = None  # last base ID answer (clock)
        self.probe_ms: float | None = None  # how long the last base ID read took
        self.known_base_id = _known_base_ids().get(c.id)  # also while the gateway is away
        self.heard = {"main": 0, "fallback": 0, "duplicates": 0, "own": 0}
        self._misses = 0
        self._ok_since: float | None = None  # clock: running steadily since
        self._probed = 0.0
        self._recent: deque[tuple[float, bytes, str]] = deque()  # (clock, telegram, source)
        if c.replay_persist:
            self._load_replay()

    # running

    async def run(self) -> None:
        """Listen for clients and keep the gateway's connection; until cancelled."""
        failed = False
        tasks: list[asyncio.Task[None]] = []
        try:
            while self._server is None and not self.serves:
                try:
                    await self._start_server()
                except OSError as err:
                    self.listen_error = str(err)
                    if not failed:
                        failed = True
                        self.on_event("error", "listen_failed", port=self.c.port, error=str(err))
                    await asyncio.sleep(LISTEN_RETRY)
            tasks = [
                asyncio.create_task(self._gateway_loop()),
                asyncio.create_task(self._writer_loop()),
                asyncio.create_task(self._fallback_loop()),
            ]
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self._shutdown()

    async def _start_server(self) -> None:
        host = self.c.bind or ("127.0.0.1" if self.listen == "local" else None)
        self._server = await asyncio.start_server(
            self._client, host, self.c.port, reuse_address=True
        )
        self.port = _port(self._server)
        self.listening, self.listen_error = True, ""

    async def _shutdown(self) -> None:
        self.attach_fallback(None)
        self.listening = False
        if self._server is not None:
            self._server.close()
        for client in list(self.clients.values()):  # first: wait_closed waits for clients
            if client.writer is not None:
                client.writer.transport.abort()  # a client that does not read: no waiting
        if self._server is not None:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self._server.wait_closed(), CLOSE_TIMEOUT)
        await self.link.close()
        self._save_replay()

    # gateway side

    async def _gateway_loop(self) -> None:
        attempt = 0
        loop = asyncio.get_running_loop()
        while True:
            try:
                await self.link.open(OPEN_TIMEOUT)
            except Exception as err:  # also a bad host name or a termios error
                self._down(_text(err))
                delay = RECONNECT_DELAYS[min(attempt, len(RECONNECT_DELAYS) - 1)]
                attempt += 1
                await asyncio.sleep(delay)
                continue
            attempt = 0
            self._up()
            splitter = esp.Splitter(self.protocol)
            ask = asyncio.create_task(self._ask_base_id()) if self.ask_base_id else None
            try:
                while True:
                    try:
                        data = await self.link.read_some(loop.time() + 3600)
                    except TimeoutError:
                        continue  # a quiet hour
                    self.stats.bytes_from_device += len(data)
                    for frame in splitter.feed(data):
                        try:
                            self._from_gateway(frame)
                        except Exception:  # a bug must not stop the gateway
                            _LOGGER.exception("%s: frame from the gateway failed", self.c.name)
            except ConnectionError as err:
                self._down(str(err) or "connection lost")
            finally:
                if ask:
                    ask.cancel()
                await self.link.close()
                self.connected_since = None
                self._awaiting.clear()
            await asyncio.sleep(RECONNECT_DELAYS[0])

    async def _ask_base_id(self) -> None:
        """Read the base ID once per connection (harmless, nothing goes over the air), so it
        shows without anyone asking; _learn picks it from the answer."""
        with contextlib.suppress(ConnectionError, ValueError):
            await self.request(esp.base_id_request(self.protocol))

    def _up(self) -> None:
        self.connected_since = time.time()
        self._misses, self._probed = 0, 0.0  # the first check right away
        self._ok_since = self._clock() if self.c.fallback_trigger == "disconnect" else None
        if self.reachable is not True:
            if self.reachable is False:
                self.on_event("info", "enocean_back", target=self.c.upstream)
            self.reachable, self.reachable_since = True, time.time()

    def _down(self, error: str) -> None:
        self.stats.last_error, self.stats.last_error_at = error, time.time()
        self._ok_since = None
        if self.reachable is not False:
            self.reachable, self.reachable_since = False, time.time()
            self.on_event("warning", "enocean_down", target=self.c.upstream, error=error)

    def _trace(self, direction: str, frame: bytes, address: str = "") -> None:
        info = esp.describe(self.protocol, frame)
        if address:
            info = f"{info} · {address}" if info else address
        self.on_trace(Chunk(time.time(), direction, frame, info=info))
        for observer in list(self.observers):
            try:
                observer(direction, frame, address)
            except Exception:  # e.g. the disk of a capture is full: the capture ends
                _LOGGER.exception("%s: observer failed and is removed", self.c.name)
                with contextlib.suppress(ValueError):
                    self.observers.remove(observer)

    def _from_gateway(self, frame: bytes) -> None:
        self.stats.from_gateway += 1
        self._trace("rx", frame)
        if esp.is_response(self.protocol, frame) and (waiting := self._next_waiting()):
            client, request = waiting
            self._learn(frame, request)
            self._send(client, frame)  # the answer to this client's command
            return
        self._learn(frame, None)
        for listener in list(self.listeners):  # B: the gateway it stands in for
            listener(frame)
        if not self.serves:
            self._heard_frame(frame, "main")

    def _deliver(self, frame: bytes) -> None:
        if esp.is_radio(self.protocol, frame) and not any(c.replay for c in self.clients.values()):
            self._replay.append((self._clock(), time.time(), frame))  # nobody to replay to yet
        for client in list(self.clients.values()):
            self._send(client, frame)

    def _learn(self, frame: bytes, request: bytes | None) -> None:
        if found := esp.base_id(self.protocol, frame, request):
            self.base_id = found
            self.base_id_writes_left = esp.base_id_writes_left(self.protocol, frame, request)
            self.answered_at = self._clock()
            if found != self.known_base_id:
                self.known_base_id = found
                _keep_base_id(self.c.id, found)

    def _next_waiting(self) -> tuple[_Client, bytes] | None:
        now = self._clock()
        while self._awaiting:
            client, deadline, request = self._awaiting.popleft()
            alive = (
                client.inbox is not None
                or client.sink is not None
                or self.clients.get(client.address) is client
            )
            if deadline >= now and alive:
                return client, request
        return None

    async def _writer_loop(self) -> None:
        while True:
            client, frame = await self._outgoing.get()
            client.queued -= 1
            if self.exclusive_peer is not None and client.host != self.exclusive_peer:
                self.stats.locked += 1  # another program has the gateway alone (PCT14)
                continue
            if self.active == "fallback" and not client.own and self.fallback is not None:
                self._relay(self.fallback, client, frame)
                continue
            if not self.link.is_open:
                self.stats.dropped += 1
                continue
            if esp.expects_response(self.protocol, frame):
                self._awaiting.append((client, self._clock() + RESPONSE_TIMEOUT, frame))
            try:
                await self.link.write(frame)
            except (OSError, ConnectionError) as err:
                self.stats.dropped += 1
                self.stats.last_error, self.stats.last_error_at = _text(err), time.time()
                continue
            self.stats.to_gateway += 1
            self.stats.bytes_to_device += len(frame)
            try:
                self._trace("tx", frame, client.address)
                self._count_airtime(frame)
            except Exception:  # a bug must not stop the sending
                _LOGGER.exception("%s: frame to the gateway failed", self.c.name)
            await asyncio.sleep(self.c.send_gap_ms / 1000)

    # client side

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername") or ("?", 0)
        host = str(peer[0])
        address = f"[{host}]:{peer[1]}" if ":" in host else f"{host}:{peer[1]}"
        if not client_allowed(self.c.remaddr, self.listen, host):
            self.stats.refused += 1
            _LOGGER.info("%s: client %s refused (not an allowed network)", self.c.name, address)
            writer.close()
            return
        if len(self.clients) >= self.c.max_clients:
            if not self.c.kickolduser:
                self.on_event("warning", "client_refused", address=address)
                writer.close()
                return
            oldest = min(self.clients.values(), key=lambda cl: cl.since)
            if oldest.writer is not None:
                oldest.writer.transport.abort()
            self.clients.pop(oldest.address, None)
        client = _Client(address, host, time.time(), writer, esp.Splitter(self.protocol))
        self.clients[address] = client
        self.on_event("info", "client_connected", address=address)
        idle = self.c.timeout or None
        try:
            while chunk := await asyncio.wait_for(reader.read(1024), idle):
                client.bytes_in += len(chunk)
                self._from_client(client, chunk)
                while client.queued >= CLIENT_QUEUE_MAX:  # the gateway is slower: wait
                    await asyncio.sleep(self.c.send_gap_ms / 1000 or 0.05)
        except (OSError, TimeoutError):
            pass
        finally:
            if self.clients.get(address) is client:
                self.clients.pop(address)
            writer.close()
            self.on_event("info", "client_disconnected", address=address)

    def _send(self, client: _Client, frame: bytes) -> None:
        """Write to a client; one that has stopped reading is dropped, not buffered forever."""
        if client.inbox is not None:
            client.inbox.put_nowait(frame)
            return
        if client.sink is not None:
            client.sink(frame)
            return
        if client.writer is None or client.writer.is_closing():
            return
        client.writer.write(frame)
        client.bytes_out += len(frame)
        transport = client.writer.transport
        if (queued := transport.get_write_buffer_size()) > CLIENT_BUFFER_LIMIT:
            self.stats.slow_clients += 1
            self.on_event("warning", "client_dropped", address=client.address, queued=queued)
            if self.clients.get(client.address) is client:
                self.clients.pop(client.address)
            transport.abort()

    def _from_client(self, client: _Client, chunk: bytes) -> None:
        client.pending += chunk
        if not client.started:
            head = bytes(client.pending[: len(CONTROL_PREFIX)])
            if CONTROL_PREFIX.startswith(head) and len(head) < len(CONTROL_PREFIX):
                return  # a control line may still be coming
            client.started = True
            if head == CONTROL_PREFIX:
                end = client.pending.find(b"\n")
                if end < 0 and len(client.pending) < CONTROL_LINE_MAX:
                    client.started = False
                    return
                line = bytes(client.pending[: end + 1]) if end >= 0 else b""
                del client.pending[: end + 1 if end >= 0 else len(client.pending)]
                if line in (REPLAY_REQUEST, REPLAY_REQUEST_TS):
                    self._start_replay(client, timestamps=line == REPLAY_REQUEST_TS)
        data, client.pending = bytes(client.pending), bytearray()
        for frame in client.splitter.feed(data):
            client.queued += 1
            self._outgoing.put_nowait((client, frame))

    def _start_replay(self, client: _Client, *, timestamps: bool = False) -> None:
        oldest = self._clock() - self.c.replay_max_age_s
        kept = [(wall, frame) for received, wall, frame in self._replay if received >= oldest]
        self._replay.clear()
        client.replay = True
        if timestamps:
            lines = [f"EOPX TS {len(kept)}\n".encode()]
            lines += [f"{wall:.3f} {frame.hex()}\n".encode() for wall, frame in kept]
            self._send(client, b"".join(lines) + b"EOPX END\n")
        else:
            for _wall, frame in kept:
                self._send(client, frame)
        self.stats.replayed += len(kept)
        _LOGGER.info("%s: replayed %d telegrams to %s", self.c.name, len(kept), client.address)

    def _replay_file(self) -> Path:
        return REPLAY_DIR / f"{self.c.id}.json"

    def _load_replay(self) -> None:
        """The buffer kept at the last stop, without what has grown too old meanwhile."""
        path = self._replay_file()
        try:
            frames = json.loads(path.read_text(encoding="utf-8"))["frames"]
            path.unlink()
        except FileNotFoundError:
            return
        except (OSError, ValueError, KeyError, TypeError) as err:
            _LOGGER.warning("%s: kept replay buffer not read: %s", self.c.name, err)
            return
        now, wall_now = self._clock(), time.time()
        for wall, text in frames:
            age = wall_now - float(wall)
            if 0 <= age <= self.c.replay_max_age_s:
                self._replay.append((now - age, float(wall), bytes.fromhex(text)))
        _LOGGER.info("%s: %d kept telegrams for the replay", self.c.name, len(self._replay))

    def _save_replay(self) -> None:
        path = self._replay_file()
        try:
            if not self.c.replay_persist or not self._replay:
                path.unlink(missing_ok=True)
                return
            REPLAY_DIR.mkdir(parents=True, exist_ok=True)
            frames = [[wall, frame.hex()] for _received, wall, frame in self._replay]
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"frames": frames}), encoding="utf-8")
            os.replace(tmp, path)
        except OSError as err:
            _LOGGER.warning("%s: replay buffer not kept: %s", self.c.name, err)

    # fallback

    def attach_fallback(self, fallback: EnOceanProxy | None) -> None:
        """A: the gateway that stands in (None: none). B's frames come in from now on."""
        if fallback is self.fallback:
            return
        if self.fallback is not None:
            with contextlib.suppress(ValueError):
                self.fallback.listeners.remove(self._from_fallback)
        self.fallback = fallback
        if fallback is not None:
            fallback.listeners.append(self._from_fallback)

    def _relay(self, fallback: EnOceanProxy, client: _Client, frame: bytes) -> None:
        """A: send a client's frame through B; B's answer goes back to the client."""
        self.stats.relayed += 1
        self._trace("tx", frame, f"{client.address} → {fallback.c.name}")

        def answer(reply: bytes) -> None:
            self._trace("rx", reply, f"{fallback.c.name} → {client.address}")
            self._send(client, reply)

        fallback.relay(client, frame, answer)

    def relay(self, origin: _Client, frame: bytes, deliver: Callable[[bytes], None]) -> None:
        """B: a frame of the gateway it stands in for, queued in turn; its answer to deliver."""
        address = f"{origin.address} ({self.serves})" if self.serves else origin.address
        client = _Client(
            address, origin.host, time.time(), None, esp.Splitter(self.protocol), sink=deliver
        )
        client.queued += 1
        self._outgoing.put_nowait((client, frame))

    def _from_fallback(self, frame: bytes) -> None:
        """A: a frame from B that is not an answer for one of A's clients."""
        self._heard_frame(frame, "fallback")

    def _heard_frame(self, frame: bytes, source: str) -> None:
        """A frame from one of the two gateways: to the clients if it comes from the active
        one, or with fallback_listen a radio telegram the other did not bring already."""
        active = source == self.active
        radio = esp.is_radio(self.protocol, frame)
        if self.fallback is not None and radio:
            if not active and not self.c.fallback_listen:
                return
            if not active and self._own_sender(frame):
                self.heard["own"] += 1  # the active gateway's own sending
                return
            if self.c.fallback_listen and (key := esp.radio_key(self.protocol, frame)):
                if self._duplicate(key, source):
                    self.heard["duplicates"] += 1
                    return
                self.heard[source] += 1
        elif not active:
            return  # answers and gateway messages count from the active gateway only
        if source == "fallback":
            self.stats.from_fallback += 1
            if self.fallback is not None:
                self._trace("rx", frame, f"via {self.fallback.c.name}")
        self._deliver(frame)

    def _own_sender(self, frame: bytes) -> bool:
        base = self.base_id or self.known_base_id
        info = esp.radio_info(self.protocol, frame)
        if base is None or info is None:
            return False
        first = int(base.replace("-", ""), 16)
        return first <= int(info[1].replace("-", ""), 16) <= first + 0x7F

    def _duplicate(self, key: bytes, source: str) -> bool:
        now = self._clock()
        while self._recent and now - self._recent[0][0] > DUPLICATE_WINDOW:
            self._recent.popleft()
        if any(k == key and s != source for _t, k, s in self._recent):
            return True
        self._recent.append((now, key, source))
        return False

    async def _fallback_loop(self) -> None:
        """Read the base ID now and then (A with a fallback, and B) and switch over or back."""
        while True:
            await asyncio.sleep(SUPERVISE)
            try:
                await self._probe()
                self._supervise()
            except Exception:  # a bug must not stop the gateway
                _LOGGER.exception("%s: fallback check failed", self.c.name)

    async def _probe(self) -> None:
        interval = FALLBACK_PROBE if self.serves else MAIN_PROBE if self.c.fallback else 0
        now = self._clock()
        if not interval or not self.link.is_open or now - self._probed < interval:
            return
        self._probed = now
        started = time.perf_counter()
        try:
            answer = await self.request(esp.base_id_request(self.protocol), PROBE_TIMEOUT)
        except (ConnectionError, ValueError):
            return
        if answer is None:
            self._misses += 1
            self._ok_since = None if self.c.fallback_trigger == "probe" else self._ok_since
            return
        self.probe_ms = round((time.perf_counter() - started) * 1000, 1)
        self._misses = 0
        if self._ok_since is None:
            self._ok_since = self._clock()

    def fallback_state(self) -> tuple[bool, str]:
        """A: can B stand in right now, and if not, why."""
        fallback = self.fallback
        if fallback is None:
            return False, "none" if not self.c.fallback else "off"
        if not fallback.link.is_open:
            return False, "not_connected"
        if fallback.base_id is None:
            return False, "base_id_unknown"
        mine = self.base_id or self.known_base_id
        if mine is None:
            return False, "own_base_id_unknown"
        if fallback.base_id != mine:
            return False, "base_id_differs"
        answered = fallback.answered_at
        if answered is None or self._clock() - answered > FALLBACK_PROBE * FALLBACK_MISSES:
            return False, "silent"
        return True, "ok"

    def _failed(self) -> str:
        """A: why its own gateway counts as failed ("" while it works)."""
        if not self.link.is_open:
            return "disconnected"
        if self.c.fallback_trigger == "probe" and self._misses >= FALLBACK_MISSES:
            return "no_answer"
        return ""

    def _supervise(self) -> None:
        if self.serves:
            return
        ready, reason = self.fallback_state()
        if self.c.fallback and (ready, reason) != (self.fallback_ready, self.fallback_reason):
            if ready:
                self.on_event("info", "enocean_fallback_ready", fallback=self._fallback_name())
            elif reason not in ("none", "off") or self.fallback_ready:
                self.on_event(
                    "warning",
                    "enocean_fallback_unready",
                    fallback=self._fallback_name(),
                    reason=reason,
                )
        self.fallback_ready, self.fallback_reason = ready, reason
        if self.active == "main":
            if (failed := self._failed()) and ready:
                self._switch("fallback", failed)
            return
        fallback = self.fallback
        if fallback is None or not fallback.link.is_open:
            self._switch("main", "fallback_lost")
        elif (
            self.c.fallback_return == "auto"
            and not self.manual
            and not self._failed()
            and self._ok_since is not None
            and self._clock() - self._ok_since >= FALLBACK_STABLE
            and fallback._outgoing.empty()
        ):
            self._switch("main", "main_back")

    def switch(self, to: str) -> None:
        """By hand: "fallback" or "main"; stays until switched back by hand or B fails."""
        if to == "fallback":
            ready, reason = self.fallback_state()
            if not ready:
                raise ValueError(f"the fallback is not ready: {reason}")
        elif to != "main":
            raise ValueError("main or fallback")
        elif not self.link.is_open:
            raise ValueError("the gateway is not connected")
        self._switch(to, "by_hand")
        self.manual = to == "fallback"

    def _switch(self, to: str, reason: str) -> None:
        if to == self.active:
            return
        name = self._fallback_name()
        self.active, self.active_since, self.switch_reason = to, time.time(), reason
        self.manual = False
        if to == "fallback":
            waiting = [entry for entry in self._awaiting if not entry[0].own]
            for entry in waiting:  # A will not answer them any more
                self._awaiting.remove(entry)
            _LOGGER.warning("%s: goes on through the fallback %s (%s)", self.c.name, name, reason)
            self.on_event(
                "warning", "enocean_failover", fallback=name, reason=reason, unanswered=len(waiting)
            )
        else:
            _LOGGER.info("%s: back on its own gateway (%s)", self.c.name, reason)
            self.on_event("info", "enocean_failback", fallback=name, reason=reason)

    def _fallback_name(self) -> str:
        if self.fallback is not None:
            return self.fallback.c.name
        return self.fallback_label or self.c.fallback

    def fallback_info(self) -> dict[str, Any] | None:
        """A's fallback for the state: None without one."""
        if not self.c.fallback:
            return None
        fallback = self.fallback
        return {
            "id": self.c.fallback,
            "name": self._fallback_name(),
            "main": self.c.name,
            "active": self.active,
            "active_since": self.active_since,
            "reason": self.switch_reason,
            "manual": self.manual,
            "ready": self.fallback_ready,
            "not_ready": None if self.fallback_ready else self.fallback_reason,
            "connected": bool(fallback and fallback.link.is_open),
            "base_id": fallback.base_id if fallback is not None else None,
            "probe_ms": fallback.probe_ms if fallback is not None else None,
            "relayed": self.stats.relayed,
            "from_fallback": self.stats.from_fallback,
            "listen": self.c.fallback_listen,
            "heard": dict(self.heard),
        }

    # duty cycle

    def _count_airtime(self, frame: bytes) -> None:
        if (ms := esp.airtime_ms(self.protocol, frame)) <= 0:
            return
        now = time.time()
        self._airtime.append((now, ms))
        duty = self.duty_cycle()
        if duty["of_limit"] >= DUTY_WARN * 100 and now - self._duty_warned > DUTY_WINDOW:
            self._duty_warned = now
            self.on_event("warning", "duty_cycle_high", of_limit=duty["of_limit"])

    def duty_cycle(self) -> dict[str, float]:
        """Air time of the telegrams sent in the last hour: ms, % of the hour, % of the limit."""
        now = time.time()
        while self._airtime and now - self._airtime[0][0] > DUTY_WINDOW:
            self._airtime.popleft()
        used = sum(ms for _time, ms in self._airtime)
        share = used / (DUTY_WINDOW * 1000)
        return {
            "ms": round(used, 1),
            "percent": round(share * 100, 3),
            "of_limit": round(share / DUTY_CYCLE_LIMIT * 100, 1),
            "telegrams": len(self._airtime),
        }

    # the app's own requests (tools)

    async def request(self, frame: bytes, timeout: float = RESPONSE_TIMEOUT) -> bytes | None:
        """Send one frame as the app itself, in turn with the clients; the gateway's answer,
        or None."""
        if esp.Splitter(self.protocol).feed(frame) != [frame]:
            raise ValueError("not exactly one complete frame")
        if not self.link.is_open:
            raise ConnectionError("gateway not connected")
        inbox: asyncio.Queue[bytes] = asyncio.Queue()
        splitter = esp.Splitter(self.protocol)
        local = _Client("app", "app", time.time(), None, splitter, inbox, own=True)
        local.queued += 1
        self._outgoing.put_nowait((local, frame))
        if not esp.expects_response(self.protocol, frame):
            return None
        try:
            async with asyncio.timeout(timeout):
                return await inbox.get()
        except TimeoutError:
            return None

    async def gateway_test(self, count: int = 20) -> dict[str, Any]:
        """Read the base ID count times: how fast and how reliably the gateway answers.
        Harmless: nothing is sent over the air. Waits for each answer before the next."""
        times: list[float] = []
        lost = 0
        for _ in range(count):
            started = time.perf_counter()
            if await self.request(esp.base_id_request(self.protocol)) is None:
                lost += 1
            else:
                times.append((time.perf_counter() - started) * 1000)
        return {
            "sent": count,
            "answered": len(times),
            "lost": lost,
            "avg_ms": round(sum(times) / len(times), 1) if times else None,
            "max_ms": round(max(times), 1) if times else None,
        }

    async def set_base_id(self, raw: bytes) -> str:
        """Change the base ID, then read it back; what the gateway said ("ok", ...)."""
        answer = await self.request(
            esp.base_id_write_request(self.protocol, raw), BASE_ID_WRITE_TIMEOUT
        )
        result = esp.base_id_write_result(self.protocol, answer)
        await self.request(esp.base_id_request(self.protocol))  # _learn takes the new one
        return result

    # state

    def state(self) -> dict[str, Any]:
        s = self.stats
        now = self._clock()
        ages = [now - received for received, _wall, _frame in self._replay]
        return {
            "protocol": self.protocol,
            "listening": self.listening,
            "listen_error": self.listen_error,
            "reachable": self.reachable,
            "reachable_since": self.reachable_since,
            "connected": self.link.is_open,
            "connected_since": self.connected_since,
            "base_id": self.base_id or self.known_base_id,
            "base_id_live": self.base_id is not None,
            "base_id_writes_left": self.base_id_writes_left,
            "probe_ms": self.probe_ms,
            "serves": self.serves or None,
            "fallback": self.fallback_info(),
            "last_error": s.last_error,
            "last_error_at": s.last_error_at or None,
            "frames": {
                "from_gateway": s.from_gateway,
                "to_gateway": s.to_gateway,
                "dropped": s.dropped,
                "replayed": s.replayed,
                "refused": s.refused,
                "slow_clients": s.slow_clients,
                "locked": s.locked,
            },
            "queue": self._outgoing.qsize(),
            "replay": {
                "kept": len(self._replay),
                "size": self._replay.maxlen,
                "oldest_s": round(max(ages), 1) if ages else None,
                "max_age_s": self.c.replay_max_age_s,
            },
            "exclusive_peer": self.exclusive_peer,
            "duty_cycle": self.duty_cycle(),
        }


# what the app shows of an EnOcean connection (kinds.py)


def loaded(c: Connection) -> dict[str, Any]:
    """The values of the "enocean_loaded" event at start."""
    return {
        "protocol": c.esp_protocol.upper(),
        "target": c.upstream,
        "port": c.port,
        "max_clients": c.max_clients,
    }


def client_row(client: _Client) -> dict[str, Any]:
    transport = client.writer.transport if client.writer is not None else None
    return {
        "address": client.address,
        "since": client.since,
        "bytes_to_client": client.bytes_out,
        "bytes_from_client": client.bytes_in,
        "replay": client.replay,
        "queued": transport.get_write_buffer_size() if transport is not None else 0,
        "stuck": False,
    }


def mqtt_entities(
    prefix: str, c: Connection, entity: Callable[..., dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    key = f"device_proxy_{c.id}"
    result = {
        f"{prefix}/binary_sensor/{key}/reachable/config": entity(
            "reachable",
            value_template="{{ 'ON' if value_json.reachable else 'OFF' }}",
            device_class="connectivity",
        ),
        f"{prefix}/sensor/{key}/telegrams/config": entity(
            "telegrams",
            value_template="{{ value_json.telegrams }}",
            state_class="total_increasing",
            icon="mdi:radio-tower",
        ),
        f"{prefix}/sensor/{key}/duty_cycle/config": entity(
            "duty_cycle",
            value_template="{{ value_json.duty_cycle }}",
            unit_of_measurement="%",
            state_class="measurement",
            icon="mdi:timer-sand",
            entity_category="diagnostic",
        ),
    }
    if c.fallback:  # "reachable" stays this gateway's own hardware
        result |= {
            f"{prefix}/binary_sensor/{key}/fallback_active/config": entity(
                "fallback_active",
                value_template="{{ 'ON' if value_json.fallback_active else 'OFF' }}",
                device_class="problem",
            ),
            f"{prefix}/sensor/{key}/active_gateway/config": entity(
                "active_gateway",
                value_template="{{ value_json.active_gateway }}",
                icon="mdi:swap-horizontal",
            ),
            f"{prefix}/binary_sensor/{key}/fallback_ready/config": entity(
                "fallback_ready",
                value_template="{{ 'ON' if value_json.fallback_ready else 'OFF' }}",
                entity_category="diagnostic",
            ),
        }
    return result


def mqtt_state(state: dict[str, Any]) -> dict[str, Any]:
    """The entities' values from the proxy's state(); duty cycle in % of the 1 % limit."""
    values = {
        "reachable": state["reachable"] is True,
        "telegrams": state["frames"]["from_gateway"],
        "duty_cycle": state["duty_cycle"]["of_limit"],
    }
    if fallback := state.get("fallback"):
        active = fallback["active"] == "fallback"
        values |= {
            "fallback_active": active,
            "active_gateway": (fallback["name"] or "?") if active else fallback["main"],
            "fallback_ready": fallback["ready"],
        }
    return values


def _known_base_ids() -> dict[str, str]:
    try:
        data = json.loads(BASE_ID_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def _keep_base_id(connection_id: str, base_id: str) -> None:
    """Remember a gateway's base ID, so its fallback can be checked while it is away."""
    known = _known_base_ids() | {connection_id: base_id}
    try:
        BASE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = BASE_ID_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(known), encoding="utf-8")
        os.replace(tmp, BASE_ID_FILE)
    except OSError as err:
        _LOGGER.debug("base ID not kept: %s", err)


def _port(server: asyncio.Server) -> int:
    """The port listened on; with port 0 (tests) IPv4 and IPv6 may get different ones."""
    sockets = sorted(server.sockets, key=lambda s: s.family != socket.AF_INET)
    return int(sockets[0].getsockname()[1])


def _text(err: BaseException) -> str:
    if isinstance(err, TimeoutError):
        return "no answer"
    return str(err) or type(err).__name__
