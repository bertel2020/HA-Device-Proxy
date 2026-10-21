"""Ties the app together: configuration, ser2net, its admin socket, devices and events.

Saving a configuration writes ser2net.yaml and makes ser2net reload it. ser2net keeps a
changed connection as it was while clients are connected; those clients (and only those of
the changed connections) are disconnected so the change takes effect, the others stay.

ser2net slows all clients of a connection down when one of them stops reading; a client
whose queue stays full is reported (and its connection's clients disconnected, if set).
ser2net opens a device only while a client is connected; "keep open" makes the app one.

With the settings' source "custom" the user's own ser2net.yaml is used instead of the forms;
the form connections stay saved but unused (no device checks, no keep open).

Modbus connections are not ser2net's: each runs a ModbusProxy (modbus.py) in the app,
whatever the source. Saving restarts only the proxies whose settings changed.
"""

from __future__ import annotations

import asyncio
import contextlib
import errno
import logging
import os
import socket
import struct
import time
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from . import custom
from .addresses import addresses, host_lan_ip
from .admin import AdminClient, AdminError, PortStatus
from .config import blocks, changed, readable_alias, render
from .detect import detect
from .devices import Device, device_for, line_counters, scan, set_low_latency
from .events import EventLog
from .ha_mqtt import HaBridge
from .importer import ImportResult, ReadError, conflicts, merge, read
from .meter import analyze
from .modbus import EXC_PATH, EXC_TARGET, ModbusProxy, read_result, restart_key
from .model import AppConfig, Connection, ValidationError, new_id
from .notify import Notifier
from .process import Ser2Net
from .store import Change, Store, summary
from .trace import Chunk, TraceHub

_LOGGER = logging.getLogger(__name__)

DEVICE_POLL = 2  # seconds between device checks
STATUS_POLL = 5  # seconds between status reads from ser2net
HOUSEKEEPING = 6 * 3600  # seconds between history clean-ups
STUCK_BYTES = 4096  # a client with this much waiting ...
STUCK_SECONDS = 30  # ... for this long does not read
KEEP_OPEN_RETRY = 5  # seconds
TRACE_POLL = 0.5  # seconds between reads of the traces
NOTIFY_POLL = 5  # seconds between checks for notifications
MQTT_KEYS = ("mqtt_enabled", "mqtt_prefix", "mqtt_base")
ANALYZE_SECONDS = 30  # of trace the meter check looks at
JOBS_KEPT = 20  # finished tool runs kept for the web interface
NOTES = {
    "de": {
        "missing": (
            "Device Proxy: {name} – Gerät fehlt",
            "{device} ist nicht angeschlossen (seit {since}).",
        ),
        "no_client": (
            "Device Proxy: {name} – kein Client",
            "Seit {since} ist kein Client verbunden.",
        ),
        "silence": (
            "Device Proxy: {name} – keine Daten",
            "Seit {since} kommen keine Daten vom Gerät.",
        ),
        "stuck": (
            "Device Proxy: {name} – Client liest nicht",
            "{address} liest nicht mehr; alle Clients dieser Verbindung werden gebremst.",
        ),
        "line_errors": (
            "Device Proxy: {name} – Leitungsfehler",
            "Die Leitungsfehler steigen ({count} seit Start) – Baudrate oder Format prüfen.",
        ),
        "ser2net": (
            "Device Proxy: ser2net startet immer wieder neu",
            "ser2net ist in den letzten 10 Minuten {count}× beendet worden. Siehe Log der App.",
        ),
        "unreachable": (
            "Device Proxy: {name} – Gerät nicht erreichbar",
            "{target} antwortet nicht (seit {since}): {error}.",
        ),
        "listen": (
            "Device Proxy: {name} – Port belegt",
            "Port {port} kann nicht geöffnet werden: {error}.",
        ),
        "custom": (
            "Device Proxy: eigene ser2net.yaml unbrauchbar",
            "Die eigene ser2net.yaml wird nicht verwendet, es wird nichts bereitgestellt. "
            "Siehe Einstellungen der App.",
        ),
    },
    "en": {
        "missing": (
            "Device Proxy: {name} – device missing",
            "{device} is not plugged in (since {since}).",
        ),
        "no_client": ("Device Proxy: {name} – no client", "No client connected since {since}."),
        "silence": ("Device Proxy: {name} – no data", "No data from the device since {since}."),
        "stuck": (
            "Device Proxy: {name} – client does not read",
            "{address} stopped reading; all clients of this connection are slowed down.",
        ),
        "line_errors": (
            "Device Proxy: {name} – line errors",
            "Line errors are rising ({count} since start) – check baud rate and format.",
        ),
        "ser2net": (
            "Device Proxy: ser2net keeps restarting",
            "ser2net ended {count}× in the last 10 minutes. See the app log.",
        ),
        "unreachable": (
            "Device Proxy: {name} – device not reachable",
            "{target} does not answer (since {since}): {error}.",
        ),
        "listen": (
            "Device Proxy: {name} – port in use",
            "Port {port} cannot be opened: {error}.",
        ),
        "custom": (
            "Device Proxy: own ser2net.yaml unusable",
            "Your own ser2net.yaml is not used, nothing is shared. See the app's settings.",
        ),
    },
}
IMPORT_DIR = Path("/config/import")  # a ser2net.yaml put here is taken over at start


@dataclass
class ApplyResult:
    changes: list[Change]
    rebuilt: list[str]  # names of the connections ser2net set up again
    disconnected: list[str]  # names of the connections whose clients had to reconnect


class CustomError(ValueError):
    """The user's ser2net.yaml cannot be used; .check has the errors."""

    def __init__(self, check: custom.CustomCheck) -> None:
        super().__init__(", ".join(e["code"] for e in check.errors))
        self.check = check


@dataclass
class Activity:
    """What the app sees of a connection between status reads."""

    kept_open: bool = False
    bytes_kept: int = 0  # read by the app's own client
    last_data: float = 0.0
    stuck_since: dict[str, float] = field(default_factory=dict)
    stuck_reported: set[str] = field(default_factory=set)


class Controller:
    def __init__(
        self,
        store: Store,
        events: EventLog,
        config_file: Path,
        *,
        custom_file: Path = custom.PATH,
        import_dir: Path = IMPORT_DIR,
        trace: TraceHub | None = None,
    ) -> None:
        self.store = store
        self.events = events
        self.config_file = config_file
        self.custom_file = custom_file
        self.import_dir = import_dir
        self.config = store.load()
        self._written: dict[str, str] = {}  # what ser2net got last: alias → block
        self.ser2net = Ser2Net(config_file, on_exit=self._ser2net_ended)
        self.admin = AdminClient(self._admin_event)
        self.present: dict[str, bool] = {}
        self.status: dict[str, PortStatus] = {}  # alias → last status from ser2net
        self.activity: dict[str, Activity] = {}  # connection id → activity
        self.internal: set[str] = set()  # addresses of the app's own clients
        self._keepers: dict[str, asyncio.Task[None]] = {}
        self.trace = trace or TraceHub()
        self.devices: list[Device] = []
        self.lan_ip: str | None = None
        self.client_since: dict[tuple[str, str], float] = {}  # (alias, address) → time
        self.rates: dict[str, tuple[float, int, int, float, float]] = {}  # alias → t, rx, tx, r/s
        self.line_errors: dict[str, dict[str, int] | None] = {}  # connection id → since start
        self._line_base: dict[str, dict[str, int]] = {}
        self.latency: dict[str, str] = {}  # connection id → result of set_low_latency
        self.ser2net_version = ""
        self.notifier = Notifier()
        self.jobs: dict[str, dict[str, object]] = {}  # tool runs: id → state
        self._tasks: set[asyncio.Task[None]] = set()  # the tool runs' tasks
        self._restarts: list[float] = []
        self._custom_invalid = False
        self._since: dict[tuple[str, str], float] = {}  # (connection id, condition) → since
        self._line_rise: dict[str, float] = {}  # connection id → last rise of line errors
        self._paused: set[str] = set()  # connections a tool has taken over
        self.proxies: dict[str, ModbusProxy] = {}  # connection id → running Modbus proxy
        self._proxy_tasks: dict[str, asyncio.Task[None]] = {}
        self.mqtt = HaBridge(self)
        self._mqtt_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._stop = asyncio.Event()

    # configuration

    @property
    def uses_custom(self) -> bool:
        return self.config.settings.source == "custom"

    @property
    def active(self) -> tuple[Connection, ...]:
        """The form connections ser2net shares (none while the user's own file is used)."""
        return () if self.uses_custom else self.config.serial

    @property
    def with_device(self) -> tuple[Connection, ...]:
        """The connections in use that open a serial device (ser2net's and Modbus RTU)."""
        return self.active + tuple(c for c in self.config.modbus if c.link == "rtu")

    def _runtime(self) -> tuple[str, dict[str, str]]:
        if not self.uses_custom:
            return render(self.config), blocks(self.config)
        try:
            text = self.custom_file.read_text(encoding="utf-8")
        except OSError as err:
            self.events.emit(
                "error", "custom_invalid", errors=[{"code": "unreadable", "error": str(err)}]
            )
            self._custom_invalid = True
            return render(AppConfig()), {}
        check = custom.check(text)
        if not check.ok:
            self.events.emit("error", "custom_invalid", errors=check.errors)
            self._custom_invalid = True
            return render(AppConfig()), {}  # admin socket only, nothing shared
        self._custom_invalid = False
        return custom.runtime(text, check.version), custom.blocks(text)

    def write_config(self) -> None:
        text, self._written = self._runtime()
        tmp = self.config_file.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, self.config_file)
        _LOGGER.debug("Configuration for ser2net:\n%s", text)

    def apply_log_level(self) -> None:
        level = logging.DEBUG if self.config.settings.log_level == "debug" else logging.INFO
        logging.getLogger().setLevel(level)

    def _connection(self, alias: str) -> Connection | None:
        return next((c for c in self.config.connections if c.alias == alias), None)

    def _names(self, alias: str) -> tuple[str | None, str]:
        c = None if self.uses_custom else self._connection(alias)
        return (c.id, c.name) if c else (None, alias)

    async def start(self, stop: asyncio.Event) -> None:
        self._stop = stop
        self.apply_log_level()
        self.trace.prepare()
        self.write_config()
        await self.import_folder()
        active = [c for c in self.config.connections if c.enabled]
        self.events.emit(
            "info", "app_started", connections=len(self.config.connections), active=len(active)
        )
        for c in self.config.modbus:
            self.events.emit(
                "info",
                "modbus_loaded",
                connection=c.id,
                name=c.name,
                state="active" if c.enabled else "disabled",
                link=c.link.upper().replace("_", " over "),
                target=c.upstream,
                port=c.port,
                max_clients=c.max_clients,
            )
        for c in self.config.serial:
            self.events.emit(
                "info",
                "connection_loaded",
                connection=c.id,
                name=c.name,
                state="active" if c.enabled else "disabled",
                device=c.device,
                format=c.serial_format,
                mode=c.mode,
                port=c.port,
                max_clients=c.max_clients,
            )
        self._reconcile_keepers()
        await self._reconcile_proxies()
        self.devices = scan()
        self._apply_latency()
        self.lan_ip = await asyncio.to_thread(host_lan_ip)
        self.ser2net_version = await self.ser2net.version()
        self._start_mqtt()
        try:
            await asyncio.gather(
                self.ser2net.run(stop),
                self.admin.run(stop),
                self._loop(stop, TRACE_POLL, self._trace_tick),
                self._loop(stop, DEVICE_POLL, self._device_tick),
                self._loop(stop, NOTIFY_POLL, self._notify_tick),
                self._loop(stop, STATUS_POLL, self.read_status),
                self._loop(stop, STATUS_POLL, self._proxy_tick),
                self._loop(stop, HOUSEKEEPING, self._housekeeping),
            )
        finally:
            for task in self._keepers.values():
                task.cancel()
            for task in self._proxy_tasks.values():
                task.cancel()
            await asyncio.gather(*self._proxy_tasks.values(), return_exceptions=True)
            if self._mqtt_task is not None:
                await self._mqtt_task

    async def apply(
        self, new: AppConfig | Callable[[AppConfig], AppConfig], source: str
    ) -> ApplyResult:
        """Save and use a new configuration (already validated). A function builds it from
        the configuration as it is once this change has its turn, so changes made at the
        same time do not overwrite each other."""
        async with self._lock:
            old, before = self.config, self._written
            if callable(new):
                new = new(old)
            items = self.store.save(old, new, source)
            self.config = new
            self.write_config()
            touched = changed(before, self._written)
            self.apply_log_level()
            self._apply_latency()
            if [getattr(old.settings, k) for k in MQTT_KEYS] != [
                getattr(new.settings, k) for k in MQTT_KEYS
            ]:
                await self._restart_mqtt()
            disconnected: list[str] = []
            if touched and self.ser2net.running:
                await self._let_go(before.keys() - self._written.keys())
                disconnected = await self._reload(touched)
            self._reconcile_keepers()
            restarted = await self._reconcile_proxies()
            names = sorted(self._names(alias)[1] for alias in touched if alias in self._written)
            names += sorted(
                c.name for c in old.connections if c.alias in touched and not new.connection(c.id)
            )
            names += sorted(restarted)
            if items:
                self.events.emit("info", "config_changed", summary=summary(items), changes=items)
            return ApplyResult(items, names, disconnected)

    async def save_custom(self, text: str, *, use: bool) -> ApplyResult:
        """Save the user's own ser2net.yaml; with use=True switch to it."""
        check = custom.check(text)
        if not check.ok:
            raise CustomError(check)
        self.custom_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.custom_file.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, self.custom_file)
        self.events.emit("info", "custom_saved", connections=len(check.connections))
        settings = replace(self.config.settings, source="custom") if use else self.config.settings
        return await self.apply(lambda config: replace(config, settings=settings), "custom")

    # import

    def preview(self, text: str) -> tuple[ImportResult, dict[str, dict[str, str]]]:
        """What an import would bring, and the existing connections each item collides with."""
        result = read(text)
        return result, {item.alias: conflicts(self.config, item) for item in result.items}

    async def run_import(
        self,
        text: str,
        *,
        replace_all: bool,
        take: set[str] | None = None,
        on_conflict: dict[str, str] | None = None,
    ) -> ApplyResult:
        result = read(text)
        wanted = take if take is not None else {i.alias for i in result.items if i.connection}
        built: list[AppConfig] = []

        def build(config: AppConfig) -> AppConfig:
            merged = merge(
                config, result, replace_all=replace_all, take=wanted, on_conflict=on_conflict or {}
            )
            built.append(merged)
            return merged

        before = {c.id for c in self.config.connections}
        applied = await self.apply(build, "import")
        added = [c for c in built[-1].connections if c.id not in before]
        self.events.emit(
            "info",
            "imported",
            taken=len(added),
            skipped=len(result.items) - len(added),
            notes=sum(len(i.notes) for i in result.items),
        )
        return applied

    async def import_folder(self) -> None:
        """Take over a ser2net.yaml, an old ser2net.conf or a modbus-proxy.yaml (options of
        ha-modbusproxy) put into the config folder's import/ (merge, no overwrite)."""
        names = ("ser2net.yaml", "ser2net.conf", "modbus-proxy.yaml")
        found = [self.import_dir / n for n in names]
        source = next((f for f in found if f.is_file()), None)
        if source is None:
            return
        try:
            text = source.read_text(encoding="utf-8")
            result, collisions = self.preview(text)
            for item in result.items:
                for note in item.notes:
                    _LOGGER.info("Import %s: %s", item.alias, note)
                if collisions.get(item.alias):
                    _LOGGER.warning(
                        "Import %s: skipped, collides with %s", item.alias, collisions[item.alias]
                    )
            for note in result.notes:
                _LOGGER.info("Import: %s", note)
            await self.run_import(text, replace_all=False)
        except (OSError, ReadError, ValidationError) as err:
            note = err.note if isinstance(err, ReadError) else {"code": "error", "error": str(err)}
            self.events.emit("error", "import_failed", error=note)
            return
        done = source.with_name(f"{source.name}.imported-{int(time.time())}")
        source.replace(done)

    async def _reload(self, touched: set[str]) -> list[str]:
        try:
            await self.admin.reload()
        except AdminError as err:
            _LOGGER.warning("Reload over the admin socket failed (%s), sending SIGHUP", err)
            self.ser2net.reload()
            return []
        disconnected = []
        try:
            for port in await self.admin.showport():
                if port.alias in touched and port.clients and port.pending != "retained":
                    await self.admin.disconnect(port.alias)
                    connection_id, name = self._names(port.alias)
                    disconnected.append(name)
                    self.events.emit(
                        "info",
                        "clients_reconnect",
                        connection=connection_id,
                        name=name,
                        count=len(port.clients),
                    )
        except AdminError as err:
            _LOGGER.warning("Could not check the changed connections: %s", err)
        return disconnected

    # events from ser2net

    def _admin_event(self, kind: str, alias: str, address: str) -> None:
        if address in self.internal:
            _LOGGER.debug("Own client %s: %s on %s", address, kind, alias)
            return
        connection_id, name = self._names(alias)
        if kind == "new connection":
            self.client_since[(alias, address)] = time.time()
        else:
            self.client_since.pop((alias, address), None)
        event = "client_connected" if kind == "new connection" else "client_disconnected"
        self.events.emit("info", event, connection=connection_id, name=name, address=address)

    def _ser2net_ended(self, code: int | None, delay: float) -> None:
        self.events.emit("warning", "ser2net_restart", code=code, delay=delay)
        now = time.time()
        self._restarts = [t for t in self._restarts if now - t < 600] + [now]

    def port_problem(self, c: Connection) -> str | None:
        """Why the connection's port cannot be opened right now (another program has it),
        None when it can or when this app holds it for this connection already."""
        current = self.config.connection(c.id)
        if current and current.enabled and (current.port, current.bind) == (c.port, c.bind):
            return None  # this connection's own port
        host = c.bind or ("127.0.0.1" if self.config.settings.listen == "local" else "")
        family = socket.AF_INET6 if ":" in host else socket.AF_INET
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # as the servers do
            try:
                sock.bind((host, c.port))
            except PermissionError:
                return None  # a low port, not the app's question here
            except OSError as err:
                if err.errno == errno.EADDRINUSE:
                    return "in use by another program"
                if err.errno == errno.EADDRNOTAVAIL:
                    return "the bind address is not on this host"
                return None
        # a program listening on one address only may leave the bind above free
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex((host or "127.0.0.1", c.port)) == 0:
                return "in use by another program"
        return None

    # Modbus proxies

    async def _reconcile_proxies(self) -> list[str]:
        """Start, restart and stop the proxies to match the configuration; the names of
        the connections that were (re)started or stopped."""
        listen = self.config.settings.listen
        wanted = {c.id: c for c in self.config.modbus if c.enabled}
        touched: list[str] = []
        for connection_id, proxy in list(self.proxies.items()):
            c = wanted.get(connection_id)
            if c is not None and proxy.key == restart_key(c, listen):
                proxy.c = c  # name, trace or notifications changed: no restart
                continue
            task = self._proxy_tasks.pop(connection_id)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)  # frees the port
            del self.proxies[connection_id]
            touched.append(proxy.c.name if c is None else c.name)
        for connection_id, c in wanted.items():
            if connection_id in self.proxies:
                continue
            proxy = ModbusProxy(c, listen, self._proxy_event(connection_id), self._proxy_trace(c))
            self.proxies[connection_id] = proxy
            task = asyncio.create_task(proxy.run())
            task.add_done_callback(self._proxy_ended)
            self._proxy_tasks[connection_id] = task
            if c.name not in touched:
                touched.append(c.name)
        return touched

    @staticmethod
    def _proxy_ended(task: asyncio.Task[None]) -> None:
        if not task.cancelled() and (err := task.exception()) is not None:
            _LOGGER.error("Modbus proxy ended", exc_info=err)

    def _proxy_event(self, connection_id: str) -> Callable[..., None]:
        def emit(level: str, kind: str, **params: object) -> None:
            c = self.config.connection(connection_id)
            name = c.name if c else connection_id
            self.events.emit(level, kind, connection=connection_id, name=name, **params)

        return emit

    def _proxy_trace(self, c: Connection) -> Callable[[Chunk], None]:
        def feed(chunk: Chunk) -> None:
            self.trace.feed(c.alias, chunk)

        return feed

    async def _proxy_tick(self) -> None:
        now = time.monotonic()
        for proxy in self.proxies.values():
            s = proxy.stats
            self._rate(proxy.c.alias, s.bytes_from_device, s.bytes_to_device, now)

    # devices

    def check_devices(self) -> None:
        for c in self.with_device:
            if not c.enabled:
                self.present.pop(c.id, None)
                continue
            present = os.path.exists(c.device)
            before = self.present.get(c.id)
            self.present[c.id] = present
            if present == before:
                continue
            if present:
                kind = "device_back" if before is False else "device"
                self.events.emit(
                    "info",
                    kind,
                    connection=c.id,
                    name=c.name,
                    device=c.device,
                    target=os.path.realpath(c.device),
                )
            else:
                self.events.emit(
                    "warning", "device_missing", connection=c.id, name=c.name, device=c.device
                )

    async def _device_tick(self) -> None:
        self.devices = await asyncio.to_thread(scan)
        self.check_devices()
        self.events.flush_bursts()

    def _apply_latency(self) -> None:
        for c in self.with_device:
            if not (c.enabled and c.low_latency):
                self.latency.pop(c.id, None)
                continue
            result = set_low_latency(c.device)
            if result != self.latency.get(c.id) and result == "read_only":
                self.events.emit("warning", "latency_read_only", connection=c.id, name=c.name)
            self.latency[c.id] = result

    # traces

    async def _trace_tick(self) -> None:
        settings = self.config.settings
        taken: set[str] = set()
        aliases = {
            c.alias: (readable_alias(c.name, taken), c.trace)
            for c in self.active + self.config.modbus
            if c.enabled
        }
        await asyncio.to_thread(
            self.trace.poll, aliases, settings.trace_file_mb << 20, settings.trace_keep
        )

    def live(self, connection_id: str, limit: int = 200) -> list[Chunk]:
        c = self.config.connection(connection_id)
        if c is None:
            return []
        return list(self.trace.live.get(c.alias, ()))[-limit:]

    # status and stuck clients

    async def read_status(self) -> None:
        if not self.admin.connected.is_set():
            return
        try:
            ports = await self.admin.showport()
        except AdminError as err:
            _LOGGER.debug("Status not read: %s", err)
            return
        self.status = {p.alias: p for p in ports}
        now = time.monotonic()
        for port in ports:
            self._rate(port.alias, port.bytes_from_device, port.bytes_to_device, now)
            c = self._connection(port.alias)
            if c is not None:
                await self._check_stuck(c, port, now)
                if port.clients and self.present.get(c.id):
                    await self._read_line_errors(c)

    def _rate(self, alias: str, rx: int, tx: int, now: float) -> None:
        before = self.rates.get(alias)
        if before is None or rx < before[1] or tx < before[2]:
            self.rates[alias] = (now, rx, tx, 0.0, 0.0)
            return
        seconds = max(now - before[0], 0.001)
        self.rates[alias] = (
            now,
            rx,
            tx,
            (rx - before[1]) / seconds,
            (tx - before[2]) / seconds,
        )

    async def _read_line_errors(self, c: Connection) -> None:
        counters = await asyncio.to_thread(line_counters, c.device)
        if counters is None:
            self.line_errors[c.id] = None
            return
        base = self._line_base.get(c.id)
        if base is None or any(counters[k] < base[k] for k in counters):
            base = self._line_base[c.id] = counters  # first read or the adapter came back
        delta = {k: counters[k] - base[k] for k in counters}
        before = self.line_errors.get(c.id) or {}
        if sum(delta.values()) > sum(before.values()):
            self.events.emit("warning", "line_errors", connection=c.id, name=c.name, **delta)
            self._line_rise[c.id] = time.time()
        self.line_errors[c.id] = delta

    # MQTT

    def _start_mqtt(self) -> None:
        self.mqtt = HaBridge(self)
        self._mqtt_task = asyncio.create_task(self.mqtt.run(self._stop))

    async def _restart_mqtt(self) -> None:
        if self._mqtt_task is not None:
            self._mqtt_task.cancel()
            try:
                await self._mqtt_task
            except asyncio.CancelledError:
                pass
        self._start_mqtt()

    # notifications

    def _lasting(
        self, connection_id: str, condition: str, active: bool, now: float
    ) -> float | None:
        """Since when the condition holds (None when it does not)."""
        key = (connection_id, condition)
        if not active:
            self._since.pop(key, None)
            return None
        return self._since.setdefault(key, now)

    def problems(self, now: float | None = None) -> dict[str, tuple[str, str]]:
        """The notifications there should be right now: id → (title, message)."""
        now = time.time() if now is None else now
        settings = self.config.settings
        texts = NOTES[settings.notify_language]
        found: dict[str, tuple[str, str]] = {}

        def add(key: str, kind: str, **values: object) -> None:
            title, message = texts[kind]
            found[key] = (title.format(**values), message.format(**values))

        def clock(ts: float) -> str:
            return time.strftime("%d.%m. %H:%M", time.localtime(ts))

        for c in self.config.modbus:
            proxy = self.proxies.get(c.id)
            if proxy is None:
                continue
            missing = c.link == "rtu" and self.present.get(c.id) is False
            if c.notify_missing and (since := self._lasting(c.id, "missing", missing, now)):
                add(
                    f"device_proxy_{c.id}_missing",
                    "missing",
                    name=c.name,
                    device=c.device,
                    since=clock(since),
                )
            down = not missing and proxy.reachable is False
            if c.notify_missing and (since := self._lasting(c.id, "unreachable", down, now)):
                add(
                    f"device_proxy_{c.id}_unreachable",
                    "unreachable",
                    name=c.name,
                    target=c.upstream,
                    error=proxy.stats.last_error or "?",
                    since=clock(proxy.reachable_since),
                )
            if proxy.listen_error:
                add(
                    f"device_proxy_{c.id}_listen",
                    "listen",
                    name=c.name,
                    port=c.port,
                    error=proxy.listen_error,
                )
            since = self._lasting(c.id, "no_client", proxy.listening and not proxy.clients, now)
            if c.notify_no_client and since and now - since >= settings.no_client_minutes * 60:
                add(f"device_proxy_{c.id}_no_client", "no_client", name=c.name, since=clock(since))
        for c in self.active:
            if not c.enabled:
                continue
            port = self.status.get(c.alias)
            activity = self.activity.get(c.id)
            clients = [
                cl for cl in (port.clients if port else []) if cl.address not in self.internal
            ]
            device_open = bool(port and port.clients)
            missing = self.present.get(c.id) is False
            if c.notify_missing and (since := self._lasting(c.id, "missing", missing, now)):
                add(
                    f"device_proxy_{c.id}_missing",
                    "missing",
                    name=c.name,
                    device=c.device,
                    since=clock(since),
                )
            idle = not missing and self.ser2net.running and not clients
            since = self._lasting(c.id, "no_client", idle, now)
            if c.notify_no_client and since and now - since >= settings.no_client_minutes * 60:
                add(f"device_proxy_{c.id}_no_client", "no_client", name=c.name, since=clock(since))
            flow = self.trace.flow.get(c.alias)
            last = flow.last_rx if flow and flow.last_rx else None
            opened = self._lasting(c.id, "open", device_open, now)
            if c.silence_minutes and opened:
                quiet_since = max(last or opened, opened)
                if now - quiet_since >= c.silence_minutes * 60:
                    add(
                        f"device_proxy_{c.id}_silence",
                        "silence",
                        name=c.name,
                        since=clock(quiet_since),
                    )
            if settings.notify_stuck and activity and activity.stuck_reported:
                address = sorted(activity.stuck_reported)[0]
                add(f"device_proxy_{c.id}_stuck", "stuck", name=c.name, address=address)
            rise = self._line_rise.get(c.id)
            if settings.notify_line_errors and rise and now - rise < 600:
                count = sum((self.line_errors.get(c.id) or {}).values())
                add(f"device_proxy_{c.id}_line_errors", "line_errors", name=c.name, count=count)
        recent = [t for t in self._restarts if now - t < 600]
        if settings.notify_ser2net and len(recent) >= 3:
            add("device_proxy_restarts", "ser2net", count=len(recent))
        if self.uses_custom and self._custom_invalid:
            add("device_proxy_custom_invalid", "custom")
        return found

    async def _notify_tick(self) -> None:
        settings = self.config.settings
        await self.notifier.update(
            self.problems(),
            grace=settings.notify_grace,
            dismiss=settings.notify_dismiss,
            service=settings.notify_service,
            resolved_message=settings.notify_resolved,
        )

    # tools

    def analyze(self, connection_id: str) -> dict[str, object]:
        """What the device sent in the last seconds, read as a smart meter (SML or D0)."""
        c = self.config.connection(connection_id)
        if c is None:
            return {}
        cutoff = time.time() - ANALYZE_SECONDS
        data = b"".join(
            ch.data
            for ch in self.trace.live.get(c.alias, ())
            if ch.direction == "rx" and ch.ts >= cutoff
        )
        return analyze(data).to_dict()

    async def modbus_read(
        self, connection_id: str, unit: int, function: int, address: int, count: int
    ) -> dict[str, object]:
        """Read registers or coils through a Modbus connection's proxy (in turn with the
        clients)."""
        proxy = self.proxies.get(connection_id)
        if proxy is None:
            raise ValueError("the connection is not active")
        limit = 125 if function in (3, 4) else 2000
        if function not in (1, 2, 3, 4) or not 1 <= count <= limit:
            raise ValueError(f"function 1 to 4, 1 to {limit} values")
        if not 1 <= unit <= 255 or not 0 <= address <= 65535 or address + count > 65536:
            raise ValueError("unit 1 to 255, address 0 to 65535")
        started = time.monotonic()
        answer = await proxy.ask(unit, struct.pack(">BHH", function, address, count))
        result = read_result(function, count, answer)
        return {**result, "time_ms": round((time.monotonic() - started) * 1000, 1)}

    def start_scan(self, connection_id: str, first: int, last: int, timeout_ms: int) -> str:
        """Find the unit ids that answer, e.g. on an RS485 bus."""
        proxy = self.proxies.get(connection_id)
        if proxy is None:
            raise ValueError("the connection is not active")
        if not 1 <= first <= last <= 247 or not 50 <= timeout_ms <= 5000:
            raise ValueError("units 1 to 247, timeout 50 to 5000 ms")
        job_id = self._new_job(connection_id, last - first + 1)
        self._spawn(self._scan(job_id, proxy, range(first, last + 1), timeout_ms / 1000))
        return job_id

    def _new_job(self, connection_id: str, total: int) -> str:
        """A tool run, one at a time per connection; finished ones beyond the last 20 go."""
        if any(
            j.get("connection") == connection_id and j["state"] == "running"
            for j in self.jobs.values()
        ):
            raise ValueError("already running")
        finished = [k for k, j in self.jobs.items() if j["state"] != "running"]
        for key in finished[: max(0, len(finished) - JOBS_KEPT)]:
            del self.jobs[key]
        job_id = new_id()
        self.jobs[job_id] = {
            "connection": connection_id,
            "state": "running",
            "done": 0,
            "total": total,
            "results": [],
        }
        return job_id

    def _spawn(self, coro: Coroutine[Any, Any, None]) -> None:
        """A background task, kept referenced until it ends (asyncio holds it weakly)."""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _scan(self, job_id: str, proxy: ModbusProxy, units: range, timeout: float) -> None:
        job = self.jobs[job_id]
        found: list[dict[str, object]] = []
        job["results"] = found
        try:
            for done, unit in enumerate(units, 1):
                answer = await proxy.ask(unit, b"\x03\x00\x00\x00\x01", timeout=timeout, retries=0)
                job["done"] = done
                code = answer[1] if answer and answer[0] & 0x80 and len(answer) > 1 else None
                if code == EXC_PATH:
                    raise ConnectionError(proxy.stats.last_error or "device not reachable")
                if answer and code != EXC_TARGET:
                    found.append({"unit": unit, "exception": code})
            job["state"] = "done"
        except (OSError, ConnectionError) as err:
            job["state"], job["error"] = "failed", str(err)
        except asyncio.CancelledError:
            job["state"], job["error"] = "failed", "stopped"
            raise

    def start_detect(self, connection_id: str) -> str:
        """Find the baud rate of a pushing meter; ser2net lets go of the device meanwhile."""
        c = self.config.connection(connection_id)
        if c is None:
            raise ValueError("no such connection")
        if c.kind != "serial":
            raise ValueError("only for ser2net's connections")
        job_id = self._new_job(connection_id, 0)
        self._spawn(self._detect(job_id, c))
        return job_id

    async def _detect(self, job_id: str, c: Connection) -> None:
        job = self.jobs[job_id]
        self._paused.add(c.id)
        keeper = self._keepers.pop(c.id, None)
        if keeper is not None:
            keeper.cancel()
        try:
            await self.admin.command(f"setportenable {c.alias} off")
            await asyncio.sleep(0.5)  # let ser2net close the device

            def progress(done: int, total: int, candidate: object) -> None:
                job["done"], job["total"] = done, total

            results = await asyncio.to_thread(detect, c.device, progress)
            job["results"] = [r.to_dict() for r in results]
            job["state"] = "done"
        except (OSError, AdminError) as err:
            job["state"], job["error"] = "failed", str(err)
        finally:
            self._paused.discard(c.id)
            if c.enabled:
                try:
                    await self.admin.command(f"setportenable {c.alias} on")
                except AdminError as err:
                    _LOGGER.warning("Could not switch %s on again: %s", c.name, err)
            self._reconcile_keepers()

    # the state for the web interface

    def snapshot(self) -> dict[str, object]:
        """Everything the status pages show, in one JSON-ready structure."""
        settings = self.config.settings
        connections = []
        for c in self.config.connections:
            if c.kind == "modbus":
                connections.append(self._modbus_snapshot(c))
                continue
            port = self.status.get(c.alias)
            flow = self.trace.flow.get(c.alias)
            rate = self.rates.get(c.alias)
            activity = self.activity.get(c.id)
            device = device_for(c.device, self.devices) if self.present.get(c.id) else None
            clients = [
                {
                    "address": cl.address,
                    "since": self.client_since.get((c.alias, cl.address)),
                    "bytes_to_client": cl.bytes_to_client,
                    "bytes_from_client": cl.bytes_from_client,
                    "queued": cl.queued,
                    "stuck": bool(activity and cl.address in activity.stuck_reported),
                }
                for cl in (port.clients if port else [])
                if cl.address not in self.internal
            ]
            connections.append(
                {
                    **c.to_dict(),
                    "alias": c.alias,
                    "present": self.present.get(c.id),
                    "tty": device.tty if device else None,
                    "usb": device.to_dict() if device else None,
                    "running": bool(port and port.enabled) and not self.uses_custom,
                    "pending": port.pending if port else None,
                    "clients": clients,
                    "kept_open": bool(activity and activity.kept_open),
                    "bytes_from_device": port.bytes_from_device if port else 0,
                    "bytes_to_device": port.bytes_to_device if port else 0,
                    "rate_from_device": rate[3] if rate else 0.0,
                    "rate_to_device": rate[4] if rate else 0.0,
                    "last_data": flow.last_rx if flow else None,
                    "line_errors": self.line_errors.get(c.id),
                    "latency": self.latency.get(c.id),
                    "addresses": addresses(c, settings, self.lan_ip),
                }
            )
        used = {
            os.path.realpath(c.device): c.name for c in self.config.connections if c.uses_device
        }
        return {
            "ser2net_running": self.ser2net.running and self.admin.connected.is_set(),
            "source": settings.source,
            "settings": settings.to_dict(),
            "lan_ip": self.lan_ip,
            "connections": connections,
            "custom_ports": [
                {"alias": p.alias, "clients": [cl.address for cl in p.clients]}
                for p in self.status.values()
            ]
            if self.uses_custom
            else [],
            "devices": [{**d.to_dict(), "used_by": used.get(d.tty)} for d in self.devices],
            "trace_files": self.trace.files(),
            "mqtt": self.mqtt.state,
        }

    def _modbus_snapshot(self, c: Connection) -> dict[str, object]:
        proxy = self.proxies.get(c.id)
        flow = self.trace.flow.get(c.alias)
        rate = self.rates.get(c.alias)
        present = self.present.get(c.id) if c.link == "rtu" else None
        device = device_for(c.device, self.devices) if present else None
        state = proxy.state() if proxy else None
        return {
            **c.to_dict(),
            "alias": c.alias,
            "present": present,
            "tty": device.tty if device else None,
            "usb": device.to_dict() if device else None,
            "running": bool(proxy and proxy.listening),
            "pending": None,
            "clients": [
                {
                    "address": cl.info.address,
                    "since": cl.info.since,
                    "bytes_to_client": cl.info.bytes_out,
                    "bytes_from_client": cl.info.bytes_in,
                    "requests": cl.info.requests,
                    "blocked": cl.info.blocked,
                    "failed": cl.info.failed,
                    "queued": 0,
                    "stuck": False,
                }
                for cl in (proxy.clients.values() if proxy else [])
            ],
            "kept_open": False,
            "bytes_from_device": proxy.stats.bytes_from_device if proxy else 0,
            "bytes_to_device": proxy.stats.bytes_to_device if proxy else 0,
            "rate_from_device": rate[3] if rate else 0.0,
            "rate_to_device": rate[4] if rate else 0.0,
            "last_data": flow.last_rx if flow else None,
            "line_errors": None,
            "latency": self.latency.get(c.id),
            "addresses": addresses(c, self.config.settings, self.lan_ip),
            "modbus": state,
        }

    async def _check_stuck(self, c: Connection, port: PortStatus, now: float) -> None:
        activity = self.activity.setdefault(c.id, Activity())
        current = {client.address for client in port.clients}
        for address in list(activity.stuck_since):
            if address not in current:
                activity.stuck_since.pop(address)
                activity.stuck_reported.discard(address)
        for client in port.clients:
            if client.address in self.internal:
                continue
            if client.queued < STUCK_BYTES:
                activity.stuck_since.pop(client.address, None)
                activity.stuck_reported.discard(client.address)
                continue
            since = activity.stuck_since.setdefault(client.address, now)
            if now - since < STUCK_SECONDS or client.address in activity.stuck_reported:
                continue
            activity.stuck_reported.add(client.address)
            self.events.emit(
                "warning",
                "client_stuck",
                connection=c.id,
                name=c.name,
                address=client.address,
                queued=client.queued,
            )
            if c.stuck_disconnect:
                # ser2net can only disconnect all clients of a connection, not one
                try:
                    await self.admin.disconnect(c.alias)
                except AdminError as err:
                    _LOGGER.warning("Could not disconnect %s: %s", c.name, err)
                else:
                    self.events.emit(
                        "warning",
                        "stuck_disconnected",
                        connection=c.id,
                        name=c.name,
                        address=client.address,
                    )

    # keeping devices open

    def _wanted_keepers(self) -> set[str]:
        return {c.id for c in self.active if c.enabled and c.keep_open and c.id not in self._paused}

    async def _let_go(self, removed: set[str]) -> None:
        """Before ser2net reads its file again, the clients of the connections that go away
        are disconnected (the app's own ones too): ser2net 4.6 keeps a connection that is in
        use at the reload, and when it was in use at an earlier reload as well, it starts
        that earlier configuration again once the client leaves, so the port stays open."""
        wanted = self._wanted_keepers()
        gone = [self._keepers.pop(i) for i in list(self._keepers) if i not in wanted]
        for task in gone:
            task.cancel()
        await asyncio.gather(*gone, return_exceptions=True)
        if not removed:
            return

        async def busy() -> set[str]:
            ports = await self.admin.showport()
            free = ("unconnected", "closed")  # closed: switched off
            return {p.alias for p in ports if p.alias in removed and p.session not in free}

        try:
            for alias in await busy():
                with contextlib.suppress(AdminError):  # the session ended meanwhile
                    await self.admin.disconnect(alias)
            deadline = time.monotonic() + 3
            while await busy() and time.monotonic() < deadline:
                await asyncio.sleep(0.1)
        except AdminError as err:
            _LOGGER.warning("Could not disconnect the clients of removed connections: %s", err)

    def _reconcile_keepers(self) -> None:
        wanted = self._wanted_keepers()
        for connection_id in list(self._keepers):
            if connection_id not in wanted:
                self._keepers.pop(connection_id).cancel()
                self.activity.setdefault(connection_id, Activity()).kept_open = False
        for connection_id in wanted - self._keepers.keys():
            self._keepers[connection_id] = asyncio.create_task(self._keep_open(connection_id))

    async def _keep_open(self, connection_id: str) -> None:
        failed = False
        activity = self.activity.setdefault(connection_id, Activity())
        while not self._stop.is_set():
            c = self.config.connection(connection_id)
            if c is None:
                return
            host = c.bind if c.bind and c.bind not in ("0.0.0.0", "::") else "127.0.0.1"
            family = socket.AF_INET6 if ":" in host else socket.AF_INET
            sock = socket.socket(family, socket.SOCK_STREAM)
            sock.setblocking(False)
            sock.bind((host, 0))
            own = sock.getsockname()
            address = f"[{own[0]}]:{own[1]}" if family == socket.AF_INET6 else f"{own[0]}:{own[1]}"
            self.internal.add(address)  # before connecting: ser2net reports it at once
            try:
                await asyncio.get_running_loop().sock_connect(sock, (host, c.port))
                reader, writer = await asyncio.open_connection(sock=sock)
            except OSError as err:
                sock.close()
                self.internal.discard(address)
                if not failed:
                    failed = True
                    self.events.emit(
                        "warning", "keep_open_failed", connection=c.id, name=c.name, error=str(err)
                    )
                await asyncio.sleep(KEEP_OPEN_RETRY)
                continue
            failed = False
            activity.kept_open = True
            try:
                while data := await reader.read(4096):
                    activity.bytes_kept += len(data)
                    activity.last_data = time.time()
            except OSError:
                pass
            finally:
                activity.kept_open = False
                writer.close()
                self.internal.discard(address)
            await asyncio.sleep(KEEP_OPEN_RETRY)

    # housekeeping

    async def _housekeeping(self) -> None:
        days = self.config.settings.history_days
        if removed := self.events.prune(days):
            _LOGGER.info("History: %s entries older than %s days removed", removed, days)

    @staticmethod
    async def _loop(
        stop: asyncio.Event, seconds: float, step: Callable[[], Awaitable[None]]
    ) -> None:
        while not stop.is_set():
            try:
                await step()
            except Exception:  # a failing step must not stop the others
                _LOGGER.exception("Background step %s failed", getattr(step, "__name__", step))
            try:
                await asyncio.wait_for(stop.wait(), seconds)
            except TimeoutError:
                pass
