"""1-Wire: an owserver (OWFS) shared with several programs, with a look at the bus.

The source is an owserver in the network (link "owserver": host and host_port), for example
the one that has the USB adapter today. Clients connect here instead, with the same
protocol: Home Assistant's onewire integration, owhttpd, pyownet scripts, other systems.

owserver already serves several clients itself; what the proxy adds is one place to see who
asks what, whether the bus answers and which devices are on it. Every client connection
gets a connection of its own to the owserver, and the bytes pass unchanged, so persistent
connections, the owserver's keepalive pings and every message type work as before. On the
way the proxy reads the message headers (24 bytes each, then the path): it counts requests,
errors and the time to the answer, writes the path to the trace, and answers a write of a
client that may not write (write_access, as for Modbus) itself with the owserver's error
-EACCES; that write never reaches the bus.

Most owserver clients (pyownet, which Home Assistant uses) open a connection for each
request. So a client here is a host, not a connection: it counts as connected from its first
request until IDLE_AFTER seconds without one, and max_clients limits the hosts.

The app reads the device list (DIRALL "/", from the owserver's cache) every PROBE_SECONDS:
that is the reachability check and the list of devices with their family.

With link "usb" the 1-Wire USB adapter (DS2490 inside the DS9490R and DS1490F) is on this
host, and the app runs its own owserver for it (OwServer): on 127.0.0.1 and a free port, so
only the proxy reaches it, and the proxy works as with an owserver in the network. owserver
takes the adapter from the kernel's ds2490 driver itself. The DS2490 is known to stop
answering after a while: WATCHDOG_MISSES device lists in a row without an answer start
owserver again, and after RESET_AFTER such restarts without an answer the adapter gets a USB
reset (as unplugging it does), at most once in RESET_PAUSE.
"""

from __future__ import annotations

import asyncio
import contextlib
import errno
import logging
import re
import socket
import struct
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from . import onewire_bus
from .clients import plain_host
from .devices import UsbDevice, reset_node, usb_devices
from .modbus import keepalive, may_write
from .model import Connection, from_this_host, peer_allowed
from .trace import Chunk

_LOGGER = logging.getLogger(__name__)

EventSink = Callable[..., None]  # (level, kind, **params)
TraceSink = Callable[[Chunk], None]

HEADER = struct.Struct(">iiiiii")  # version, payload, type or ret, flags, size, offset
SERVER_MESSAGE = 1 << 16  # version: a message from another owserver, with tokens after it
TOKEN_SIZE = 16
MAX_TOKENS = 64
MAX_REQUEST = 65536  # payload of a request: a path and the data to write
MAX_ANSWER = 1 << 20  # payload of an answer: a large directory
PING = -1  # payload of the owserver's "still working" message, which has no body
PERSISTENCE = 0x04  # flags: the connection stays open for the next request

MSG = {
    0: "error",
    1: "nop",
    2: "read",
    3: "write",
    4: "dir",
    5: "size",
    6: "presence",
    7: "dirall",
    8: "get",
    9: "dirallslash",
    10: "getslash",
}
MSG_READ, MSG_WRITE, MSG_DIR, MSG_DIRALL = 2, 3, 4, 7
DIRS = {"dir", "dirall", "dirallslash"}

CONNECT_TIMEOUT = 5.0  # seconds to reach the owserver
PROBE_SECONDS = 30.0  # between two reads of the device list
PROBE_TIMEOUT = 10.0
IDLE_AFTER = 300.0  # seconds without a request: the host is no longer a client
SWEEP = 10.0  # seconds between two looks for such hosts
LISTEN_RETRY = 10.0
CLOSE_TIMEOUT = 2.0
ANSWERS_KEPT = 100  # answer times the average is taken over
CONNECTIONS_PER_HOST = 32  # open connections of one host at a time; more are refused

OWSERVER = "owserver"
ADAPTER = ("04fa", "2490")  # vendor and product of the DS2490 (DS9490R, DS1490F)
OWSERVER_DELAYS = (1, 2, 5, 10, 30)  # seconds before starting an ended owserver again
OWSERVER_STABLE = 60.0  # a run this long resets the delay
OWSERVER_STOP = 5.0  # seconds owserver gets to end before it is killed
FIRST_PROBE = 10.0  # seconds the own owserver gets to take connections before the first look
WATCHDOG_MISSES = 2  # device lists in a row without an answer: owserver starts again
RESET_AFTER = 2  # such restarts without an answer since: the adapter gets a USB reset
RESET_PAUSE = 600.0  # at most one automatic USB reset in this many seconds
USB_BACK = 3.0  # seconds after a USB reset before owserver opens the adapter again
LOG_KEPT = 20  # owserver's last log lines in the state
STATISTICS_SECONDS = 60.0  # between two reads of the owserver's error counters
INFO_SECONDS = 600.0  # between two reads of the adapter's name and the owserver's version
# what the owserver says about its first adapter and itself; 2.x had /system/adapter/
INFO_PATHS = {
    "name": ("/bus.0/interface/settings/name", "/system/adapter/name.0"),
    "address": ("/bus.0/interface/settings/address", "/system/adapter/address.0"),
    "version": ("/bus.0/interface/settings/version", "/system/adapter/version.0"),
    "owserver": ("/system/configuration/version",),
}

DEVICE_ID = re.compile(r"[0-9A-F]{2}\.[0-9A-F]{12}")
# family code → the usual chip (the owserver tells the exact one in <id>/type)
FAMILIES = {
    "01": "DS1990A / DS2401",
    "02": "DS1991",
    "04": "DS1994",
    "06": "DS1993",
    "08": "DS1992",
    "0A": "DS1995",
    "0C": "DS1996",
    "05": "DS2405",
    "10": "DS18S20",
    "12": "DS2406",
    "1D": "DS2423",
    "20": "DS2450",
    "22": "DS1822",
    "26": "DS2438",
    "28": "DS18B20",
    "29": "DS2408",
    "3A": "DS2413",
    "3B": "DS1825",
    "42": "DS28EA00",
    "7E": "EDS00xx",
    "81": "DS1420",  # the ID chip inside the DS9490 and DS1490F USB adapters
    "EF": "HobbyBoards",
}


class ProtocolError(ValueError):
    """Bytes that are no owserver message: the connection is closed."""


@dataclass
class Stats:
    bytes_to_device: int = 0
    bytes_from_device: int = 0
    requests: dict[str, int] = field(
        default_factory=lambda: dict.fromkeys(("read", "write", "dir", "other"), 0)
    )
    errors: int = 0  # answers with a negative return value
    blocked: int = 0  # writes turned away (write_access)
    refused: int = 0  # connections turned away (networks, max_clients)
    last_error: str = ""
    last_error_at: float = 0.0


@dataclass
class Watchdog:
    misses: int = 0  # device lists in a row without an answer
    restarts: int = 0  # owserver started again since the bus last answered
    resets: int = 0  # USB resets since the start
    last_reset: float | None = None


@dataclass(eq=False)
class _Host:
    """One client: a host, with all its connections."""

    address: str  # the host ("192.168.1.20"); owserver clients connect again for each request
    host: str
    since: float
    last: float  # wall time of its last request
    active: float  # loop time of its last request, for IDLE_AFTER
    local: bool = False  # on this host (counts as 127.0.0.1 for write_access)
    writers: set[asyncio.StreamWriter] = field(default_factory=set)
    requests: int = 0
    errors: int = 0
    blocked: int = 0
    bytes_in: int = 0  # from the client
    bytes_out: int = 0  # to the client
    last_path: str = ""


def restart_key(c: Connection, listen: str) -> Connection:
    """What a running proxy depends on: a change of anything else does not restart it."""
    return replace(
        c,
        name="",
        trace="off",
        notify_missing=False,
        notify_no_client=False,
        silence_minutes=0,
        silence_restart="",
        power_switch="",
        template="generic",
        remaddr=f"{c.remaddr}|{listen}",
        # read for every client or request
        max_clients=1,
        timeout=0,
        write_access="all",
        write_clients="",
    )


def request(kind: int, path: str, flags: int = 0, size: int = 0) -> bytes:
    """A client's message: header and the path ending in NUL."""
    payload = path.encode() + b"\0"
    return HEADER.pack(0, len(payload), kind, flags, size, 0) + payload


def answer(ret: int, payload: bytes = b"", flags: int = 0) -> bytes:
    """An owserver's message: header and payload."""
    return HEADER.pack(0, len(payload), ret, flags, len(payload), 0) + payload


async def read_request(reader: asyncio.StreamReader) -> tuple[bytes, int, int, str]:
    """One client message: (all its bytes, type, flags, path); EOF before a header raises
    IncompleteReadError."""
    head = await reader.readexactly(HEADER.size)
    version, payload, kind, flags, _size, _offset = HEADER.unpack(head)
    tokens = version & 0xFFFF if version & SERVER_MESSAGE else 0
    if not 0 <= payload <= MAX_REQUEST or tokens > MAX_TOKENS:
        raise ProtocolError(f"not an owserver request (payload {payload})")
    body = await reader.readexactly(payload + tokens * TOKEN_SIZE)
    path = body[:payload].split(b"\0", 1)[0].decode("utf-8", "replace")
    return head + body, kind, flags, path


async def read_answer(reader: asyncio.StreamReader) -> tuple[bytes, int, int]:
    """One owserver message: (all its bytes, return value, payload length; PING for a
    keepalive)."""
    head = await reader.readexactly(HEADER.size)
    _version, payload, ret, _flags, _size, _offset = HEADER.unpack(head)
    if payload == PING:
        return head, ret, PING
    if not 0 <= payload <= MAX_ANSWER:
        raise ProtocolError(f"not an owserver answer (payload {payload})")
    return head + await reader.readexactly(payload), ret, payload


def parse_devices(payload: bytes) -> list[str]:
    """The device IDs in a DIRALL answer ("/28.A1B2C3D4E5F6,/bus.0,/settings,…")."""
    text = payload.split(b"\0", 1)[0].decode("ascii", "replace")
    found = []
    for entry in text.split(","):
        name = entry.strip().strip("/").rsplit("/", 1)[-1].upper()
        if DEVICE_ID.fullmatch(name) and name not in found:
            found.append(name)
    return found


def error_name(ret: int) -> str:
    return errno.errorcode.get(-ret, str(ret))


def free_port() -> int:
    """A port nothing listens on now, on 127.0.0.1 (for the own owserver)."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class OwServer:
    """The app's own owserver on the USB adapter: started again when it ends."""

    def __init__(
        self,
        port: int,
        on_exit: Callable[[int | None, float], None],
        binary: str = "",
        cache_s: int = 15,
    ) -> None:
        self.port = port
        self.cache_s = cache_s  # --timeout_volatile: a read value answered from the cache
        self.on_exit = on_exit  # (exit code, seconds until the next start)
        self.binary = binary or OWSERVER
        self.restarts = 0  # after it ended by itself
        self.starts = 0
        self.started_at: float | None = None
        self.last_exit: int | None = None
        self.start_error = ""
        self.log: deque[str] = deque(maxlen=LOG_KEPT)
        self._proc: asyncio.subprocess.Process | None = None
        self._again = False  # restart() asked for it: no delay, no event
        self._started = asyncio.Event()  # a new owserver process is there
        self._paused = False  # restart_with(): no new start until the adapter is reset
        self._resume = asyncio.Event()

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    def command(self) -> list[str]:
        # -u: the first USB adapter; errors to stderr (2), which the app logs
        return [
            self.binary, "--foreground", "--error_print=2", "--error_level=1",
            "-u", "-p", f"127.0.0.1:{self.port}", f"--timeout_volatile={self.cache_s}",
        ]  # fmt: skip

    async def run(self) -> None:
        failures = 0
        loop = asyncio.get_running_loop()
        try:
            while True:
                while self._paused:
                    self._resume.clear()
                    await self._resume.wait()
                started = loop.time()
                code = await self._run_once()
                if self._again:
                    self._again = False
                    continue
                if loop.time() - started >= OWSERVER_STABLE:
                    failures = 0
                delay = OWSERVER_DELAYS[min(failures, len(OWSERVER_DELAYS) - 1)]
                failures += 1
                self.restarts += 1
                self.on_exit(code, delay)
                await asyncio.sleep(delay)
        finally:
            # also when cancelled a second time while waiting: owserver must not stay
            await asyncio.shield(self.terminate())

    async def _run_once(self) -> int | None:
        try:
            self._proc = await asyncio.create_subprocess_exec(
                *self.command(),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except OSError as err:
            self.start_error = str(err)
            self.last_exit = None
            return None
        self.start_error, self.started_at = "", time.time()
        self.starts += 1
        self._started.set()
        assert self._proc.stdout is not None
        while True:
            try:
                raw = await self._proc.stdout.readline()
            except ValueError:  # a line over 64 KiB
                continue
            if not raw:
                break
            if line := raw.decode(errors="replace").strip():
                self.log.append(line)
                _LOGGER.info("owserver: %s", line)
        self.last_exit = await self._proc.wait()
        return self.last_exit

    async def restart(self) -> None:
        """End owserver; run() starts it again at once (waited for, up to OWSERVER_STOP)."""
        if not self.running:
            return
        self._again = True
        self._started.clear()
        await self.terminate()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._started.wait(), OWSERVER_STOP)

    async def restart_with(self, between: Callable[[], None]) -> None:
        """End owserver, run between (in a thread), start it again after USB_BACK."""
        running = self.running
        self._again = running
        self._started.clear()
        self._paused = True
        await self.terminate()
        try:
            await asyncio.to_thread(between)
        finally:
            await asyncio.sleep(USB_BACK)  # the adapter comes back on the bus
            self._paused = False
            self._resume.set()
        if running:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self._started.wait(), OWSERVER_STOP)

    async def terminate(self) -> None:
        proc = self._proc
        if proc is None or proc.returncode is not None:
            return
        with contextlib.suppress(ProcessLookupError):
            proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), OWSERVER_STOP)
        except TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            await proc.wait()

    def state(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "port": self.port,
            "started_at": self.started_at if self.running else None,
            "restarts": self.restarts,
            "last_exit": self.last_exit,
            "start_error": self.start_error,
            "log": list(self.log),
        }


class OneWireProxy:
    def __init__(
        self,
        c: Connection,
        listen: str,
        on_event: EventSink,
        on_trace: TraceSink,
    ) -> None:
        self.c = c
        self.listen = listen
        self.key = restart_key(c, listen)
        self.on_event = on_event
        self.on_trace = on_trace
        self.stats = Stats()
        self.clients: dict[str, _Host] = {}
        self.only: str | None = None
        self.refuse: Callable[[str, str], bool] = lambda _host, _name: False
        self.listening = False
        self.listen_error = ""
        self.reachable: bool | None = None
        self.reachable_since = time.time()
        self.devices: list[str] = []
        self.devices_at: float | None = None
        self.bus = onewire_bus.Bus(c.id)  # known, missing and new devices, values, counters
        self.info: dict[str, str] = {}  # INFO_PATHS: the adapter's name, address, version
        self._info_at = -INFO_SECONDS
        self.probe_ms: float | None = None
        self.port = c.port  # the port listened on (tests: the one the system picked for 0)
        self._answers: deque[float] = deque(maxlen=ANSWERS_KEPT)  # ms
        self._last_answer_ms: float | None = None
        self._server: asyncio.Server | None = None
        self._open = 0  # client connections now
        # link "usb": the own owserver, the adapters found, the watchdog's counts
        self.owserver = (
            OwServer(free_port(), self._owserver_ended, cache_s=c.owserver_cache_s)
            if c.onewire_usb
            else None
        )
        self.adapters: list[UsbDevice] = []
        self.find_adapters: Callable[[], list[UsbDevice]] = lambda: usb_devices(*ADAPTER)
        self.reset_adapter: Callable[[str], None] = lambda node: reset_node(Path(node))
        self.watchdog = Watchdog()
        self._reset_at = -RESET_PAUSE  # loop time of the last automatic USB reset

    # running

    async def run(self) -> None:
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
                asyncio.create_task(self._probe_loop()),
                asyncio.create_task(self._sweep_loop()),
                asyncio.create_task(self._statistics_loop()),
            ]
            if self.owserver is not None:
                tasks.append(asyncio.create_task(self.owserver.run()))
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
        sockets = sorted(self._server.sockets, key=lambda s: s.family != socket.AF_INET)
        self.port = int(sockets[0].getsockname()[1])
        self.listening, self.listen_error = True, ""

    async def _shutdown(self) -> None:
        self.listening = False
        if self._server is not None:
            self._server.close()
        for client in self.clients.values():
            for writer in list(client.writers):
                writer.transport.abort()
        if self._server is not None:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self._server.wait_closed(), CLOSE_TIMEOUT)

    # the owserver

    async def _connect(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if self.owserver is not None:
            host, port = "127.0.0.1", self.owserver.port
        else:
            host, port = self.c.host, self.c.host_port
        try:
            return await asyncio.wait_for(asyncio.open_connection(host, port), CONNECT_TIMEOUT)
        except TimeoutError:
            raise ConnectionError("no answer") from None

    def _emit(self, events: list[onewire_bus.Event]) -> None:
        for level, kind, values in events:
            self.on_event(level, kind, **values)

    async def ask(self, kind: int, path: str, size: int = 0) -> tuple[int, bytes]:
        """One request of the app itself: (return value, payload)."""
        writer = None
        try:
            async with asyncio.timeout(PROBE_TIMEOUT):
                reader, writer = await self._connect()
                writer.write(request(kind, path, size=size))
                await writer.drain()
                while True:
                    data, ret, payload = await read_answer(reader)
                    if payload != PING:
                        return ret, data[HEADER.size :]
        finally:
            if writer is not None:
                writer.close()

    async def read_info(self) -> None:
        """Name, address and version of the owserver's first adapter, and its own version;
        what it does not have stays out."""
        info: dict[str, str] = {}
        for key, paths in INFO_PATHS.items():
            for path in paths:
                try:
                    ret, payload = await self.ask(MSG_READ, path, 512)
                except (OSError, TimeoutError, asyncio.IncompleteReadError, ProtocolError):
                    return
                text = payload.split(b"\0", 1)[0].decode("utf-8", "replace").strip()
                if ret >= 0 and text and text.isprintable():
                    info[key] = text[:128]
                    break
        self.info = info

    async def read_statistics(self) -> None:
        """The owserver's error counters (CRC, bus); left out when it has none."""
        values: dict[str, int] = {}
        for name in onewire_bus.STATISTICS:
            try:
                ret, payload = await self.ask(MSG_READ, f"/statistics/errors/{name}", 32)
            except (OSError, TimeoutError, asyncio.IncompleteReadError, ProtocolError):
                return
            if ret < 0:
                continue
            text = payload.split(b"\0", 1)[0].strip()
            if text.isdigit():
                values[name] = int(text)
        if values:
            self.bus.counted(values)

    async def _statistics_loop(self) -> None:
        if self.owserver is not None:
            await self._owserver_ready()
        while True:
            if not self.reachable:  # the first device list may not be there yet
                await asyncio.sleep(5)
                continue
            await self.read_statistics()
            await asyncio.sleep(STATISTICS_SECONDS)

    def forget(self, device_id: str) -> bool:
        return self.bus.forget(device_id)

    async def _owserver_ready(self) -> None:
        """Wait until the own owserver takes connections, up to FIRST_PROBE: no "not
        reachable" while it starts."""
        deadline = asyncio.get_running_loop().time() + FIRST_PROBE
        while asyncio.get_running_loop().time() < deadline:
            try:
                _reader, writer = await self._connect()
            except OSError:
                await asyncio.sleep(0.2)
                continue
            writer.close()
            return

    async def _probe_loop(self) -> None:
        if self.owserver is not None:
            await self._owserver_ready()
        while True:
            await self.probe()
            await self.look_after()
            await asyncio.sleep(PROBE_SECONDS)

    async def probe(self) -> None:
        """Read the device list: is the owserver there, and what is on the bus."""
        loop = asyncio.get_running_loop()
        started = loop.time()
        writer = None
        try:
            async with asyncio.timeout(PROBE_TIMEOUT):
                reader, writer = await self._connect()
                writer.write(request(MSG_DIRALL, "/"))
                await writer.drain()
                while True:
                    _data, ret, payload = await read_answer(reader)
                    if payload != PING:
                        break
                body = _data[HEADER.size :]
        except (OSError, TimeoutError, asyncio.IncompleteReadError, ProtocolError) as err:
            self._down(_text(err))
            return
        finally:
            if writer is not None:
                writer.close()
        if ret < 0:
            self._down(f"device list: {error_name(ret)}")
            return
        self.probe_ms = round((loop.time() - started) * 1000, 1)
        self.devices, self.devices_at = parse_devices(body), time.time()
        self._up()
        self._emit(self.bus.listed(self.devices))
        for device_id in self.bus.needs_type():  # the exact chip, once per device
            try:
                answered, chip = await self.ask(MSG_READ, f"/{device_id}/type", 32)
            except (OSError, TimeoutError, asyncio.IncompleteReadError, ProtocolError):
                break  # next time
            self.bus.typed(device_id, answered, chip)
        for device_id in self.bus.needs_power():  # once per sensor and run, as it is listed
            try:
                answered, supply = await self.ask(MSG_READ, f"/{device_id}/power", 8)
            except (OSError, TimeoutError, asyncio.IncompleteReadError, ProtocolError):
                break  # next time
            self.bus.powered(device_id, answered, supply)
        if loop.time() - self._info_at >= INFO_SECONDS:
            self._info_at = loop.time()
            await self.read_info()

    # the own owserver (link "usb")

    def _owserver_ended(self, code: int | None, delay: float) -> None:
        assert self.owserver is not None
        error = self.owserver.start_error or (self.owserver.log[-1] if self.owserver.log else "")
        self.on_event("warning", "onewire_owserver_ended", code=code, delay=delay, error=error)

    async def look_after(self) -> None:
        """The watchdog, after each look at the device list: owserver again, then a USB
        reset, when the bus keeps not answering."""
        if self.owserver is None:
            return
        self.adapters = await asyncio.to_thread(self.find_adapters)
        w = self.watchdog
        if self.reachable is not False:
            w.misses = w.restarts = 0
            return
        w.misses += 1
        if w.misses < WATCHDOG_MISSES:
            return
        w.misses = 0
        loop = asyncio.get_running_loop()
        if (
            w.restarts >= RESET_AFTER
            and self.adapters
            and loop.time() - self._reset_at >= RESET_PAUSE
        ):
            self._reset_at = loop.time()
            w.restarts = 0
            with contextlib.suppress(OSError, ValueError):  # said by usb_reset's event
                await self.usb_reset(reason="watchdog")
            return
        w.restarts += 1
        if self.owserver.running:  # one that ended is started again by OwServer anyway
            self.on_event("warning", "onewire_restarted", reason="no answer")
            await self.owserver.restart()

    async def usb_reset(self, reason: str = "manual") -> str:
        """End owserver, reset the adapter, let owserver open it again; the adapter's place.
        Raises ValueError without an adapter, OSError when the reset fails."""
        if self.owserver is None:
            raise ValueError("the bus is not on a USB adapter of this host")
        self.adapters = await asyncio.to_thread(self.find_adapters)
        if not self.adapters:
            raise ValueError("no 1-Wire USB adapter found")
        adapter = self.adapters[0]
        owserver = self.owserver
        try:
            # owserver lets the adapter go; reset; owserver opens it again (run() starts it)
            await owserver.restart_with(lambda: self.reset_adapter(adapter.node))
        except OSError as err:
            self.on_event("error", "onewire_usb_reset_failed", place=adapter.place, error=str(err))
            raise
        self.watchdog.resets += 1
        self.watchdog.last_reset = time.time()
        self.on_event("warning", "onewire_usb_reset", place=adapter.place, reason=reason)
        return adapter.place

    def _up(self) -> None:
        if self.reachable is not True:
            if self.reachable is False:
                self.on_event("info", "onewire_back", target=self.c.upstream)
            self.reachable, self.reachable_since = True, time.time()

    def _down(self, error: str) -> None:
        self.stats.last_error, self.stats.last_error_at = error, time.time()
        if self.reachable is not False:
            self.reachable, self.reachable_since = False, time.time()
            self.on_event("warning", "onewire_down", target=self.c.upstream, error=error)

    # clients

    async def _sweep_loop(self) -> None:
        while True:
            await asyncio.sleep(SWEEP)
            self.sweep()

    def sweep(self) -> None:
        """Hosts without a request for IDLE_AFTER and no open connection are gone."""
        now = asyncio.get_running_loop().time()
        for key, client in list(self.clients.items()):
            if not client.writers and now - client.active >= IDLE_AFTER:
                del self.clients[key]
                self.on_event(
                    "info",
                    "client_disconnected",
                    address=client.address,
                    bytes_to_client=client.bytes_out,
                    bytes_from_client=client.bytes_in,
                )

    def _allowed(self, writer: asyncio.StreamWriter) -> tuple[str, bool] | None:
        """(host, on this host) of a new connection, or None when it is turned away."""
        peer = writer.get_extra_info("peername") or ("?", 0)
        host = plain_host(str(peer[0]))
        if self.refuse(host, self.c.name):
            self.on_event("info", "client_refused_blocked", address=host)
            return None
        sock = writer.get_extra_info("sockname")
        if not peer_allowed(self.c.remaddr, self.listen, peer, sock):
            self.stats.refused += 1
            self.on_event("warning", "client_refused_network", address=host)
            return None
        if self.only and host != self.only:
            self.on_event("info", "client_refused_exclusive", address=host, only=self.only)
            return None
        return host, from_this_host(peer, sock)

    def _client_for(self, host: str, local: bool) -> _Host | None:
        """The client of a host that sent its first request; None: one too many."""
        client = self.clients.get(host)
        if client is not None:
            if len(client.writers) >= CONNECTIONS_PER_HOST:
                self.stats.refused += 1
                return None
            return client
        if len(self.clients) >= self.c.max_clients:
            self.stats.refused += 1
            self.on_event("warning", "client_refused", address=host)
            return None
        now = time.time()
        client = _Host(host, host, now, now, asyncio.get_running_loop().time(), local)
        self.clients[host] = client
        self.on_event("info", "client_connected", address=host)
        return client

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        allowed = self._allowed(writer)
        if allowed is None:
            writer.close()
            return
        keepalive(writer.get_extra_info("socket"))
        self._open += 1
        client: _Host | None = None
        upstream: asyncio.StreamWriter | None = None
        pumps: list[asyncio.Task[None]] = []
        try:
            try:
                first = await asyncio.wait_for(read_request(reader), self.c.timeout or None)
            except (asyncio.IncompleteReadError, TimeoutError, OSError, ProtocolError):
                return  # connected and asked nothing (a port check): no client
            client = self._client_for(*allowed)
            if client is None:
                return
            client.writers.add(writer)
            try:
                up_reader, upstream = await self._connect()
            except OSError as err:  # ConnectionError too
                self._down(_text(err))
                return
            waiting: deque[tuple[float, str, str]] = deque()  # (loop time, type, path)
            pumps = [
                asyncio.create_task(
                    self._requests(client, reader, writer, upstream, waiting, first)
                ),
                asyncio.create_task(self._answers_to(client, up_reader, writer, waiting)),
            ]
            await asyncio.wait(pumps, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for pump in pumps:
                pump.cancel()
            await asyncio.gather(*pumps, return_exceptions=True)
            if upstream is not None:
                upstream.close()
            writer.close()
            if client is not None:
                client.writers.discard(writer)
                client.active = asyncio.get_running_loop().time()
            self._open -= 1

    async def _requests(
        self,
        client: _Host,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        upstream: asyncio.StreamWriter,
        waiting: deque[tuple[float, str, str]],
        message: tuple[bytes, int, int, str],
    ) -> None:
        loop = asyncio.get_running_loop()
        with contextlib.suppress(asyncio.IncompleteReadError, OSError, ProtocolError, TimeoutError):
            while True:
                data, kind, _flags, path = message
                name = MSG.get(kind, f"type {kind}")
                client.requests += 1
                client.bytes_in += len(data)
                client.last, client.active, client.last_path = time.time(), loop.time(), path
                bucket = "dir" if name in DIRS else name if name in ("read", "write") else "other"
                self.stats.requests[bucket] += 1
                self._trace("tx", data, f"{name} {path} · {client.address}")
                if kind == MSG_WRITE and not may_write(self.c, client.host, client.local):
                    client.blocked += 1
                    self.stats.blocked += 1
                    self.on_event(
                        "warning", "onewire_write_blocked", address=client.address, path=path
                    )
                    refusal = answer(-errno.EACCES)
                    writer.write(refusal)  # no persistence: the client connects again
                    client.bytes_out += len(refusal)
                    self._trace("rx", refusal, f"EACCES {path} · {client.address}")
                    await writer.drain()
                    return
                upstream.write(data)
                self.stats.bytes_to_device += len(data)
                waiting.append((loop.time(), name, path))
                await upstream.drain()
                message = await asyncio.wait_for(read_request(reader), self.c.timeout or None)

    async def _answers_to(
        self,
        client: _Host,
        up_reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        waiting: deque[tuple[float, str, str]],
    ) -> None:
        loop = asyncio.get_running_loop()
        with contextlib.suppress(asyncio.IncompleteReadError, OSError, ProtocolError):
            while True:
                data, ret, payload = await read_answer(up_reader)
                writer.write(data)
                client.bytes_out += len(data)
                self.stats.bytes_from_device += len(data)
                if payload == PING:
                    await writer.drain()
                    continue
                self._up()
                sent, name, path = waiting[0] if waiting else (loop.time(), "?", "")
                if ret < 0:
                    client.errors += 1
                    self.stats.errors += 1
                    self.stats.last_error = f"{error_name(ret)} {path}"
                    self.stats.last_error_at = time.time()
                # a directory comes as one message per entry and an empty one at the end
                if waiting and (name != "dir" or payload == 0 or ret < 0):
                    waiting.popleft()
                    ms = round((loop.time() - sent) * 1000, 1)
                    self._answers.append(ms)
                    self._last_answer_ms = ms
                if name in ("read", "get"):
                    error = error_name(ret) if ret < 0 else ""
                    self._emit(self.bus.answered(path, ret, data[HEADER.size :], error))
                self._trace("rx", data, f"{_said(name, path, ret, data)} · {client.address}")
                await writer.drain()

    def _trace(self, direction: str, data: bytes, info: str) -> None:
        self.on_trace(Chunk(time.time(), direction, data, info=info))

    def disconnect_clients(self, keep: str | None = None) -> int:
        """Close the open connections (the programs connect again)."""
        count = 0
        for client in self.clients.values():
            if client.host == keep:
                continue
            for writer in list(client.writers):
                writer.close()
                count += 1
        return count

    def disconnect_host(self, host: str) -> int:
        client = self.clients.get(host)
        if client is None:
            return 0
        writers = list(client.writers)
        for writer in writers:
            writer.close()
        return len(writers)

    def state(self) -> dict[str, Any]:
        s = self.stats
        answers = list(self._answers)
        return {
            "source": self.c.link,
            "owserver": self.owserver.state() if self.owserver is not None else None,
            "adapters": [
                {"place": a.place, "product": a.product, "driver": a.driver} for a in self.adapters
            ],
            "watchdog": asdict(self.watchdog) if self.owserver is not None else None,
            "listening": self.listening,
            "listen_error": self.listen_error,
            "reachable": self.reachable,
            "reachable_since": self.reachable_since,
            "target": self.c.upstream,
            "last_error": s.last_error,
            "last_error_at": s.last_error_at or None,
            # also the known ones that are missing now, first
            "devices": [
                {**row, "type": row["chip"] or FAMILIES.get(row["family"], "")}
                for row in self.bus.rows()
            ],
            "present": len(self.devices),
            "missing": self.bus.missing(),
            "statistics": self.bus.statistics_state(),
            "info": dict(self.info),
            "devices_at": self.devices_at,
            "probe_ms": self.probe_ms,
            "requests": dict(s.requests),
            "errors": s.errors,
            "blocked": s.blocked,
            "refused": s.refused,
            "answer_ms": {
                "last": self._last_answer_ms,
                "avg": round(sum(answers) / len(answers), 1) if answers else None,
            },
            "connections": self._open,
        }


# what the app shows of a 1-Wire connection (kinds.py)


def loaded(c: Connection) -> dict[str, Any]:
    """The values of the "onewire_loaded" event at start."""
    return {"target": c.upstream, "port": c.port, "max_clients": c.max_clients}


def client_row(client: _Host) -> dict[str, Any]:
    return {
        "address": client.address,
        "since": client.since,
        "bytes_to_client": client.bytes_out,
        "bytes_from_client": client.bytes_in,
        "requests": client.requests,
        "errors": client.errors,
        "blocked": client.blocked,
        "last_request": client.last,
        "last_path": client.last_path,
        "connections": len(client.writers),
        "queued": 0,
        "stuck": False,
    }


def mqtt_entities(
    prefix: str, c: Connection, entity: Callable[..., dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    key = f"device_proxy_{c.id}"
    return {
        f"{prefix}/binary_sensor/{key}/reachable/config": entity(
            "reachable",
            value_template="{{ 'ON' if value_json.reachable else 'OFF' }}",
            device_class="connectivity",
        ),
        f"{prefix}/sensor/{key}/onewire_devices/config": entity(
            "onewire_devices",
            value_template="{{ value_json.onewire_devices }}",
            state_class="measurement",
            icon="mdi:thermometer-lines",
        ),
        f"{prefix}/sensor/{key}/onewire_missing/config": entity(
            "onewire_missing",
            value_template="{{ value_json.onewire_missing }}",
            state_class="measurement",
            icon="mdi:thermometer-off",
        ),
        f"{prefix}/sensor/{key}/requests/config": entity(
            "requests",
            value_template="{{ value_json.requests }}",
            state_class="total_increasing",
            icon="mdi:swap-vertical",
            entity_category="diagnostic",
        ),
    }


def mqtt_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "reachable": state["reachable"] is True,
        "onewire_devices": state["present"],
        "onewire_missing": len(state["missing"]),
        "requests": sum(state["requests"].values()),
    }


def _said(name: str, path: str, ret: int, data: bytes) -> str:
    """An answer for the trace: the error, or for a read the value ("21.5")."""
    if ret < 0:
        return f"{error_name(ret)} {path}"
    value = data[HEADER.size :].split(b"\0", 1)[0]
    if name in ("read", "get") and 0 < len(value) <= 40 and value.isascii():
        text = value.decode().strip()
        if text.isprintable():
            return f"{name} {path} = {text}"
    return f"{name} {path}"


def _text(err: BaseException) -> str:
    if isinstance(err, TimeoutError):
        return "no answer"
    if isinstance(err, asyncio.IncompleteReadError):
        return "connection closed"
    return str(err) or type(err).__name__
