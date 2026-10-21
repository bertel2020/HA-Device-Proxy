"""Client for ser2net's admin port, kept open for the life of ser2net.

After "yaml" every answer comes as a document (%YAML 1.1 / --- / ... ) and ser2net also
pushes "new connection" and "disconnect" documents on its own. Its YAML is not quite
standard (repeated keys such as one "port" per connection, single quotes escaped with a
backslash), so documents are read line by line here instead of with a YAML library.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .model import ADMIN_SOCKET

_LOGGER = logging.getLogger(__name__)

Node = list[tuple[str, Any]]  # ordered key/value pairs; a value is a str, int or Node


def parse_value(text: str) -> str | int:
    if text.startswith("!!int "):
        return int(text[6:])
    if text.startswith("!!str "):
        text = text[6:]
    if len(text) >= 2 and text[0] == text[-1] == "'":
        text = text[1:-1].replace("\\'", "'")
    return text


def parse_document(lines: list[str]) -> Node:
    root: Node = []
    stack: list[tuple[int, Node]] = [(-1, root)]
    for line in lines:
        if not line.strip():
            continue
        indent = (len(line) - len(line.lstrip(" "))) // 2
        key, sep, rest = line.strip().partition(":")
        if not sep:
            continue
        while stack[-1][0] >= indent:
            stack.pop()
        rest = rest.strip()
        if rest:
            stack[-1][1].append((key, parse_value(rest)))
        else:
            child: Node = []
            stack[-1][1].append((key, child))
            stack.append((indent, child))
    return root


def get(node: Node, key: str, default: Any = None) -> Any:
    return next((value for k, value in node if k == key), default)


def get_all(node: Node, key: str) -> list[Any]:
    return [value for k, value in node if k == key]


@dataclass
class Client:
    address: str  # "192.168.1.20:50114"
    bytes_to_client: int = 0
    bytes_from_client: int = 0
    queued: int = 0


@dataclass
class PortStatus:
    alias: str
    enabled: bool
    device: str
    clients: list[Client] = field(default_factory=list)
    bytes_from_device: int = 0
    bytes_to_device: int = 0
    pending: str = "retained"  # "reconfigured": a change waits for the clients to leave
    session: str = "unconnected"  # "closed" when off; else a session is (still) there


def remote_address(text: str) -> str:
    """gensio's "ipv4,192.168.1.20,50114" (or without the family) as "192.168.1.20:50114";
    an IPv4 client on ser2net's IPv6 socket ("::ffff:192.168.1.20") the same."""
    parts = text.split(",")
    if parts and parts[0] in ("ipv4", "ipv6"):
        parts = parts[1:]
    if len(parts) >= 2:
        host = ",".join(parts[:-1]).removeprefix("::ffff:")
        return f"[{host}]:{parts[-1]}" if ":" in host else f"{host}:{parts[-1]}"
    return text


def ports_from(response: Node) -> list[PortStatus]:
    ports = []
    for port in get_all(response, "port"):
        ports.append(
            PortStatus(
                alias=str(get(port, "name", "")),
                enabled=str(get(port, "enable state", "on")) != "off",
                device=str(get(port, "device", "")),
                clients=[
                    Client(
                        remote_address(str(get(c, "name", ""))),
                        int(get(c, "bytes written to TCP", 0)),
                        int(get(c, "bytes read from TCP", 0)),
                        int(get(c, "bytes in queue to TCP", 0)),
                    )
                    for c in get_all(port, "connected")
                ],
                bytes_from_device=int(get(port, "bytes read from device", 0)),
                bytes_to_device=int(get(port, "bytes written to device", 0)),
                pending=str(get(port, "close state", "retained")),
                session=str(get(port, "tcp to device state", "unconnected")),
            )
        )
    return ports


class AdminError(Exception):
    """ser2net answered a command with an error, or the admin port is not there."""


class AdminClient:
    """The app's one connection to ser2net's admin socket, in YAML mode."""

    def __init__(
        self,
        on_event: Callable[[str, str, str], None],
        *,
        path: str = ADMIN_SOCKET,
    ) -> None:
        self.on_event = on_event  # (type, alias, remote address)
        self.path = path
        self.connected = asyncio.Event()
        self._writer: asyncio.StreamWriter | None = None
        self._waiting: asyncio.Queue[asyncio.Future[Node]] = asyncio.Queue()
        self._lock = asyncio.Lock()

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                reader, writer = await asyncio.open_unix_connection(self.path)
            except OSError:
                await _sleep(stop, 1)
                continue
            self._writer = writer
            writer.write(b"yaml\r\n")
            await writer.drain()
            self.connected.set()
            _LOGGER.debug("Admin port connected")
            reading = asyncio.create_task(self._read(reader, stop))
            stopping = asyncio.create_task(stop.wait())
            try:
                await asyncio.wait([reading, stopping], return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in (reading, stopping):
                    task.cancel()
                self.connected.clear()
                self._writer = None
                writer.close()
                self._fail_waiting()
            await _sleep(stop, 1)

    async def _read(self, reader: asyncio.StreamReader, stop: asyncio.Event) -> None:
        document: list[str] | None = None
        while not stop.is_set():
            raw = await reader.readline()
            if not raw:
                return
            line = raw.decode(errors="replace").rstrip("\r\n")
            if line.startswith("%YAML"):
                document = []
            elif document is not None and line == "---" and not document:
                continue
            elif document is not None and line == "...":
                self._dispatch(parse_document(document))
                document = None
            elif document is not None:
                document.append(line)

    def _dispatch(self, doc: Node) -> None:
        response = get(doc, "response")
        if isinstance(response, list):
            if not self._waiting.empty():
                future = self._waiting.get_nowait()
                if not future.done():
                    future.set_result(response)
            return
        for kind in ("new connection", "disconnect"):
            info = get(doc, kind)
            if isinstance(info, list):
                address = remote_address(str(get(info, "remaddr", "")))
                self.on_event(kind, str(get(info, "name", "")), address)

    def _fail_waiting(self) -> None:
        while not self._waiting.empty():
            future = self._waiting.get_nowait()
            if not future.done():
                future.set_exception(AdminError("ser2net's admin port closed"))

    async def command(self, line: str, timeout: float = 5) -> Node:
        async with self._lock:
            if self._writer is None:
                raise AdminError("ser2net's admin port is not connected")
            future: asyncio.Future[Node] = asyncio.get_running_loop().create_future()
            await self._waiting.put(future)
            self._writer.write(line.encode() + b"\r\n")
            await self._writer.drain()
            try:
                response = await asyncio.wait_for(future, timeout)
            except TimeoutError:
                if self._writer is not None:  # a late answer would pass for the next one's
                    self._writer.close()
                raise AdminError(f"no answer to {line.split()[0]!r}") from None
        error = get(response, "error")
        if error is not None and error != "reload done":
            raise AdminError(str(error))
        return response

    async def showport(self, alias: str | None = None) -> list[PortStatus]:
        return ports_from(await self.command(f"showport {alias}" if alias else "showport"))

    async def disconnect(self, alias: str) -> None:
        await self.command(f"disconnect {alias}")

    async def reload(self) -> None:
        await self.command("reload", timeout=15)


async def _sleep(stop: asyncio.Event, seconds: float) -> None:
    try:
        await asyncio.wait_for(stop.wait(), seconds)
    except TimeoutError:
        pass
