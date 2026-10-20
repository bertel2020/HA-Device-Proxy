"""Ties the app together: configuration, ser2net, its admin socket, devices and events.

Saving a configuration writes ser2net.yaml and makes ser2net reload it. ser2net keeps a
changed connection as it was while clients are connected; those clients (and only those of
the changed connections) are disconnected so the change takes effect, the others stay.

ser2net slows all clients of a connection down when one of them stops reading; a client
whose queue stays full is reported (and its connection's clients disconnected, if set).
ser2net opens a device only while a client is connected; "keep open" makes the app one.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path

from .admin import AdminClient, AdminError, PortStatus
from .config import blocks, changed, render
from .events import EventLog
from .model import AppConfig, Connection
from .process import Ser2Net
from .store import Change, Store, summary

_LOGGER = logging.getLogger(__name__)

DEVICE_POLL = 2  # seconds between device checks
STATUS_POLL = 5  # seconds between status reads from ser2net
HOUSEKEEPING = 6 * 3600  # seconds between history clean-ups
STUCK_BYTES = 4096  # a client with this much waiting ...
STUCK_SECONDS = 30  # ... for this long does not read
KEEP_OPEN_RETRY = 5  # seconds


@dataclass
class ApplyResult:
    changes: list[Change]
    rebuilt: list[str]  # names of the connections ser2net set up again
    disconnected: list[str]  # names of the connections whose clients had to reconnect


@dataclass
class Activity:
    """What the app sees of a connection between status reads."""

    kept_open: bool = False
    bytes_kept: int = 0  # read by the app's own client
    last_data: float = 0.0
    stuck_since: dict[str, float] = field(default_factory=dict)
    stuck_reported: set[str] = field(default_factory=set)


class Controller:
    def __init__(self, store: Store, events: EventLog, config_file: Path) -> None:
        self.store = store
        self.events = events
        self.config_file = config_file
        self.config = store.load()
        self.ser2net = Ser2Net(config_file, on_exit=self._ser2net_ended)
        self.admin = AdminClient(self._admin_event)
        self.present: dict[str, bool] = {}
        self.status: dict[str, PortStatus] = {}  # alias → last status from ser2net
        self.activity: dict[str, Activity] = {}  # connection id → activity
        self.internal: set[str] = set()  # addresses of the app's own clients
        self._keepers: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()
        self._stop = asyncio.Event()

    # configuration

    def write_config(self) -> None:
        text = render(self.config)
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
        c = self._connection(alias)
        return (c.id, c.name) if c else (None, alias)

    async def start(self, stop: asyncio.Event) -> None:
        self._stop = stop
        self.apply_log_level()
        self.write_config()
        active = [c for c in self.config.connections if c.enabled]
        self.events.emit(
            "info", "app_started", connections=len(self.config.connections), active=len(active)
        )
        for c in self.config.connections:
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
        try:
            await asyncio.gather(
                self.ser2net.run(stop),
                self.admin.run(stop),
                self._loop(stop, DEVICE_POLL, self._device_tick),
                self._loop(stop, STATUS_POLL, self.read_status),
                self._loop(stop, HOUSEKEEPING, self._housekeeping),
            )
        finally:
            for task in self._keepers.values():
                task.cancel()

    async def apply(self, new: AppConfig, source: str) -> ApplyResult:
        """Save and use a new configuration (already validated)."""
        async with self._lock:
            old = self.config
            touched = changed(blocks(old), blocks(new))
            items = self.store.save(old, new, source)
            self.config = new
            self.write_config()
            self.apply_log_level()
            disconnected: list[str] = []
            if touched and self.ser2net.running:
                disconnected = await self._reload(touched)
            self._reconcile_keepers()
            names = [c.name for c in new.connections if c.alias in touched]
            names += [
                c.name for c in old.connections if c.alias in touched and not new.connection(c.id)
            ]
            self.events.emit("info", "config_changed", summary=summary(items), changes=items)
            return ApplyResult(items, sorted(names), disconnected)

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
        event = "client_connected" if kind == "new connection" else "client_disconnected"
        self.events.emit("info", event, connection=connection_id, name=name, address=address)

    def _ser2net_ended(self, code: int | None, delay: float) -> None:
        self.events.emit("warning", "ser2net_restart", code=code, delay=delay)

    # devices

    def check_devices(self) -> None:
        for c in self.config.connections:
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
        self.check_devices()
        self.events.flush_bursts()

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
            c = self._connection(port.alias)
            if c is not None:
                await self._check_stuck(c, port, now)

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

    def _reconcile_keepers(self) -> None:
        wanted = {c.id for c in self.config.connections if c.enabled and c.keep_open}
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
