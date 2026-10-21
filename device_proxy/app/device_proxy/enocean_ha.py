"""What Home Assistant's EnOcean Eltako integration gets from the app's EnOcean gateways.

The same contract as the EnOcean Proxy app had, so the integration works with either:

- Supervisor discovery (service "enocean_eltako"): one message lists every active gateway
  with port and protocol, plus the app's host name and status port. The Supervisor keeps one
  message per app and service, so a message per gateway would replace the previous one. It is
  sent again whenever that list changes, and withdrawn when no gateway is left.
- A read-only status on its own port (settings.enocean_status_port, 9199): the integration
  polls GET /api/status for its gateway cards (connected, programs, air time, replay, lock).
  No frames, no actions. The app runs in the host network, so only Home Assistant and the
  other apps may ask (127.0.0.1, 172.30.32.0/23); the LAN is refused.

"app" and "api" tell the integration it is talking to this app; "version" is the app's own.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
import urllib.request
from typing import TYPE_CHECKING, Any

from .enocean import EnOceanProxy, _port
from .model import APPS_NETWORKS, AppConfig, Connection, client_allowed

if TYPE_CHECKING:
    from .controller import Controller

_LOGGER = logging.getLogger(__name__)

API = 1  # the version of this contract
SERVICE = "enocean_eltako"
SUPERVISOR = "http://supervisor"
STATUS_PEERS = ", ".join(APPS_NETWORKS)
MAX_REQUEST = 8192


def gateways(config: AppConfig) -> list[Connection]:
    """The gateways Home Assistant is told about: the active EnOcean connections."""
    return [c for c in config.proxied if c.kind == "enocean" and c.enabled]


def discovery_config(hostname: str, status_port: int, items: list[Connection]) -> dict[str, Any]:
    return {
        "app": "device_proxy",  # the integration names it and may move gateways over to it
        "host": hostname,
        "status_port": status_port,
        "replay": True,
        "gateways": [{"name": c.name, "port": c.port, "protocol": c.esp_protocol} for c in items],
    }


def gateway_status(c: Connection, proxy: EnOceanProxy | None) -> dict[str, Any]:
    """One gateway, with the fields of the EnOcean Proxy app's status."""
    state = proxy.state() if proxy is not None else None
    return {
        "name": c.name,
        "port": c.port,
        "protocol": c.esp_protocol,
        "connected": bool(state and state["connected"]),
        "connected_since": state["connected_since"] if state else None,
        "last_error": (state["last_error"] or None) if state else None,
        "base_id": state["base_id"] if state else None,
        "clients": [
            {"peer": client.host, "replay": client.replay}
            for client in (proxy.clients.values() if proxy is not None else [])
        ],
        "stats": state["frames"] if state else {},
        "queue": state["queue"] if state else 0,
        "replay": state["replay"] if state else None,
        "exclusive_peer": state["exclusive_peer"] if state else None,
        "duty_cycle": state["duty_cycle"] if state else {},
    }


def status(controller: Controller) -> dict[str, Any]:
    items = []
    for c in gateways(controller.config):
        proxy = controller.proxies.get(c.id)
        items.append(gateway_status(c, proxy if isinstance(proxy, EnOceanProxy) else None))
    return {
        "app": "device_proxy",
        "api": API,
        "version": os.environ.get("APP_VERSION", "dev"),
        "now": time.time(),
        "gateways": items,
    }


def _supervisor(path: str, payload: dict[str, Any] | None = None, method: str = "") -> Any:
    request = urllib.request.Request(
        f"{SUPERVISOR}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {os.environ['SUPERVISOR_TOKEN']}",
            "Content-Type": "application/json",
        },
        method=method or ("POST" if payload is not None else "GET"),
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read()
    return json.loads(body) if body else None


class EnOceanHa:
    """Keeps the discovery message and the status server in line with the configuration."""

    def __init__(self, controller: Controller) -> None:
        self.c = controller
        self.port: int | None = None  # where the status server listens
        self.listen_error = ""
        self._server: asyncio.Server | None = None
        self._announced: dict[str, Any] | None = None
        self._uuid: str | None = None  # of the discovery message
        self._hostname: str | None = None

    async def update(self) -> None:
        """After the start and every change of the configuration."""
        config = self.c.config
        settings = config.settings
        items = gateways(config)
        await self._serve(settings.enocean_status_port if items else None)
        if settings.enocean_discovery and items:
            await self._announce(items)
        else:
            await self._withdraw()

    async def stop(self) -> None:
        await self._serve(None)

    # status server

    async def _serve(self, port: int | None) -> None:
        if port == self.port and (self._server is not None or port is None):
            return
        if self._server is not None:
            self._server.close()
            with contextlib.suppress(Exception):
                await self._server.wait_closed()
            self._server = None
        self.port = port
        if port is None:
            return
        try:
            self._server = await asyncio.start_server(self._handle, None, port, reuse_address=True)
            self.listen_error = ""
        except OSError as err:
            self.listen_error = str(err)
            self.c.events.emit(
                "error", "listen_failed", name="EnOcean status", port=port, error=str(err)
            )
            return
        self.port = _port(self._server)  # tests: 0 → a free port

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername") or ("?", 0)
        try:
            if not client_allowed(STATUS_PEERS, "all", str(peer[0])):
                return
            async with asyncio.timeout(5):
                head = await reader.readuntil(b"\r\n\r\n")
            if len(head) > MAX_REQUEST:
                return
            method, path, *_ = head.split(b"\r\n", 1)[0].decode("latin-1").split(" ")
            if method == "GET" and path.split("?")[0].strip("/") == "api/status":
                code, body = "200 OK", json.dumps(status(self.c)).encode()
                kind = "application/json"
            else:
                code, body, kind = "404 Not Found", b"not found", "text/plain"
            writer.write(
                f"HTTP/1.1 {code}\r\nContent-Type: {kind}\r\nContent-Length: {len(body)}\r\n"
                "Connection: close\r\n\r\n".encode()
                + body
            )
            await writer.drain()
        except (OSError, TimeoutError, ValueError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()

    # discovery

    async def _announce(self, items: list[Connection]) -> None:
        if "SUPERVISOR_TOKEN" not in os.environ:
            return
        try:
            if self._hostname is None:
                info = await asyncio.to_thread(_supervisor, "/addons/self/info")
                self._hostname = str(info["data"]["hostname"])
            config = discovery_config(
                self._hostname, self.c.config.settings.enocean_status_port, items
            )
            if config == self._announced:
                return
            answer = await asyncio.to_thread(
                _supervisor, "/discovery", {"service": SERVICE, "config": config}
            )
            self._uuid = (answer or {}).get("data", {}).get("uuid") or self._uuid
            self._announced = config
            _LOGGER.info("Announced %d EnOcean gateway(s) to Home Assistant", len(items))
        except (OSError, KeyError, TypeError, ValueError) as err:
            _LOGGER.warning("Could not announce the EnOcean gateways to Home Assistant: %s", err)

    async def _withdraw(self) -> None:
        if self._uuid is None or "SUPERVISOR_TOKEN" not in os.environ:
            self._announced = None
            return
        try:
            await asyncio.to_thread(_supervisor, f"/discovery/{self._uuid}", None, "DELETE")
            self._uuid = self._announced = None
        except (OSError, ValueError) as err:
            _LOGGER.warning("Could not withdraw the EnOcean discovery: %s", err)
