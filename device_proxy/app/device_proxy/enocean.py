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

A client that stops reading is disconnected before its unsent data grows without bound.
While a capture reserves the gateway for one program (exclusive_peer, PCT14 with a FAM14),
the frames of the others are held back.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field, replace
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
CLIENT_BUFFER_LIMIT = 256 * 1024  # bytes not yet delivered to a client before it is dropped

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
    replay: bool = False
    pending: bytearray = field(default_factory=bytearray)
    started: bool = False  # the replay request is only accepted as the very first bytes
    bytes_in: int = 0
    bytes_out: int = 0


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
        self.exclusive_peer: str | None = None  # only this host may send (PCT14 capture)
        self._clock = clock
        self._outgoing: asyncio.Queue[tuple[_Client, bytes]] = asyncio.Queue()
        self._awaiting: deque[tuple[_Client, float, bytes]] = deque()  # who gets the answer
        self._replay: deque[tuple[float, float, bytes]] = deque(maxlen=c.replay_size)
        self._airtime: deque[tuple[float, float]] = deque()  # (time, ms) of sent telegrams
        self._duty_warned = 0.0
        self._server: asyncio.Server | None = None
        self.port = c.port  # the port listened on (tests: the one the system picked for 0)

    # running

    async def run(self) -> None:
        """Listen for clients and keep the gateway's connection; until cancelled."""
        failed = False
        tasks: list[asyncio.Task[None]] = []
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
            tasks = [
                asyncio.create_task(self._gateway_loop()),
                asyncio.create_task(self._writer_loop()),
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
        self.port = self._server.sockets[0].getsockname()[1]
        self.listening, self.listen_error = True, ""

    async def _shutdown(self) -> None:
        self.listening = False
        if self._server is not None:
            self._server.close()
        for client in list(self.clients.values()):  # first: wait_closed waits for clients
            if client.writer is not None:
                client.writer.close()
        if self._server is not None:
            with contextlib.suppress(Exception):
                await self._server.wait_closed()
        await self.link.close()

    # gateway side

    async def _gateway_loop(self) -> None:
        attempt = 0
        loop = asyncio.get_running_loop()
        while True:
            try:
                await self.link.open(OPEN_TIMEOUT)
            except (OSError, TimeoutError) as err:
                self._down(_text(err))
                delay = RECONNECT_DELAYS[min(attempt, len(RECONNECT_DELAYS) - 1)]
                attempt += 1
                await asyncio.sleep(delay)
                continue
            attempt = 0
            self._up()
            splitter = esp.Splitter(self.protocol)
            try:
                while True:
                    try:
                        data = await self.link.read_some(loop.time() + 3600)
                    except TimeoutError:
                        continue  # a quiet hour
                    self.stats.bytes_from_device += len(data)
                    for frame in splitter.feed(data):
                        self._from_gateway(frame)
            except ConnectionError as err:
                self._down(str(err) or "connection lost")
            finally:
                await self.link.close()
                self.connected_since = None
                self._awaiting.clear()
            await asyncio.sleep(RECONNECT_DELAYS[0])

    def _up(self) -> None:
        self.connected_since = time.time()
        if self.reachable is not True:
            if self.reachable is False:
                self.on_event("info", "enocean_back", target=self.c.upstream)
            self.reachable, self.reachable_since = True, time.time()

    def _down(self, error: str) -> None:
        self.stats.last_error, self.stats.last_error_at = error, time.time()
        if self.reachable is not False:
            self.reachable, self.reachable_since = False, time.time()
            self.on_event("warning", "enocean_down", target=self.c.upstream, error=error)

    def _trace(self, direction: str, frame: bytes, address: str = "") -> None:
        info = esp.describe(self.protocol, frame)
        if address:
            info = f"{info} · {address}" if info else address
        self.on_trace(Chunk(time.time(), direction, frame, info=info))

    def _from_gateway(self, frame: bytes) -> None:
        self.stats.from_gateway += 1
        self._trace("rx", frame)
        if esp.is_response(self.protocol, frame) and (waiting := self._next_waiting()):
            client, request = waiting
            self._learn(frame, request)
            self._send(client, frame)  # the answer to this client's command
            return
        self._learn(frame, None)
        if esp.is_radio(self.protocol, frame) and not any(c.replay for c in self.clients.values()):
            self._replay.append((self._clock(), time.time(), frame))  # nobody to replay to yet
        for client in list(self.clients.values()):
            self._send(client, frame)

    def _learn(self, frame: bytes, request: bytes | None) -> None:
        if found := esp.base_id(self.protocol, frame, request):
            self.base_id = found

    def _next_waiting(self) -> tuple[_Client, bytes] | None:
        now = self._clock()
        while self._awaiting:
            client, deadline, request = self._awaiting.popleft()
            alive = client.inbox is not None or self.clients.get(client.address) is client
            if deadline >= now and alive:
                return client, request
        return None

    async def _writer_loop(self) -> None:
        while True:
            client, frame = await self._outgoing.get()
            if not self.link.is_open:
                self.stats.dropped += 1
                continue
            if self.exclusive_peer is not None and client.host != self.exclusive_peer:
                self.stats.locked += 1  # another program has the gateway alone (PCT14)
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
            self._trace("tx", frame, client.address)
            self._count_airtime(frame)
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
                oldest.writer.close()
            self.clients.pop(oldest.address, None)
        client = _Client(address, host, time.time(), writer, esp.Splitter(self.protocol))
        self.clients[address] = client
        self.on_event("info", "client_connected", address=address)
        idle = self.c.timeout or None
        try:
            while chunk := await asyncio.wait_for(reader.read(1024), idle):
                client.bytes_in += len(chunk)
                self._from_client(client, chunk)
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
        local = _Client("app", "app", time.time(), None, esp.Splitter(self.protocol), inbox)
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
            "base_id": self.base_id,
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
    prefix: str, connection_id: str, entity: Callable[..., dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    key = f"device_proxy_{connection_id}"
    return {
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


def mqtt_state(state: dict[str, Any]) -> dict[str, Any]:
    """The entities' values from the proxy's state(); duty cycle in % of the 1 % limit."""
    return {
        "reachable": state["reachable"] is True,
        "telegrams": state["frames"]["from_gateway"],
        "duty_cycle": state["duty_cycle"]["of_limit"],
    }


def _text(err: BaseException) -> str:
    if isinstance(err, TimeoutError):
        return "no answer"
    return str(err) or type(err).__name__
