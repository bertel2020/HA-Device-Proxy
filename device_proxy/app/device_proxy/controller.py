"""Ties the app together: configuration, ser2net, its admin socket, devices and events.

Saving a configuration writes ser2net.yaml and makes ser2net reload it. ser2net keeps a
changed connection as it was while clients are connected; those clients (and only those of
the changed connections) are disconnected so the change takes effect, the others stay.

ser2net slows all clients of a connection down when one of them stops reading; a client
whose queue stays full is reported (and its connection's clients disconnected, if set).
ser2net opens a device only while a client is connected; "keep open" makes the app one.

With the settings' source "custom" the user's own ser2net.yaml is used instead of the forms;
the form connections stay saved but unused (no device checks, no keep open).

The other kinds (Modbus, EnOcean; kinds.py) are not ser2net's: each such connection runs a proxy in
the app, whatever the source. Saving restarts only the proxies whose settings changed.
"""

from __future__ import annotations

import asyncio
import contextlib
import errno
import ipaddress
import json
import logging
import os
import re
import socket
import struct
import time
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass, field, replace
from functools import partial
from pathlib import Path
from typing import Any

from . import custom, esp, health, i18n, model, testcase
from .addresses import addresses, host_lan
from .admin import AdminClient, AdminError, PortStatus
from .clients import KnownClients, host_of, is_local, local_kind, parse_names, plain_host
from .config import blocks, changed, readable_alias, remaddr_without, render
from .db import Database
from .detect import detect
from .devices import (
    Device,
    device_for,
    fingerprint,
    line_counters,
    moved,
    scan,
    set_low_latency,
    usb_node,
    usb_reset,
)
from .enocean import EnOceanProxy
from .enocean_ha import EnOceanHa
from .enocean_tools import Capture, Captures, parse_frame, sendable
from .events import EventLog
from .ha_mqtt import HaBridge
from .importer import ImportResult, ReadError, conflicts, merge, read
from .kinds import PROXIED, AppProxy
from .meter import Analysis, analyze
from .modbus import (
    DEVICE_ID_REQUEST,
    EXC_PATH,
    EXC_TARGET,
    SUNSPEC_BASES,
    SUNSPEC_COMMON,
    ModbusProxy,
    device_id,
    is_sunspec,
    read_result,
    sunspec_common,
    write_pdu,
)
from .model import (
    AppConfig,
    Connection,
    ValidationError,
    new_id,
    own_address,
    parse_sender_names,
)
from .notify import SHOWN_FILE, Notifier, set_switch
from .process import Ser2Net
from .sessions import ClientSessions
from .store import PASSWORD_KEPT, Change, SaveError, Store, hidden, quiet, summary
from .trace import Chunk, TraceHub, recording_stem

_LOGGER = logging.getLogger(__name__)

DEVICE_POLL = 2  # seconds between device checks
STATUS_POLL = 5  # seconds between status reads from ser2net
HOUSEKEEPING = 6 * 3600  # seconds between history clean-ups
REFUSED_REASONS = {
    "client_refused": "full",
    "client_refused_network": "network",
    "client_refused_exclusive": "exclusive",
}
STUCK_BYTES = 4096  # a client with this much waiting ...
STUCK_SECONDS = 30  # ... for this long does not read
KEEP_OPEN_RETRY = 5  # seconds
PROXY_RESTART = 30  # seconds before a proxy that ended by an error starts again
TRACE_POLL = 0.5  # seconds between reads of the traces
NOTIFY_POLL = 5  # seconds between checks for notifications
MQTT_KEYS = (
    "mqtt_enabled",
    "mqtt_prefix",
    "mqtt_base",
    "mqtt_host",
    "mqtt_port",
    "mqtt_user",
    "mqtt_password",
    "mqtt_tls",
)
ANALYZE_SECONDS = 30  # of trace the meter check looks at
JOBS_KEPT = 20  # finished tool runs kept for the web interface
IDENTIFY_MAX = 16  # units the scan asks who they are
EXCLUSIVE_MAX = 240  # minutes one host may have a connection to itself
USB_BACK = 10  # seconds a reset USB adapter may take to come back
AUTO_RESTART_MAX = 3  # restarts in a row without data, then the app only warns
POWER_OFF = 5  # seconds a power cycle keeps the device off
POWER_ON_TRIES = 3  # the switch must come back on: asked again when that fails
POWER_RETRY = 2  # seconds between those attempts
POWER_BACK = 30  # seconds a device may take to come back after the power was off
NOTIFY_EACH_CLIENT = 5  # more new clients than this: one notification for all of them
DUTY_NOTE = 80  # % of the EnOcean duty cycle limit: notification
NOTES = i18n.section("notifications")
REASONS = i18n.section("reasons")  # why a gateway went on through its fallback, or not
PRINTS_FILE = Path("/data/device_prints.json")  # the adapter of each connection, see moved_to
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
        known_clients: KnownClients | None = None,
        prints_file: Path = PRINTS_FILE,
        notify_file: Path | None = SHOWN_FILE,
    ) -> None:
        self.store = store
        self.known_clients = known_clients or KnownClients()
        self.prints_file = prints_file
        # maintenance: connection id → (the one host that may connect, until when); ends with
        # an app restart, so access always comes back
        self.exclusive: dict[str, tuple[str, float]] = {}
        try:  # the adapter each connection had last, to find it again on another port
            self.prints: dict[str, dict[str, str]] = json.loads(prints_file.read_text())
        except (OSError, ValueError):
            self.prints = {}
        self.events = events
        self.sessions = ClientSessions(events.db)
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
        self.lan_net: str | None = None
        self.client_since: dict[tuple[str, str], float] = {}  # (alias, address) → time
        self.rates: dict[str, tuple[float, int, int, float, float]] = {}  # alias → t, rx, tx, r/s
        self.line_errors: dict[str, dict[str, int] | None] = {}  # connection id → since start
        self._line_base: dict[str, dict[str, int]] = {}
        self.latency: dict[str, str] = {}  # connection id → result of set_low_latency
        self.ser2net_version = ""
        self.notifier = Notifier(path=notify_file)
        self.jobs: dict[str, dict[str, object]] = {}  # tool runs: id → state
        self._tasks: set[asyncio.Task[None]] = set()  # the tool runs' tasks
        self._restarts: list[float] = []
        self._custom_invalid = False
        self._since: dict[tuple[str, str], float] = {}  # (connection id, condition) → since
        self._line_rise: dict[str, float] = {}  # connection id → last rise of line errors
        self._paused: set[str] = set()  # connections a tool or a restart has taken over
        # automatic restarts without data: connection id → [last restart, count, gave up]
        self._auto: dict[str, list[Any]] = {}
        self.proxies: dict[str, AppProxy] = {}  # connection id → running proxy
        self._proxy_tasks: dict[str, asyncio.Task[None]] = {}
        self._proxy_failed: dict[str, float] = {}  # connection id → when its proxy ended
        self.health_file = health.HEALTH_FILE
        self.events.listeners.append(lambda event: self.mqtt.send_event(event))
        self.panel_url = ""  # the link to this app in Home Assistant, for its devices
        self.mqtt = HaBridge(self)
        self.enocean_ha = EnOceanHa(self)
        self.captures = Captures(self.trace.record_dir)
        self.captures.on_full = self._capture_full
        self.captures.on_failed = self._capture_failed
        self._mqtt_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self.last_change: dict[str, object] | None = None  # see apply()
        self._stop = asyncio.Event()
        self._running = False  # start() has begun: MQTT may be started

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
        """The connections in use that open a serial device (ser2net's and the proxies')."""
        return tuple(c for c in self.active + self.config.proxied if c.uses_device)

    def _runtime(self) -> tuple[str, dict[str, str]]:
        if not self.uses_custom:
            config = self._for_ser2net(self.config)
            return render(config), blocks(config)
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
        text, written = self._runtime()
        tmp = self.config_file.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, self.config_file)
        self._written = written  # only what ser2net can read
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
        self._stop, self._running = stop, True
        self.apply_log_level()
        self.trace.prepare()
        self.lan_ip, self.lan_net = await asyncio.to_thread(host_lan)
        model.HOST_NETWORK = self.lan_net  # before the first ser2net.yaml and proxy
        self.write_config()
        await self.import_folder()
        active = [c for c in self.config.connections if c.enabled]
        self.events.emit(
            "info",
            "app_started",
            version=os.environ.get("APP_VERSION", "dev"),
            connections=len(self.config.connections),
            active=len(active),
        )
        for c in self.config.proxied:
            self.events.emit(
                "info",
                f"{c.kind}_loaded",
                connection=c.id,
                name=c.name,
                state="active" if c.enabled else "disabled",
                **PROXIED[c.kind].loaded(c),
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
        await self.enocean_ha.update()
        self.devices = scan()
        self._apply_latency()
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
                self._loop(stop, STATUS_POLL, self._silence_tick),
                self._loop(stop, STATUS_POLL, self._sessions_tick),
                self._loop(stop, HOUSEKEEPING, self._housekeeping),
                self._loop(stop, STATUS_POLL, self._report_problems),
            )
        finally:
            # also when one of them failed: the others and MQTT end too, and the app exits
            # (and is started again) instead of serving the panel without its proxies
            stop.set()
            self.events.emit("info", "app_stopped")
            for task in self._keepers.values():
                task.cancel()
            for task in self._proxy_tasks.values():
                task.cancel()
            await asyncio.gather(*self._proxy_tasks.values(), return_exceptions=True)
            self.sessions.shutdown()
            await self.enocean_ha.stop()
            if self._mqtt_task is not None:
                await asyncio.gather(self._mqtt_task, return_exceptions=True)

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
            working = [c.id for c in old.connections if self.working(c)]
            version = self.store.latest_id()
            items = self.store.save(old, new, source)
            if items and not quiet(items):
                # the configuration before, while it is the last change: what to go back to
                # when a connection that worked stops working (the panel offers it)
                self.last_change = (
                    {"ts": time.time(), "version": version, "working": working}
                    if version is not None
                    else None
                )
            self.config = new
            self.events.debounce_count = new.settings.debounce_count
            self.events.window = new.settings.debounce_minutes * 60
            touched: set[str] = set()
            disconnected: list[str] = []
            # saved: whatever fails now, the proxies and entities still follow the new
            # configuration, and the history has the change
            try:
                self.known_clients.named(parse_names(new.settings.client_names))
                try:
                    self.write_config()
                except OSError as err:
                    raise SaveError(
                        err.errno,
                        f"configuration saved, but not written for ser2net: {err.strerror or err}",
                    ) from err
                touched = changed(before, self._written)
                self.apply_log_level()
                self._apply_latency()
                if [getattr(old.settings, k) for k in MQTT_KEYS] != [
                    getattr(new.settings, k) for k in MQTT_KEYS
                ]:
                    await self._restart_mqtt()
                if touched and self.ser2net.running:
                    await self._let_go(before.keys() - self._written.keys())
                    disconnected = await self._reload(touched)
            finally:
                try:
                    self._reconcile_keepers()
                    restarted = await self._reconcile_proxies()
                    await self.enocean_ha.update()
                finally:
                    if items:
                        self.events.emit(
                            "info", "config_changed", summary=summary(items), changes=items
                        )
            names = sorted(self._names(alias)[1] for alias in touched if alias in self._written)
            names += sorted(
                c.name for c in old.connections if c.alias in touched and not new.connection(c.id)
            )
            names += sorted(restarted)
            return ApplyResult(items, names, disconnected)

    def effects(self, new: AppConfig) -> list[dict[str, object]]:
        """What saving new would do to the running connections, decided as apply() decides
        it but without doing it: the ones set up again or stopped, each with the clients
        that have to connect again. Connections that only start are left out."""
        found: list[dict[str, object]] = []
        if not self.uses_custom and new.settings.source != "custom":  # the own file: its page
            after = blocks(self._for_ser2net(new))
            for alias in sorted(changed(self._written, after)):
                if alias not in self._written:
                    continue
                port = self.status.get(alias)
                clients = [
                    cl for cl in (port.clients if port else []) if cl.address not in self.internal
                ]
                found.append(
                    {
                        "name": self._names(alias)[1],
                        "effect": "restart" if alias in after else "stop",
                        "clients": len(clients),
                    }
                )
        listen = new.settings.access
        wanted = {c.id: c for c in new.proxied if c.enabled}
        for connection_id, proxy in self.proxies.items():
            c = wanted.get(connection_id)
            if (
                c is not None
                and proxy.key == PROXIED[c.kind].restart_key(c, listen)
                and bool(self._serves(c, new)) == bool(getattr(proxy, "serves", ""))
            ):
                continue
            found.append(
                {
                    "name": proxy.c.name if c is None else c.name,
                    "effect": "stop" if c is None else "restart",
                    "clients": len(proxy.clients),
                }
            )
        return found

    async def check_custom(self, text: str) -> custom.CustomCheck:
        """The file as it is, and the ports the app's proxies hold already (in a thread: a
        large file must not stop the proxies)."""
        ports = {c.port: c.name for c in self.config.proxied if c.enabled}
        return await asyncio.to_thread(custom.check, text, ports)

    async def save_custom(self, text: str, *, use: bool) -> ApplyResult:
        """Save the user's own ser2net.yaml; with use=True switch to it."""
        check = await self.check_custom(text)
        if not check.ok:
            raise CustomError(check)

        def build(config: AppConfig) -> AppConfig:
            # in turn with other changes: the file and the settings as they are by then
            self.custom_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.custom_file.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.custom_file)
            if not use:
                return config
            return replace(config, settings=replace(config.settings, source="custom"))

        result = await self.apply(build, "custom")
        self.events.emit("info", "custom_saved", connections=len(check.connections))
        return result

    # import

    async def preview(self, text: str) -> tuple[ImportResult, dict[str, dict[str, str]]]:
        """What an import would bring, and the existing connections each item collides with."""
        result = await asyncio.to_thread(read, text)  # a large file must not stop the proxies
        # also with an item before it in the same file (two ports on one serial device)
        seen, found = list(self.config.connections), {}
        for item in result.items:
            found[item.alias] = conflicts(AppConfig(connections=tuple(seen)), item)
            if item.connection is not None:
                seen.append(item.connection)
        return result, found

    async def imported(
        self,
        text: str,
        *,
        replace_all: bool,
        take: set[str] | None = None,
        on_conflict: dict[str, str] | None = None,
    ) -> AppConfig:
        """The configuration an import would make, without saving it (as run_import builds it)."""
        result = await asyncio.to_thread(read, text)
        wanted = take if take is not None else {i.alias for i in result.items if i.connection}
        return merge(
            self.config, result, replace_all=replace_all, take=wanted, on_conflict=on_conflict or {}
        )

    async def run_import(
        self,
        text: str,
        *,
        replace_all: bool,
        take: set[str] | None = None,
        on_conflict: dict[str, str] | None = None,
    ) -> ApplyResult:
        result = await asyncio.to_thread(read, text)
        wanted = take if take is not None else {i.alias for i in result.items if i.connection}
        built: list[AppConfig] = []

        def build(config: AppConfig) -> AppConfig:
            merged = merge(
                config, result, replace_all=replace_all, take=wanted, on_conflict=on_conflict or {}
            )
            built.append(merged)
            return merged

        before = {c.id: c for c in self.config.connections}
        applied = await self.apply(build, "import")
        # added, or replaced (a replacing item keeps the old id): taken over either way
        taken = [c for c in built[-1].connections if before.get(c.id) != c]
        self.events.emit(
            "info",
            "imported",
            taken=len(taken),
            skipped=len(result.items) - len(taken),
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
            result, collisions = await self.preview(text)
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
            self.known_clients.touch(address, name)
            self.sessions.disconnected(address, connection_id or alias)
        event = "client_connected" if kind == "new connection" else "client_disconnected"
        self.events.emit("info", event, connection=connection_id, name=name, address=address)
        if event == "client_connected":
            self._client_seen(connection_id, name, address)
            if self._on_the_list(address):
                self.sessions.connected(address, connection_id or alias, name)

    def _on_the_list(self, address: str) -> bool:
        """A host the card Clients can show; a scan of the network does not fill the history."""
        host = plain_host(host_of(address))
        known = self.known_clients
        return host in known.known or host in known.new or is_local(host, self.lan_ip)

    def _client_seen(self, connection_id: str | None, name: str, address: str) -> None:
        names = parse_names(self.config.settings.client_names)
        if self.known_clients.seen(address, name, names, self.lan_ip):
            self.events.emit(
                "warning", "client_new", connection=connection_id, name=name, address=address
            )

    def acknowledge_client(self, host: str) -> bool:
        return self.known_clients.acknowledge(host)

    async def block_client(self, host: str) -> bool:
        """Keep this host out of every connection; its clients are disconnected at once. With
        ser2net all clients of a connection reconnect: it cannot drop a single one. True when
        the block does not reach serial ports: those of the own ser2net.yaml, which ser2net
        gets as it is."""
        host = plain_host(host)
        try:
            ipaddress.ip_address(host)
        except ValueError:
            raise ValueError("an IP address") from None
        if is_local(host, self.lan_ip) or own_address(host):
            raise ValueError("Home Assistant, its apps and this host cannot be blocked")
        if any(host == only for only, _ in self.exclusive.values()):
            raise ValueError("this host is in maintenance")
        serial_unaffected = self.uses_custom and bool(self._written)
        if not self.known_clients.block(host):
            return serial_unaffected
        for proxy in self.proxies.values():
            proxy.disconnect_host(host)
        await self._apply_ser2net()
        kind = "client_blocked_not_custom" if serial_unaffected else "client_blocked"
        self.events.emit("info", kind, address=host)
        return serial_unaffected

    async def unblock_client(self, host: str) -> bool:
        if not self.known_clients.unblock(host):
            return False
        await self._apply_ser2net()
        self.events.emit("info", "client_unblocked", address=host)
        return True

    def _ser2net_ended(self, code: int | None, delay: float) -> None:
        if error := self.ser2net.start_error:
            self.events.emit("error", "ser2net_start_failed", error=error, delay=delay)
        else:
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

    # the app's proxies (kinds.py)

    async def _reconcile_proxies(self) -> list[str]:
        """Start, restart and stop the proxies to match the configuration; the names of
        the connections that were (re)started or stopped."""
        listen = self.config.settings.access
        wanted = {c.id: c for c in self.config.proxied if c.enabled}
        touched: list[str] = []
        for connection_id, proxy in list(self.proxies.items()):
            c = wanted.get(connection_id)
            if (
                c is not None
                and proxy.key == PROXIED[c.kind].restart_key(c, listen)
                and bool(self._serves(c)) == bool(getattr(proxy, "serves", ""))
            ):
                proxy.c = c  # name, trace or notifications changed: no restart
                if isinstance(proxy, EnOceanProxy):
                    proxy.serves = self._serves(c)
                continue
            if isinstance(proxy, EnOceanProxy):
                self._capture_ends(proxy)
            task = self._proxy_tasks.pop(connection_id)
            self._proxy_failed.pop(connection_id, None)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)  # frees the port
            del self.proxies[connection_id]
            touched.append(proxy.c.name if c is None else c.name)
        for connection_id, c in wanted.items():
            if connection_id in self.proxies:
                continue
            build = PROXIED[c.kind].build
            proxy = build(c, listen, self._proxy_event(connection_id), self._proxy_trace(c))
            proxy.only = (
                self.exclusive[connection_id][0] if connection_id in self.exclusive else None
            )
            proxy.refuse = self.known_clients.refused
            if isinstance(proxy, ModbusProxy):
                proxy.router = self._modbus_proxy
            if isinstance(proxy, EnOceanProxy):
                proxy.serves = self._serves(c)  # a fallback: no port of its own
            self.proxies[connection_id] = proxy
            task = asyncio.create_task(proxy.run())
            task.add_done_callback(partial(self._proxy_ended, connection_id))
            self._proxy_tasks[connection_id] = task
            if c.name not in touched:
                touched.append(c.name)
        self._wire_fallbacks()
        return touched

    def _serves(self, c: Connection, config: AppConfig | None = None) -> str:
        """The name of the gateway this EnOcean connection is the fallback of, or ""."""
        main = (config or self.config).fallback_of(c.id) if c.kind == "enocean" else None
        return main.name if main is not None else ""

    def _wire_fallbacks(self) -> None:
        """Attach each EnOcean gateway's fallback proxy (again after either restarted)."""
        for proxy in self.proxies.values():
            if not isinstance(proxy, EnOceanProxy) or proxy.serves:
                continue
            fallback = self.proxies.get(proxy.c.fallback) if proxy.c.fallback else None
            proxy.attach_fallback(fallback if isinstance(fallback, EnOceanProxy) else None)
            known = self.config.connection(proxy.c.fallback) if proxy.c.fallback else None
            proxy.fallback_label = known.name if known is not None else ""

    def _proxy_ended(self, connection_id: str, task: asyncio.Task[None]) -> None:
        if not task.cancelled() and (err := task.exception()) is not None:
            _LOGGER.error("Proxy ended, starts again in %d s", PROXY_RESTART, exc_info=err)
            self._proxy_failed[connection_id] = time.monotonic()
            c = self.config.connection(connection_id)
            self.events.emit(
                "error",
                "proxy_failed",
                connection=connection_id,
                name=c.name if c else connection_id,
                error=str(err) or type(err).__name__,
                delay=PROXY_RESTART,
            )

    async def _restart_failed(self) -> None:
        """Start a proxy again that an unexpected error has ended."""
        now = time.monotonic()
        due = [i for i, at in self._proxy_failed.items() if now - at >= PROXY_RESTART]
        if not due:
            return
        async with self._lock:
            for connection_id in due:
                self._proxy_failed.pop(connection_id, None)
                task = self._proxy_tasks.get(connection_id)
                if task is None or not task.done():
                    continue
                del self._proxy_tasks[connection_id]
                proxy = self.proxies.pop(connection_id)
                if isinstance(proxy, EnOceanProxy):
                    self._capture_ends(proxy)
            await self._reconcile_proxies()
            for connection_id in due:
                if connection_id in self.proxies and (c := self.config.connection(connection_id)):
                    self.events.emit(
                        "info", "proxy_restarted", connection=connection_id, name=c.name
                    )

    def _proxy_event(self, connection_id: str) -> Callable[..., None]:
        def emit(level: str, kind: str, **params: object) -> None:
            c = self.config.connection(connection_id)
            name = c.name if c else connection_id
            to_client, from_client = (
                params.pop("bytes_to_client", None),
                params.pop("bytes_from_client", None),
            )
            self.events.emit(level, kind, connection=connection_id, name=name, **params)
            address = str(params.get("address", ""))
            if kind == "client_connected":
                self._client_seen(connection_id, name, address)
                if self._on_the_list(address):
                    self.sessions.connected(address, connection_id, name)
            elif kind == "client_disconnected":
                self.known_clients.touch(address, name)
                self.sessions.disconnected(
                    address,
                    connection_id,
                    to_client if isinstance(to_client, int) else None,
                    from_client if isinstance(from_client, int) else None,
                )
            elif kind in REFUSED_REASONS and self._on_the_list(address):
                self.sessions.refused(address, connection_id, name, REFUSED_REASONS[kind])

        return emit

    def _proxy_trace(self, c: Connection) -> Callable[[Chunk], None]:
        def feed(chunk: Chunk) -> None:
            self.trace.feed(c.alias, chunk)

        return feed

    def _capture_ends(self, proxy: EnOceanProxy) -> None:
        capture = self.captures.current
        if capture is not None and capture.connection == proxy.c.id:
            self.stop_capture()

    async def _proxy_tick(self) -> None:
        for connection_id, (_, until) in list(self.exclusive.items()):
            if time.time() >= until or self.config.connection(connection_id) is None:
                await self.end_exclusive(connection_id, "expired")
        now = time.monotonic()
        for proxy in self.proxies.values():
            s = proxy.stats
            self._rate(proxy.c.alias, s.bytes_from_device, s.bytes_to_device, now)
        await self._restart_failed()
        await self.enocean_ha.retry()
        down = [
            p.c.name
            for p in self.proxies.values()
            if isinstance(p, EnOceanProxy) and not p.listening and not p.serves
        ]
        with contextlib.suppress(OSError):  # only the Docker health check reads it
            health.write(down, self.health_file)

    # devices

    def check_devices(self) -> None:
        prints = dict(self.prints)
        for c in self.with_device:
            if not c.enabled:
                self.present.pop(c.id, None)
                continue
            present = os.path.exists(c.device)
            before = self.present.get(c.id)
            self.present[c.id] = present
            device = device_for(c.device, self.devices) if present else None
            if device is not None and (print_ := fingerprint(device)):
                prints[c.id] = print_
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
        self._save_prints(prints)

    def _save_prints(self, prints: dict[str, dict[str, str]]) -> None:
        prints = {k: v for k, v in prints.items() if self.config.connection(k)}
        if prints == self.prints:
            return
        self.prints = prints
        try:
            self.prints_file.write_text(json.dumps(prints), encoding="utf-8")
        except OSError as err:
            _LOGGER.debug("Adapters not saved: %s", err)

    def moved_to(self, c: Connection) -> list[dict[str, object]]:
        """A missing device's adapter plugged in elsewhere: the free adapters it may be."""
        print_ = self.prints.get(c.id)
        if not c.uses_device or self.present.get(c.id) is not False or not print_:
            return []
        paths = [o.device for o in self.config.connections if o.uses_device]
        used = {*paths, *(os.path.realpath(p) for p in paths)}
        return [d.to_dict() for d in moved(print_, self.devices, used)]

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

    def _file_names(self) -> dict[str, str]:
        """Connection id → the name of its recording files, for every connection: numbered in
        the order of the configuration, so switching one off or on does not hand its name
        ("pump_1") to another of the same name ("Pump-1" is "pump_1_2"), whose recordings would
        then end up among its files, and the oldest of them deleted."""
        taken: set[str] = set()
        return {c.id: readable_alias(c.name, taken) for c in self.config.connections}

    def _trace_names(self) -> list[tuple[Connection, str]]:
        """Enabled connection → the name of its recording files."""
        names = self._file_names()
        return [(c, names[c.id]) for c in self.active + self.config.proxied if c.enabled]

    def _trace_files(self) -> list[dict[str, object]]:
        """The recordings, each with the connection it belongs to (if it still exists)."""
        owner = {name: connection_id for connection_id, name in self._file_names().items()}
        return [
            {**f, "connection": owner.get(recording_stem(str(f["name"])))}
            for f in self.trace.files()
        ]

    async def _trace_tick(self) -> None:
        settings = self.config.settings
        aliases = {c.alias: (name, c.trace) for c, name in self._trace_names()}
        await self.trace.poll(aliases, settings.trace_file_mb << 20, settings.trace_keep)

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
        # clients ser2net dropped without a word (a restart): no entry stays for ever
        live = {(p.alias, cl.address) for p in ports for cl in p.clients}
        recent = time.time() - 60  # just connected, maybe not in this answer yet
        self.client_since = {
            k: since for k, since in self.client_since.items() if k in live or since > recent
        }
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
        if not self._running:
            return  # a change saved before start(): start() starts MQTT with it
        self.mqtt = HaBridge(self)
        self._mqtt_task = asyncio.create_task(self.mqtt.run(self._stop))

    async def _restart_mqtt(self) -> None:
        if self._mqtt_task is not None and not self._mqtt_task.done():
            keep = set(HaBridge(self).configs()) if self.config.settings.mqtt_enabled else set()
            try:
                await asyncio.wait_for(self.mqtt.clear(keep), 5)
            except Exception as err:  # the broker is away: the next start clears what it can
                _LOGGER.info("MQTT: old entities not cleared: %s", err)
        if self._mqtt_task is not None:
            self._mqtt_task.cancel()
            try:
                await self._mqtt_task
            except asyncio.CancelledError:
                pass
            except Exception:  # how the old one ended must not stop the new settings
                _LOGGER.exception("MQTT had stopped with an error")
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
        reasons = REASONS[settings.notify_language]
        found: dict[str, tuple[str, str]] = {}

        def add(key: str, kind: str, **values: object) -> None:
            title, message = texts[kind]
            found[key] = (title.format(**values), message.format(**values))

        def clock(ts: float) -> str:
            return time.strftime("%d.%m. %H:%M", time.localtime(ts))

        if settings.notify_new_clients and len(self.known_clients.new) > NOTIFY_EACH_CLIENT:
            add("device_proxy_new_clients", "new_clients", count=len(self.known_clients.new))
        elif settings.notify_new_clients:
            for host, entry in self.known_clients.new.items():
                add(
                    f"device_proxy_client_{re.sub(r'[^0-9a-f]', '_', host.lower())}",
                    "new_client",
                    host=host,
                    address=entry.get("address", host),
                    name=entry.get("connection", "?"),
                    since=clock(float(str(entry.get("first", now)))),
                )

        for c in self.config.proxied:
            proxy = self.proxies.get(c.id)
            if proxy is None:
                continue
            missing = c.uses_device and self.present.get(c.id) is False
            if c.notify_missing and (since := self._lasting(c.id, "missing", missing, now)):
                add(
                    f"device_proxy_{c.id}_missing",
                    "missing",
                    name=c.name,
                    device=c.device,
                    since=clock(since),
                )
            fallback = proxy.fallback_info() if isinstance(proxy, EnOceanProxy) else None
            # running on the fallback: that notification says it, with the reason
            down = not missing and proxy.reachable is False
            down = down and not (fallback and fallback["active"] == "fallback")
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
            if isinstance(proxy, EnOceanProxy):
                share = proxy.duty_cycle()["of_limit"]
                if share >= DUTY_NOTE:
                    add(f"device_proxy_{c.id}_duty", "duty", name=c.name, share=round(share))
            if fallback and fallback["active"] == "fallback":
                add(
                    f"device_proxy_{c.id}_fallback",
                    "fallback",
                    name=c.name,
                    fallback=fallback["name"] or "?",
                    reason=reasons.get(fallback["reason"], fallback["reason"]),
                    since=clock(fallback["active_since"]),
                )
            elif fallback and not fallback["ready"] and c.notify_missing:
                add(
                    f"device_proxy_{c.id}_fallback_unready",
                    "fallback_unready",
                    name=c.name,
                    fallback=fallback["name"] or "?",
                    reason=reasons.get(fallback["not_ready"], fallback["not_ready"]),
                )
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
            quiet_since = self._quiet_since(c, device_open, now)
            if c.silence_minutes and quiet_since is not None:
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

    def _quiet_since(self, c: Connection, device_open: bool, now: float) -> float | None:
        """Since when the open device has sent nothing (None while it is closed)."""
        opened = self._lasting(c.id, "open", device_open, now)
        if opened is None:
            return None
        flow = self.trace.flow.get(c.alias)
        last = flow.last_rx if flow and flow.last_rx else None
        return max(last or opened, opened)

    async def _notify_tick(self) -> None:
        settings = self.config.settings
        await self.notifier.update(
            self.problems(),
            grace=settings.notify_grace,
            dismiss=settings.notify_dismiss,
            service=settings.notify_service,
            resolved_message=settings.notify_resolved,
            language=settings.notify_language,
        )

    # tools

    def analyze(self, connection_id: str) -> dict[str, object]:
        """What the device sent in the last seconds, read as a smart meter (SML or D0)."""
        return self.meter(connection_id).to_dict()

    def meter(self, connection_id: str) -> Analysis:
        c = self.config.connection(connection_id)
        if c is None:
            return Analysis()
        cutoff = time.time() - ANALYZE_SECONDS
        data = b"".join(
            ch.data
            for ch in self.trace.live.get(c.alias, ())
            if ch.direction == "rx" and ch.ts >= cutoff
        )
        return analyze(data)

    async def modbus_read(
        self, connection_id: str, unit: int, function: int, address: int, count: int
    ) -> dict[str, object]:
        """Read registers or coils through a Modbus connection's proxy (in turn with the
        clients)."""
        proxy = self._modbus(connection_id)
        limit = 125 if function in (3, 4) else 2000
        if function not in (1, 2, 3, 4) or not 1 <= count <= limit:
            raise ValueError(f"function 1 to 4, 1 to {limit} values")
        if not 1 <= unit <= 255 or not 0 <= address <= 65535 or address + count > 65536:
            raise ValueError("unit 1 to 255, address 0 to 65535")
        started = time.monotonic()
        answer = await proxy.ask(unit, struct.pack(">BHH", function, address, count))
        result = read_result(function, count, answer)
        return {**result, "time_ms": round((time.monotonic() - started) * 1000, 1)}

    async def modbus_write(
        self, connection_id: str, unit: int, function: int, address: int, values: list[int]
    ) -> dict[str, object]:
        """Write coils or registers through a Modbus connection's proxy, then read them back.
        A connection whose write access is "none" stays locked for the tool too."""
        proxy = self._modbus(connection_id)
        if proxy.c.write_access == "none":
            raise ValueError("writing is locked for this connection")
        if not 1 <= unit <= 255:
            raise ValueError("unit 1 to 255")
        pdu = write_pdu(function, address, values)
        started = time.monotonic()
        answer = await proxy.ask(unit, pdu)
        time_ms = round((time.monotonic() - started) * 1000, 1)
        if not answer or answer[0] & 0x80:
            code = answer[1] if answer and len(answer) > 1 else None
            result: dict[str, object] = {"ok": False, "exception": code, "time_ms": time_ms}
        else:
            result = {"ok": True, "time_ms": time_ms}
        self.events.emit(
            "info" if result["ok"] else "warning",
            "tool_write" if result["ok"] else "tool_write_failed",
            connection=connection_id,
            unit=unit,
            function=function,
            address=address,
            values=" ".join(str(v) for v in values[:8]) + (" …" if len(values) > 8 else ""),
        )
        if result["ok"]:
            back = await proxy.ask(
                unit,
                struct.pack(">BHH", 1 if function in (5, 15) else 3, address, len(values)),
            )
            result["readback"] = read_result(1 if function in (5, 15) else 3, len(values), back)
        return result

    def start_scan(self, connection_id: str, first: int, last: int, timeout_ms: int) -> str:
        """Find the unit ids that answer, e.g. on an RS485 bus."""
        proxy = self._modbus(connection_id)
        if not 1 <= first <= last <= 247 or not 50 <= timeout_ms <= 5000:
            raise ValueError("units 1 to 247, timeout 50 to 5000 ms")
        job_id = self._new_job(connection_id, last - first + 1)
        self._spawn(job_id, self._scan(job_id, proxy, range(first, last + 1), timeout_ms / 1000))
        return job_id

    def _enocean(self, connection_id: str) -> EnOceanProxy:
        proxy = self.proxies.get(connection_id)
        if not isinstance(proxy, EnOceanProxy):
            raise ValueError("the connection is not active")
        return proxy

    def testcase(self, connection_id: str, anonymised: bool) -> dict[str, Any]:
        """The connection's last frames as a test case (testcase.py)."""
        c = self.config.connection(connection_id)
        if c is None:
            raise ValueError("no such connection")
        proxy = self.proxies.get(connection_id)
        base_id = proxy.base_id or proxy.known_base_id if isinstance(proxy, EnOceanProxy) else None
        chunks = list(self.trace.live.get(c.alias, ()))
        return testcase.build(c, chunks, base_id=base_id, anonymised=anonymised)

    def enocean_senders(self, connection_id: str) -> list[dict[str, Any]]:
        names = parse_sender_names(self.config.settings.sender_names)
        return [
            {**row, "name": names.get(row["id"], "")}
            for row in self._enocean(connection_id).senders_list()
        ]

    async def enocean_send(self, connection_id: str, text: str) -> dict[str, object]:
        """Send one frame as the app; the gateway's answer, if the frame expects one."""
        proxy = sendable(self._enocean(connection_id))
        frame = parse_frame(proxy.protocol, text)
        answer = await proxy.request(frame)
        return {
            "sent": frame.hex(" ").upper(),
            "answer": answer.hex(" ").upper() if answer else None,
        }

    async def enocean_test(self, connection_id: str, count: int) -> dict[str, object]:
        if not 1 <= count <= 100:
            raise ValueError("count: 1 to 100")
        return await sendable(self._enocean(connection_id)).gateway_test(count)

    async def enocean_base_id(self, connection_id: str, text: str) -> dict[str, object]:
        """Change the gateway's base ID; the answer and the base ID read back."""
        proxy = sendable(self._enocean(connection_id))
        raw = esp.parse_base_id(text)
        result = await proxy.set_base_id(raw)
        self.events.emit(
            "info" if result == "ok" else "warning",
            "base_id_set" if result == "ok" else "base_id_failed",
            connection=proxy.c.id,
            base_id=raw.hex("-").upper(),
            result=result,
        )
        return {
            "result": result,
            "base_id": proxy.base_id,
            "writes_left": proxy.base_id_writes_left,
        }

    async def disconnect_clients(self, connection_id: str, source: str) -> int:
        """Close the connections of all clients of a connection; they may connect again."""
        c = self.config.connection(connection_id)
        if c is None or not c.enabled:
            raise ValueError("the connection is not active")
        proxy = self.proxies.get(connection_id)
        if proxy is not None:
            count = proxy.disconnect_clients()
        elif c.kind == "serial" and not self.uses_custom:
            ports = await self.admin.showport(c.alias)
            count = sum(len(p.clients) for p in ports)
            if count:
                await self.admin.disconnect(c.alias)
        else:
            raise ValueError("the connection is not active")
        self.events.emit(
            "info", "clients_disconnected", connection=c.id, name=c.name, count=count, by=source
        )
        return count

    # restarting a connection, also with a USB reset of its adapter

    async def restart_connection(
        self, connection_id: str, source: str, *, usb: bool = False, power: bool = False
    ) -> dict[str, object]:
        """Close the connection's device or proxy and open it again, e.g. for a hanging
        stick; with usb, the adapter is reset in between, as if unplugged; with power, the
        connection's switch in Home Assistant cuts the power for a moment. The clients are
        disconnected and may connect again."""
        c = self.config.connection(connection_id)
        if c is None or not c.enabled:
            raise ValueError("the connection is not active")
        if c.kind == "serial" and self.uses_custom:
            raise ValueError("not with an own ser2net.yaml")
        if connection_id in self._paused:
            raise ValueError("a tool or a restart is using the connection right now")
        if usb:
            if not c.uses_device:
                raise ValueError("a USB reset needs a device of this host")
            await asyncio.to_thread(usb_node, c.device)  # ValueError: not there, not USB
        if power and not c.power_switch:
            raise ValueError("the connection has no power switch")
        result: dict[str, object] = {"usb": None, "usb_error": None}
        if c.kind == "serial":
            await self._restart_port(c, usb, result, power)
        else:
            await self._restart_proxy(c, usb, result, power)
        self.events.emit(
            "warning" if source == "auto" else "info",  # by itself: something was wrong
            "connection_restarted",
            connection=c.id,
            name=c.name,
            by=source,
            usb=str(result["usb"] or ""),
        )
        if result["usb_error"]:
            self.events.emit(
                "warning",
                "usb_reset_failed",
                connection=c.id,
                name=c.name,
                error=str(result["usb_error"]),
            )
        return result

    async def _restart_port(
        self, c: Connection, usb: bool, result: dict[str, object], power: bool = False
    ) -> None:
        """ser2net closes the device (and drops the clients) and opens it again."""
        self._paused.add(c.id)
        keeper = self._keepers.pop(c.id, None)
        if keeper is not None:
            keeper.cancel()
            await asyncio.gather(keeper, return_exceptions=True)
        try:
            await self.admin.command(f"setportenable {c.alias} off")
            await asyncio.sleep(0.5)  # let ser2net close the device
            if usb:
                await self._reset_usb(c, result)
            if power:
                await self._power_cycle(c, result)
        except AdminError as err:
            raise ValueError(f"ser2net: {err}") from None
        finally:
            self._paused.discard(c.id)
            current = self.config.connection(c.id)
            if current is not None and current.enabled:
                try:
                    await self.admin.command(f"setportenable {c.alias} on")
                except AdminError as err:
                    _LOGGER.warning("Could not switch %s on again: %s", c.name, err)
            self._reconcile_keepers()

    async def _restart_proxy(
        self, c: Connection, usb: bool, result: dict[str, object], power: bool = False
    ) -> None:
        """The app's proxy stops (closing the device and the clients) and starts again."""
        async with self._lock:
            proxy = self.proxies.get(c.id)
            task = self._proxy_tasks.pop(c.id, None)
            if proxy is None or task is None:
                raise ValueError("the connection is not active")
            self._paused.add(c.id)
            try:
                if isinstance(proxy, EnOceanProxy):
                    self._capture_ends(proxy)
                self._proxy_failed.pop(c.id, None)
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)  # frees device and port
                del self.proxies[c.id]
                if usb:
                    await self._reset_usb(c, result)
                if power:
                    await self._power_cycle(c, result)
            finally:
                self._paused.discard(c.id)
                await self._reconcile_proxies()

    async def _reset_usb(self, c: Connection, result: dict[str, object]) -> None:
        """USB reset of the connection's adapter; waits until its device is back."""
        try:
            result["usb"] = await asyncio.to_thread(usb_reset, c.device)
        except (OSError, ValueError) as err:
            result["usb_error"] = str(err)
            _LOGGER.warning("USB reset of %s failed: %s", c.name, err)
            return
        await asyncio.sleep(1)  # the adapter goes away first
        deadline = time.monotonic() + USB_BACK
        while not os.path.exists(c.device) and time.monotonic() < deadline:
            await asyncio.sleep(0.5)
        self.devices = await asyncio.to_thread(scan)

    async def _power_cycle(self, c: Connection, result: dict[str, object]) -> None:
        """The connection's switch in Home Assistant off, a few seconds, on again; then waits
        for a device of this host. Whatever happens, the switch is asked to come back on."""
        try:
            await asyncio.to_thread(set_switch, c.power_switch, False)
        except (OSError, ValueError) as err:
            self._power_failed(c, result, err)
            return
        result["power"] = c.power_switch
        try:
            await asyncio.sleep(POWER_OFF)
        except asyncio.CancelledError:  # the app stops: the device must not stay off
            with contextlib.suppress(OSError, ValueError):
                set_switch(c.power_switch, True)
            raise
        for attempt in range(POWER_ON_TRIES):
            try:
                await asyncio.to_thread(set_switch, c.power_switch, True)
                break
            except (OSError, ValueError) as err:
                if attempt == POWER_ON_TRIES - 1:
                    self._power_failed(c, result, err)
                    return
                await asyncio.sleep(POWER_RETRY)
        self.events.emit(
            "info", "power_cycled", connection=c.id, name=c.name, switch=c.power_switch
        )
        if c.uses_device:
            deadline = time.monotonic() + POWER_BACK
            while not os.path.exists(c.device) and time.monotonic() < deadline:
                await asyncio.sleep(0.5)
            self.devices = await asyncio.to_thread(scan)

    def _power_failed(self, c: Connection, result: dict[str, object], err: Exception) -> None:
        result["power_error"] = str(err)
        _LOGGER.warning("Power cycle of %s failed: %s", c.name, err)
        self.events.emit(
            "warning",
            "power_cycle_failed",
            connection=c.id,
            name=c.name,
            switch=c.power_switch,
            error=str(err),
        )

    async def _silence_tick(self, now: float | None = None) -> None:
        """Restart the connections that want it after their minutes without data; after
        AUTO_RESTART_MAX restarts in a row without data the power is cycled once, if the
        connection has a switch for that, and then only the warning stays."""
        now = time.time() if now is None else now
        for c in self.active:
            if not (c.enabled and c.silence_minutes and c.silence_restart):
                self._auto.pop(c.id, None)
                continue
            if c.id in self._paused:
                continue
            port = self.status.get(c.alias)
            quiet = self._quiet_since(c, bool(port and port.clients), now)
            # the last restart, restarts in a row, gave up, the power was cycled
            state = self._auto.setdefault(c.id, [0.0, 0, False, False])
            flow = self.trace.flow.get(c.alias)
            if flow and flow.last_rx and flow.last_rx > state[0]:
                state[1], state[2], state[3] = 0, False, False  # data since then: counts anew
            if quiet is None:
                continue
            if now - max(quiet, state[0]) < c.silence_minutes * 60:
                continue
            if state[1] >= AUTO_RESTART_MAX and c.power_switch and not state[3]:
                state[0], state[3] = now, True
                try:
                    await self.restart_connection(c.id, "auto", power=True)
                except ValueError as err:
                    self._auto_restart_failed(c, err)
                continue
            if state[1] >= AUTO_RESTART_MAX:
                if not state[2]:
                    state[2] = True
                    self.events.emit(
                        "warning",
                        "auto_restart_gave_up",
                        connection=c.id,
                        name=c.name,
                        count=state[1],
                    )
                continue
            state[0], state[1] = now, state[1] + 1
            try:
                await self.restart_connection(c.id, "auto", usb=c.silence_restart == "usb")
            except ValueError as err:
                self._auto_restart_failed(c, err)

    def _auto_restart_failed(self, c: Connection, err: Exception) -> None:
        _LOGGER.warning("Automatic restart of %s failed: %s", c.name, err)
        self.events.emit(
            "warning", "auto_restart_failed", connection=c.id, name=c.name, error=str(err)
        )

    # maintenance: one host alone

    def _for_ser2net(self, config: AppConfig) -> AppConfig:
        """ser2net's connections keep the blocked hosts out, and those in maintenance accept
        their one host only."""
        if blocked := list(self.known_clients.blocked):
            for port in config.connections:
                if port.kind == "serial":
                    limit = remaddr_without(port, config.settings.access, blocked)
                    config = config.with_connection(replace(port, remaddr=limit))
        for connection_id, (host, _) in self.exclusive.items():
            c = config.connection(connection_id)
            if c is not None and c.kind == "serial":
                net = f"{host}/128" if ":" in host else f"{host}/32"
                config = config.with_connection(replace(c, remaddr=net))
        return config

    def _exclusive_info(self, connection_id: str) -> dict[str, object] | None:
        if connection_id not in self.exclusive:
            return None
        host, until = self.exclusive[connection_id]
        return {"host": host, "until": until}

    async def set_exclusive(self, connection_id: str, host: str, minutes: int) -> None:
        """Only this host may use the connection for a while, e.g. a service tool or a
        firmware update; the other clients are disconnected and kept out."""
        c = self.config.connection(connection_id)
        if c is None or not c.enabled:
            raise ValueError("the connection is not active")
        try:
            host = str(ipaddress.ip_address(host))
        except ValueError:
            raise ValueError("an IP address") from None
        if host in self.known_clients.blocked:
            raise ValueError("this host is blocked")
        if not 1 <= minutes <= EXCLUSIVE_MAX:
            raise ValueError(f"1 to {EXCLUSIVE_MAX} minutes")
        if c.kind == "serial" and self.uses_custom:
            raise ValueError("not with an own ser2net.yaml")
        self.exclusive[connection_id] = (host, time.time() + minutes * 60)
        await self._apply_exclusive(connection_id)
        self.events.emit(
            "info", "exclusive_on", connection=c.id, name=c.name, host=host, minutes=minutes
        )

    async def end_exclusive(self, connection_id: str, reason: str = "by_hand") -> bool:
        if self.exclusive.pop(connection_id, None) is None:
            return False
        await self._apply_exclusive(connection_id)
        c = self.config.connection(connection_id)
        self.events.emit(
            "info",
            "exclusive_off",
            connection=connection_id,
            name=c.name if c else connection_id,
            reason=reason,
        )
        return True

    async def _apply_exclusive(self, connection_id: str) -> None:
        host = self.exclusive[connection_id][0] if connection_id in self.exclusive else None
        proxy = self.proxies.get(connection_id)
        if proxy is not None:
            proxy.only = host
            if host:
                proxy.disconnect_clients(keep=host)
            return
        await self._apply_ser2net()

    async def _apply_ser2net(self) -> None:
        async with self._lock:  # a remaddr changes, the clients of that connection reconnect
            before = self._written
            self.write_config()
            touched = changed(before, self._written)
            if touched and self.ser2net.running:
                await self._reload(touched)

    async def press(self, connection_id: str, action: str) -> None:
        """A button of the connection's device in Home Assistant (MQTT)."""
        if action == "disconnect":
            await self.disconnect_clients(connection_id, "mqtt")
        elif action in ("restart", "usb_reset"):
            await self.restart_connection(connection_id, "mqtt", usb=action == "usb_reset")
        elif action == "power_cycle":
            await self.restart_connection(connection_id, "mqtt", power=True)
        elif action in ("to_fallback", "to_main"):
            self.enocean_switch(connection_id, action.removeprefix("to_"))
        else:
            raise ValueError(f"no such button: {action}")

    def enocean_switch(self, connection_id: str, to: str) -> dict[str, object]:
        """Switch a gateway to its fallback or back by hand."""
        proxy = self._enocean(connection_id)
        proxy.switch(to)
        return {"active": proxy.active}

    async def enocean_promote(self, connection_id: str, old: str) -> ApplyResult:
        """The fallback's hardware becomes the gateway's (e.g. the gateway broke): the
        connection keeps its name, port, clients and history; the old hardware goes to the
        fallback's connection, which is then switched off, kept as fallback or deleted."""
        if old not in ("off", "keep", "delete"):
            raise ValueError("old: off, keep or delete")
        swapped: list[tuple[str, str]] = []

        def build(config: AppConfig) -> AppConfig:
            main = config.connection(connection_id)
            fallback = config.connection(main.fallback) if main and main.fallback else None
            if main is None or fallback is None:
                raise ValueError("the gateway has no fallback")
            mine = {f: getattr(main, f) for f in model.GATEWAY_HARDWARE}
            theirs = {f: getattr(fallback, f) for f in model.GATEWAY_HARDWARE}
            config = config.with_connection(replace(main, **theirs))
            config = config.with_connection(
                replace(fallback, **mine, enabled=fallback.enabled and old != "off")
            )
            if old == "delete":
                config = config.without_connection(fallback.id)
            config.validate()
            swapped[:] = [(fallback.upstream, main.upstream)]
            return config

        result = await self.apply(build, "ui")
        new, previous = swapped[0]
        self.events.emit(
            "info",
            "enocean_fallback_promoted",
            connection=connection_id,
            new=new,
            old=previous,
            action=old,
        )
        return result

    def start_capture(self, connection_id: str, exclusive_peer: str | None) -> dict[str, object]:
        proxy = self._enocean(connection_id)
        capture = self.captures.start(proxy, exclusive_peer, self._file_names().get(proxy.c.id))
        self.events.emit(
            "info",
            "capture_locked" if exclusive_peer else "capture_started",
            connection=proxy.c.id,
            name=proxy.c.name,
            file=capture.path.name,
            peer=exclusive_peer,
        )
        return capture.to_dict()

    def stop_capture(self) -> dict[str, object] | None:
        capture = self.captures.stop()
        if capture is None:
            return None
        self.events.emit(
            "info",
            "capture_stopped",
            connection=capture.connection,
            name=capture.name,
            file=capture.path.name,
            frames=capture.frames,
        )
        return capture.to_dict()

    def _capture_full(self, capture: Capture) -> None:
        self.events.emit(
            "warning",
            "capture_full",
            connection=capture.connection,
            name=capture.name,
            file=capture.path.name,
            frames=capture.frames,
        )

    def _capture_failed(self, capture: Capture, error: str) -> None:
        self.events.emit(
            "error",
            "capture_failed",
            connection=capture.connection,
            name=capture.name,
            file=capture.path.name,
            frames=capture.frames,
            error=error,
        )

    def _modbus_proxy(self, connection_id: str) -> ModbusProxy | None:
        """The running proxy of a Modbus connection, for units routed to it."""
        proxy = self.proxies.get(connection_id)
        return proxy if isinstance(proxy, ModbusProxy) else None

    def _modbus(self, connection_id: str) -> ModbusProxy:
        proxy = self.proxies.get(connection_id)
        if not isinstance(proxy, ModbusProxy):
            raise ValueError("the connection is not active")
        return proxy

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

    def _spawn(self, job_id: str, coro: Coroutine[Any, Any, None]) -> None:
        """A tool run in the background, kept referenced until it ends (asyncio holds it
        weakly); an unexpected error ends the run instead of leaving it running forever."""

        async def run() -> None:
            try:
                await coro
            except Exception as err:
                _LOGGER.exception("Tool run failed")
                job = self.jobs.get(job_id)
                if job is not None and job.get("state") == "running":
                    job["state"], job["error"] = "failed", str(err) or type(err).__name__

        task = asyncio.create_task(run())
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
            job["phase"] = "identify"
            for entry in found[:IDENTIFY_MAX]:
                entry.update(
                    await self._identify(proxy, int(str(entry["unit"])), max(timeout, 1.0))
                )
            job["state"] = "done"
        except (OSError, ConnectionError) as err:
            job["state"], job["error"] = "failed", str(err)
        except asyncio.CancelledError:
            job["state"], job["error"] = "failed", "stopped"
            raise

    @staticmethod
    async def _identify(proxy: ModbusProxy, unit: int, timeout: float) -> dict[str, object]:
        """What a unit the scan found says about itself: its device identification and, for
        inverters and meters, the SunSpec common model."""
        info: dict[str, object] = {}
        ident = device_id(await proxy.ask(unit, DEVICE_ID_REQUEST, timeout=timeout, retries=0))
        if ident:
            info["ident"] = ident
        for base in SUNSPEC_BASES:
            mark = await proxy.ask(
                unit, struct.pack(">BHH", 3, base, 2), timeout=timeout, retries=0
            )
            if is_sunspec(mark):
                common = await proxy.ask(
                    unit,
                    struct.pack(">BHH", 3, base + 2, SUNSPEC_COMMON),
                    timeout=timeout,
                    retries=0,
                )
                info["sunspec"] = {"base": base, **sunspec_common(common)}
                break
        return info

    def start_detect(self, connection_id: str) -> str:
        """Find the baud rate of a pushing meter; ser2net lets go of the device meanwhile."""
        c = self.config.connection(connection_id)
        if c is None:
            raise ValueError("no such connection")
        if c.kind != "serial" or not c.uses_device:
            raise ValueError("only for a serial device of this host")
        job_id = self._new_job(connection_id, 0)
        self._spawn(job_id, self._detect(job_id, c))
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
            current = self.config.connection(c.id)  # it may have been switched off meanwhile
            if current is not None and current.enabled:
                try:
                    await self.admin.command(f"setportenable {c.alias} on")
                except AdminError as err:
                    _LOGGER.warning("Could not switch %s on again: %s", c.name, err)
            self._reconcile_keepers()

    # the state for the web interface

    def _client_rows(
        self, connections: list[dict[str, Any]], names: dict[str, str]
    ) -> list[dict[str, object]]:
        """The known hosts for the settings; Home Assistant and the apps only while connected."""
        live: dict[str, str] = {}
        for c in connections:
            for client in c["clients"]:
                live.setdefault(plain_host(host_of(str(client["address"]))), str(c["name"]))
        known = self.known_clients
        rows: list[tuple[tuple[bool, int, int], dict[str, object]]] = []
        for host in {*known.known, *names, *live} - known.blocked.keys() - known.new.keys():
            auto = local_kind(host, self.lan_ip)
            if auto and host not in live:
                continue
            try:
                ip = ipaddress.ip_address(host)
            except ValueError:
                continue  # the app's own clients have no address
            last = known.last.get(host, {})
            row = {
                "host": host,
                "name": names.get(host, ""),
                "auto": auto,
                "connected": host in live,
                "connection": live.get(host) or last.get("connection", ""),
                "last": last.get("time"),
                "first": known.known.get(host),
            }
            rows.append(((auto is not None, ip.version, int(ip)), row))
        return [row for _, row in sorted(rows, key=lambda item: item[0])]

    def snapshot(self) -> dict[str, object]:
        """Everything the status pages show, in one JSON-ready structure."""
        settings = self.config.settings
        client_names = parse_names(settings.client_names)
        attempts = self.known_clients.attempts
        connections = []
        for c in self.config.connections:
            if c.kind in PROXIED:
                connections.append(self._proxy_snapshot(c))
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
                    "moved_to": self.moved_to(c),
                    "exclusive": self._exclusive_info(c.id),
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
            "settings": hidden(settings.to_dict(), {"mqtt_password"}, PASSWORD_KEPT),
            "lan_ip": self.lan_ip,
            "lan_net": self.lan_net,
            "new_clients": [{"host": h, **entry} for h, entry in self.known_clients.new.items()],
            "new_clients_full": self.known_clients.new_full,
            "known_clients": self._client_rows(connections, client_names),
            "blocked_clients": [
                {
                    "host": h,
                    "since": since,
                    "name": client_names.get(h),
                    "refused": attempt.count if (attempt := attempts.get(h)) else 0,
                    "refused_last": attempt.last if attempt else None,
                }
                for h, since in self.known_clients.blocked.items()
            ],
            "connections": connections,
            "custom_ports": [
                {"alias": p.alias, "clients": [cl.address for cl in p.clients]}
                for p in self.status.values()
            ]
            if self.uses_custom
            else [],
            "devices": [{**d.to_dict(), "used_by": used.get(d.tty)} for d in self.devices],
            "trace_files": self._trace_files(),
            "mqtt": self.mqtt.state,
            "capture": self.captures.current.to_dict() if self.captures.current else None,
            "enocean_status": self.enocean_ha.state(),
            "last_change": self.last_change,
        }

    def working(self, c: Connection) -> bool:
        """Does the connection do its job right now: open port, device there and reachable."""
        if not c.enabled or (c.uses_device and self.present.get(c.id) is False):
            return False
        if c.kind in PROXIED:
            proxy = self.proxies.get(c.id)
            serves = bool(getattr(proxy, "serves", ""))  # a fallback gateway: no port of its own
            return bool(proxy and (proxy.listening or serves) and proxy.reachable is not False)
        port = self.status.get(c.alias)
        return not self.uses_custom and self.ser2net.running and bool(port and port.enabled)

    def _proxy_snapshot(self, c: Connection) -> dict[str, object]:
        """A proxied connection; its proxy's state() under the kind's name ("modbus": ...)."""
        kind = PROXIED[c.kind]
        proxy = self.proxies.get(c.id)
        flow = self.trace.flow.get(c.alias)
        rate = self.rates.get(c.alias)
        present = self.present.get(c.id) if c.uses_device else None
        device = device_for(c.device, self.devices) if present else None
        state = proxy.state() if proxy else None
        return {
            **c.to_dict(),
            "alias": c.alias,
            "present": present,
            "tty": device.tty if device else None,
            "usb": device.to_dict() if device else None,
            "running": bool(proxy and (proxy.listening or getattr(proxy, "serves", ""))),
            "pending": None,
            "clients": [kind.client_row(cl) for cl in (proxy.clients.values() if proxy else [])],
            "kept_open": False,
            "bytes_from_device": proxy.stats.bytes_from_device if proxy else 0,
            "bytes_to_device": proxy.stats.bytes_to_device if proxy else 0,
            "rate_from_device": rate[3] if rate else 0.0,
            "rate_to_device": rate[4] if rate else 0.0,
            "last_data": flow.last_rx if flow else None,
            "line_errors": None,
            "moved_to": self.moved_to(c),
            "exclusive": self._exclusive_info(c.id),
            "latency": self.latency.get(c.id),
            "addresses": addresses(c, self.config.settings, self.lan_ip),
            c.kind: state,
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
            address = ""
            try:
                sock.setblocking(False)
                sock.bind((host, 0))
                own = sock.getsockname()
                address = (
                    f"[{own[0]}]:{own[1]}" if family == socket.AF_INET6 else f"{own[0]}:{own[1]}"
                )
                self.internal.add(address)  # before connecting: ser2net reports it at once
                await asyncio.get_running_loop().sock_connect(sock, (host, c.port))
                reader, writer = await asyncio.open_connection(sock=sock)
            except OSError as err:  # also a bind address this host does not have
                sock.close()
                self.internal.discard(address)
                if not failed:
                    failed = True
                    self.events.emit(
                        "warning", "keep_open_failed", connection=c.id, name=c.name, error=str(err)
                    )
                await asyncio.sleep(KEEP_OPEN_RETRY)
                continue
            except BaseException:  # cancelled while connecting
                sock.close()
                self.internal.discard(address)
                raise
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

    async def _sessions_tick(self) -> None:
        live: dict[tuple[str, str], tuple[int, int]] = {}
        for alias, port in self.status.items():
            connection = self._names(alias)[0] or alias
            for cl in port.clients:
                if cl.address not in self.internal:
                    live[(connection, cl.address)] = (cl.bytes_to_client, cl.bytes_from_client)
        for connection_id, proxy in self.proxies.items():
            client_row = PROXIED[proxy.c.kind].client_row
            for row in map(client_row, proxy.clients.values()):
                live[(connection_id, row["address"])] = (
                    row["bytes_to_client"],
                    row["bytes_from_client"],
                )
        # without ser2net's answer nobody can say who is gone
        self.sessions.tick(live, check_gone=self.admin.connected.is_set())

    async def _report_problems(self) -> None:
        """What went wrong before the events could say so, or below them."""
        sources: list[Store | KnownClients | Database] = [self.store, self.known_clients]
        if self.events.db is not None:
            sources.append(self.events.db)
        for source in sources:
            found, source.problems = source.problems, []
            for kind, params in found:
                self.events.emit("error", kind, **params)

    async def _housekeeping(self) -> None:
        days = self.config.settings.history_days
        self.sessions.prune(days)
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
