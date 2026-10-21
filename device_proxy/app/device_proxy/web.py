"""The web interface behind Home Assistant's ingress: the page, its script and a JSON API.

A small HTTP/1.1 server on asyncio (no extra dependency). The app runs in the host network,
so the server binds to the host's address in the Supervisor network (172.30.32.1) when it
can, and only the Supervisor's ingress proxy (172.30.32.2) may talk to it. The page uses
relative URLs, so it works under the ingress path.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field, replace
from importlib import resources
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from . import diagnostics
from .config import block, export
from .controller import Controller, CustomError
from .importer import ReadError
from .model import INGRESS_PORT, AppConfig, Connection, Settings, ValidationError, new_id
from .notify import notify_services

_LOGGER = logging.getLogger(__name__)

INGRESS_HOSTS = ("172.30.32.1", "0.0.0.0")  # the Supervisor network first, else everywhere
INGRESS_PEERS = ("172.30.32.2",)  # the Supervisor's ingress proxy
MAX_HEADER = 16384
MAX_BODY = 4 << 20  # an imported ser2net.yaml
STATIC = {
    "": ("index.html", "text/html; charset=utf-8"),
    "app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class HttpError(Exception):
    def __init__(self, status: int, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.details = details


@dataclass
class Request:
    method: str
    path: str
    query: dict[str, str]
    body: bytes
    params: dict[str, str] = field(default_factory=dict)

    def json(self) -> Any:
        try:
            return json.loads(self.body or b"{}")
        except ValueError:
            raise HttpError(400, "the body is not JSON") from None


@dataclass
class Response:
    status: int = 200
    body: bytes = b""
    content_type: str = "application/json"
    headers: dict[str, str] = field(default_factory=dict)


def ok(data: Any = None, status: int = 200) -> Response:
    return Response(status, json.dumps(data, ensure_ascii=False, default=str).encode())


Handler = Callable[[Request], Awaitable[Response]]


def _number(query: dict[str, str], name: str, default: Any, kind: Callable[[str], Any]) -> Any:
    """A number from the query string; a bad one is the caller's mistake (400)."""
    try:
        return kind(query.get(name) or "") if query.get(name) else default
    except ValueError:
        raise HttpError(400, f"{name} must be a number") from None


REASONS = {
    200: "OK",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    413: "Payload Too Large",
    500: "Internal Server Error",
}


class WebServer:
    def __init__(
        self,
        controller: Controller,
        *,
        port: int = INGRESS_PORT,
        hosts: tuple[str, ...] = INGRESS_HOSTS,
        peers: tuple[str, ...] | None = INGRESS_PEERS,
        version: str = "",
    ) -> None:
        self.c = controller
        self.port = port
        self.hosts = hosts
        self.peers = None if peers is None else set(peers)
        self.version = version
        self.routes: list[tuple[str, re.Pattern[str], Handler]] = []
        self._server: asyncio.Server | None = None
        self._route("GET", r"api/state", self.state)
        self._route("GET", r"api/events", self.events)
        self._route("GET", r"api/history", self.history)
        self._route("GET", r"api/stats", self.stats)
        self._route("GET", r"api/live/(?P<id>[0-9a-f]{8})", self.live)
        self._route("POST", r"api/connections", self.create)
        self._route("PUT", r"api/connections/(?P<id>[0-9a-f]{8})", self.update)
        self._route("DELETE", r"api/connections/(?P<id>[0-9a-f]{8})", self.delete)
        self._route("POST", r"api/connections/(?P<id>[0-9a-f]{8})/enabled", self.enable)
        self._route("POST", r"api/preview", self.preview)
        self._route("PUT", r"api/settings", self.settings)
        self._route("POST", r"api/import/preview", self.import_preview)
        self._route("POST", r"api/import", self.run_import)
        self._route("GET", r"api/export", self.export)
        self._route("GET", r"api/custom", self.get_custom)
        self._route("POST", r"api/custom/check", self.check_custom)
        self._route("PUT", r"api/custom", self.put_custom)
        self._route("GET", r"api/versions", self.versions)
        self._route("GET", r"api/versions/(?P<id>\d+)", self.version_config)
        self._route("POST", r"api/versions/(?P<id>\d+)/restore", self.restore)
        self._route("GET", r"api/trace/(?P<name>[^/]+)", self.trace_file)
        self._route("DELETE", r"api/trace/(?P<name>[^/]+)", self.delete_trace)
        self._route("GET", r"api/tools/(?P<id>[0-9a-f]{8})/meter", self.meter)
        self._route("POST", r"api/tools/(?P<id>[0-9a-f]{8})/detect", self.detect)
        self._route("POST", r"api/tools/(?P<id>[0-9a-f]{8})/modbus/read", self.modbus_read)
        self._route("POST", r"api/tools/(?P<id>[0-9a-f]{8})/modbus/scan", self.modbus_scan)
        self._route("POST", r"api/tools/(?P<id>[0-9a-f]{8})/enocean/send", self.enocean_send)
        self._route("POST", r"api/tools/(?P<id>[0-9a-f]{8})/enocean/test", self.enocean_test)
        self._route("POST", r"api/tools/(?P<id>[0-9a-f]{8})/enocean/capture", self.capture_start)
        self._route("POST", r"api/capture/stop", self.capture_stop)
        self._route("GET", r"api/jobs/(?P<job>[0-9a-f]{8})", self.job)
        self._route("GET", r"api/notify/services", self.notify_services)
        self._route("GET", r"api/diagnostics", self.diagnostics)

    def _route(self, method: str, pattern: str, handler: Handler) -> None:
        self.routes.append((method, re.compile(pattern + "$"), handler))

    async def start(self) -> None:
        for host in self.hosts:
            try:
                self._server = await asyncio.start_server(self._handle, host, self.port)
            except OSError as err:
                _LOGGER.debug("Web interface not on %s: %s", host, err)
                continue
            _LOGGER.info("Web interface on %s:%s", host, self.port)
            return
        _LOGGER.error("Web interface could not start on port %s", self.port)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    # HTTP

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        if self.peers is not None and (not peer or peer[0] not in self.peers):
            writer.close()
            return
        try:
            while True:
                request = await self._read(reader)
                if request is None:
                    break
                response = await self._dispatch(request)
                self._write(writer, response)
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        except HttpError as err:
            self._write(writer, ok({"error": str(err)}, err.status))
        finally:
            writer.close()

    async def _read(self, reader: asyncio.StreamReader) -> Request | None:
        try:
            head = await reader.readuntil(b"\r\n\r\n")
        except asyncio.IncompleteReadError:
            return None
        except asyncio.LimitOverrunError:
            raise HttpError(413, "headers too large") from None
        if len(head) > MAX_HEADER:
            raise HttpError(413, "headers too large")
        lines = head.decode("latin-1").split("\r\n")
        try:
            method, target, _ = lines[0].split(" ", 2)
        except ValueError:
            raise HttpError(400, "bad request line") from None
        headers = {}
        for line in lines[1:]:
            name, sep, value = line.partition(":")
            if sep:
                headers[name.strip().lower()] = value.strip()
        try:
            length = int(headers.get("content-length", "0") or 0)
        except ValueError:
            raise HttpError(400, "bad Content-Length") from None
        if length < 0:
            raise HttpError(400, "bad Content-Length")
        if length > MAX_BODY:
            raise HttpError(413, "body too large")
        body = await reader.readexactly(length) if length else b""
        url = urlsplit(target)
        query = {k: v[-1] for k, v in parse_qs(url.query).items()}
        return Request(method.upper(), unquote(url.path).lstrip("/"), query, body)

    async def _dispatch(self, request: Request) -> Response:
        if request.method == "GET" and request.path in STATIC:
            return self._static(request.path)
        allowed = False
        for method, pattern, handler in self.routes:
            match = pattern.match(request.path)
            if not match:
                continue
            allowed = True
            if method != request.method:
                continue
            request.params = match.groupdict()
            try:
                return await handler(request)
            except HttpError as err:
                return ok({"error": str(err), "details": err.details}, err.status)
            except ValidationError as err:
                return ok({"error": "invalid", "errors": err.errors}, 400)
            except Exception:
                _LOGGER.exception("Web interface: %s %s failed", request.method, request.path)
                return ok({"error": "internal error, see the app log"}, 500)
        return ok({"error": "not allowed" if allowed else "not found"}, 405 if allowed else 404)

    def _static(self, path: str) -> Response:
        name, content_type = STATIC[path]
        body = resources.files(__package__).joinpath("web", name).read_bytes()
        return Response(200, body, content_type, {"Cache-Control": "no-cache"})

    @staticmethod
    def _write(writer: asyncio.StreamWriter, response: Response) -> None:
        reason = REASONS.get(response.status, "OK")
        head = [
            f"HTTP/1.1 {response.status} {reason}",
            f"Content-Type: {response.content_type}",
            f"Content-Length: {len(response.body)}",
            "X-Content-Type-Options: nosniff",
            *(f"{k}: {v}" for k, v in response.headers.items()),
        ]
        writer.write(("\r\n".join(head) + "\r\n\r\n").encode("latin-1") + response.body)

    # API

    async def state(self, request: Request) -> Response:
        data = self.c.snapshot()
        data["version"] = self.version
        data["ser2net_version"] = self.c.ser2net_version
        data["events_seq"] = self.c.events.seq
        return ok(data)

    async def events(self, request: Request) -> Response:
        after = _number(request.query, "after", 0, int)
        return ok([e.to_dict() for e in self.c.events.since(after)])

    async def history(self, request: Request) -> Response:
        events = self.c.events.history(
            connection=request.query.get("connection") or None,
            since=_number(request.query, "since", 0.0, float),
            limit=min(_number(request.query, "limit", 500, int), 5000),
        )
        return ok([e.to_dict() for e in events])

    async def stats(self, request: Request) -> Response:
        days = min(max(_number(request.query, "days", 30, int), 1), 365)
        return ok({"days": days, "connections": self.c.events.stats(days)})

    async def live(self, request: Request) -> Response:
        after = _number(request.query, "after", 0, int)
        chunks = [ch.to_dict() for ch in self.c.live(request.params["id"], limit=400)]
        return ok([ch for ch in chunks if int(str(ch["seq"])) > after])

    def _connection_from(self, data: Any, connection_id: str) -> Connection:
        if not isinstance(data, dict):
            raise HttpError(400, "a connection object is needed")
        return Connection.from_dict({**data, "id": connection_id})

    async def _save(self, build: Callable[[AppConfig], AppConfig], source: str = "ui") -> Response:
        def checked(current: AppConfig) -> AppConfig:
            config = build(current)
            config.validate()
            return config

        result = await self.c.apply(checked, source)
        return ok(asdict(result))

    async def create(self, request: Request) -> Response:
        connection = self._connection_from(request.json().get("connection"), new_id())
        response = await self._save(lambda config: config.with_connection(connection))
        response.body = json.dumps({**json.loads(response.body), "id": connection.id}).encode()
        return response

    async def update(self, request: Request) -> Response:
        connection_id = request.params["id"]
        if self.c.config.connection(connection_id) is None:
            raise HttpError(404, "no such connection")
        connection = self._connection_from(request.json().get("connection"), connection_id)
        return await self._save(lambda config: config.with_connection(connection))

    async def delete(self, request: Request) -> Response:
        connection_id = request.params["id"]
        if self.c.config.connection(connection_id) is None:
            raise HttpError(404, "no such connection")
        return await self._save(lambda config: config.without_connection(connection_id))

    async def enable(self, request: Request) -> Response:
        connection_id = request.params["id"]
        if self.c.config.connection(connection_id) is None:
            raise HttpError(404, "no such connection")
        enabled = bool(request.json().get("enabled"))

        def build(config: AppConfig) -> AppConfig:
            current = config.connection(connection_id)
            if current is None:
                raise HttpError(404, "no such connection")
            return config.with_connection(replace(current, enabled=enabled))

        return await self._save(build)

    async def preview(self, request: Request) -> Response:
        data = request.json().get("connection") or {}
        connection_id = str(data.get("id") or "00000000")
        try:
            connection = self._connection_from(data, connection_id)
        except ValidationError as err:
            return ok({"yaml": "", "errors": err.errors})
        others = self.c.config.without_connection(connection_id).with_connection(connection)
        try:
            others.validate()
            errors: dict[str, str] = {}
        except ValidationError as err:
            index = next(i for i, c in enumerate(others.connections) if c.id == connection_id)
            prefix = f"connections.{index}."
            errors = {k[len(prefix) :]: v for k, v in err.errors.items() if k.startswith(prefix)}
        warnings: dict[str, str] = {}
        if "port" not in errors and (problem := self.c.port_problem(connection)):
            warnings["port"] = problem
        if connection.kind != "serial":  # the app's Modbus proxy, not ser2net
            return ok({"yaml": "", "errors": errors, "warnings": warnings})
        text = block(connection, self.c.config.settings.listen, trace=False)
        return ok({"yaml": text, "errors": errors, "warnings": warnings})

    async def settings(self, request: Request) -> Response:
        data = request.json().get("settings")
        if not isinstance(data, dict):
            raise HttpError(400, "a settings object is needed")
        settings = Settings.from_dict({**self.c.config.settings.to_dict(), **data})
        if settings.source == "custom" and not self.c.custom_file.exists():
            raise HttpError(409, "save your own ser2net.yaml first")
        return await self._save(lambda config: replace(config, settings=settings))

    async def import_preview(self, request: Request) -> Response:
        text = str(request.json().get("text", ""))
        try:
            result, collisions = self.c.preview(text)
        except ReadError as err:
            return ok({"error": "unreadable", "note": err.note}, 400)
        return ok(
            {
                "version": result.version,
                "notes": result.notes,
                "items": [
                    {
                        "alias": item.alias,
                        "connection": item.connection.to_dict() if item.connection else None,
                        "notes": item.notes,
                        "conflicts": collisions.get(item.alias, {}),
                    }
                    for item in result.items
                ],
            }
        )

    async def run_import(self, request: Request) -> Response:
        data = request.json()
        try:
            result = await self.c.run_import(
                str(data.get("text", "")),
                replace_all=bool(data.get("replace_all")),
                take=set(data["take"]) if "take" in data else None,
                on_conflict={str(k): str(v) for k, v in (data.get("on_conflict") or {}).items()},
            )
        except ReadError as err:
            return ok({"error": "unreadable", "note": err.note}, 400)
        return ok(asdict(result))

    async def export(self, request: Request) -> Response:
        text = export(self.c.config, include_disabled=request.query.get("disabled", "1") != "0")
        stamp = time.strftime("%Y%m%d-%H%M")
        return Response(
            200,
            text.encode(),
            "application/x-yaml; charset=utf-8",
            {"Content-Disposition": f'attachment; filename="ser2net-{stamp}.yaml"'},
        )

    async def get_custom(self, request: Request) -> Response:
        try:
            text = self.c.custom_file.read_text(encoding="utf-8")
        except OSError:
            text = export(self.c.config)  # a start: the current connections
        return ok(
            {
                "text": text,
                "check": asdict(self.c.check_custom(text)),
                "exists": self.c.custom_file.exists(),
            }
        )

    async def check_custom(self, request: Request) -> Response:
        return ok(asdict(self.c.check_custom(str(request.json().get("text", "")))))

    async def put_custom(self, request: Request) -> Response:
        data = request.json()
        try:
            result = await self.c.save_custom(str(data.get("text", "")), use=bool(data.get("use")))
        except CustomError as err:
            return ok({"error": "invalid", "check": asdict(err.check)}, 400)
        return ok(asdict(result))

    async def versions(self, request: Request) -> Response:
        return ok(self.c.store.versions())

    async def version_config(self, request: Request) -> Response:
        config = self.c.store.version(int(request.params["id"]))
        if config is None:
            raise HttpError(404, "no such version")
        return ok(config.to_dict())

    async def restore(self, request: Request) -> Response:
        config = self.c.store.version(int(request.params["id"]))
        if config is None:
            raise HttpError(404, "no such version")
        return await self._save(lambda _: config, "restore")

    def _trace_path(self, name: str) -> Any:
        if "/" in name or name.startswith(".") or not (".log" in name or name.endswith(".jsonl")):
            raise HttpError(400, "not a trace file")
        path = self.c.trace.record_dir / name
        if not path.is_file():
            raise HttpError(404, "no such file")
        return path

    async def trace_file(self, request: Request) -> Response:
        path = self._trace_path(request.params["name"])
        return Response(
            200,
            path.read_bytes(),
            "text/plain; charset=utf-8",
            {"Content-Disposition": f'attachment; filename="{path.name}"'},
        )

    async def meter(self, request: Request) -> Response:
        if self.c.config.connection(request.params["id"]) is None:
            raise HttpError(404, "no such connection")
        return ok(self.c.analyze(request.params["id"]))

    async def detect(self, request: Request) -> Response:
        try:
            return ok({"job": self.c.start_detect(request.params["id"])})
        except ValueError as err:
            raise HttpError(409, str(err)) from None

    @staticmethod
    def _ints(data: Any, *keys: str) -> list[int]:
        try:
            return [int(data[k]) for k in keys]
        except (KeyError, TypeError, ValueError):
            raise HttpError(400, f"numbers needed: {', '.join(keys)}") from None

    async def modbus_read(self, request: Request) -> Response:
        unit, function, address, count = self._ints(
            request.json(), "unit", "function", "address", "count"
        )
        try:
            return ok(
                await self.c.modbus_read(request.params["id"], unit, function, address, count)
            )
        except ValueError as err:
            raise HttpError(409, str(err)) from None

    async def modbus_scan(self, request: Request) -> Response:
        first, last, timeout_ms = self._ints(request.json(), "first", "last", "timeout_ms")
        try:
            return ok({"job": self.c.start_scan(request.params["id"], first, last, timeout_ms)})
        except ValueError as err:
            raise HttpError(409, str(err)) from None

    async def job(self, request: Request) -> Response:

        job = self.c.jobs.get(request.params["job"])
        if job is None:
            raise HttpError(404, "no such job")
        return ok(job)

    async def notify_services(self, request: Request) -> Response:
        return ok(await asyncio.to_thread(notify_services))

    async def diagnostics(self, request: Request) -> Response:
        try:
            runtime = self.c.config_file.read_text(encoding="utf-8")
        except OSError:
            runtime = ""
        data = diagnostics.build(
            version=self.version,
            ser2net_version=self.c.ser2net_version,
            snapshot=self.c.snapshot(),
            config=self.c.config.to_dict(),
            runtime_yaml=runtime,
            events=[e.to_dict() for e in self.c.events.history(limit=500)],
        )
        stamp = time.strftime("%Y%m%d-%H%M")
        return Response(
            200,
            data,
            "application/zip",
            {"Content-Disposition": f'attachment; filename="device-proxy-diagnostics-{stamp}.zip"'},
        )

    async def enocean_send(self, request: Request) -> Response:
        data = request.json()
        if not isinstance(data, dict) or not isinstance(data.get("hex"), str):
            raise HttpError(400, "hex: the frame as hex digits")
        try:
            return ok(await self.c.enocean_send(request.params["id"], data["hex"]))
        except ValueError as err:
            raise HttpError(409, str(err)) from None

    async def enocean_test(self, request: Request) -> Response:
        (count,) = self._ints(request.json(), "count")
        try:
            return ok(await self.c.enocean_test(request.params["id"], count))
        except ValueError as err:
            raise HttpError(409, str(err)) from None

    async def capture_start(self, request: Request) -> Response:
        data = request.json()
        peer = data.get("exclusive_peer") if isinstance(data, dict) else None
        if peer is not None and not isinstance(peer, str):
            raise HttpError(400, "exclusive_peer: an address or nothing")
        try:
            return ok(self.c.start_capture(request.params["id"], peer or None))
        except ValueError as err:
            raise HttpError(409, str(err)) from None

    async def capture_stop(self, request: Request) -> Response:
        return ok(self.c.stop_capture())

    async def delete_trace(self, request: Request) -> Response:
        os.unlink(self._trace_path(request.params["name"]))
        return ok({"deleted": request.params["name"]})
