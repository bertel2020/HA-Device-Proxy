"""Home Assistant's entity registry over its WebSocket API: the entity IDs of the app's devices.

MQTT discovery only names an entity the first time it appears, so the IDs of existing entities
can only change here. The standard library has no WebSocket client and this needs very little
of one: a handshake, text frames and answers to pings.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import struct
from types import TracebackType
from typing import Any

PREFIX = "device_proxy"
TIMEOUT = 15  # seconds for one answer
USED_BY = ("automation", "script", "scene", "group")


class RegistryError(Exception):
    """Home Assistant refused, or is not there to ask."""


# what can go wrong on the way, for those who report it instead of failing
FAILED = (OSError, EOFError, TimeoutError, ValueError, RegistryError)


class Core:
    """One authenticated connection to Home Assistant's WebSocket API."""

    def __init__(self, host: str = "supervisor", port: int = 80, token: str | None = None) -> None:
        self.host, self.port = host, port
        self.token = token if token is not None else os.environ.get("SUPERVISOR_TOKEN")
        self._id = 0

    async def __aenter__(self) -> Core:
        if not self.token:
            raise RegistryError("only inside Home Assistant")
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), TIMEOUT
        )
        key = base64.b64encode(os.urandom(16)).decode()
        self.writer.write(
            (
                "GET /core/websocket HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        await self.writer.drain()
        head = await asyncio.wait_for(self.reader.readuntil(b"\r\n\r\n"), TIMEOUT)
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise RegistryError("Home Assistant did not accept the WebSocket")
        await self._receive()  # auth_required
        await self._send(json.dumps({"type": "auth", "access_token": self.token}).encode())
        if (await self._receive()).get("type") != "auth_ok":
            raise RegistryError("Home Assistant did not accept the app's token")
        return self

    async def __aexit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        self.writer.close()

    async def _send(self, data: bytes, opcode: int = 1) -> None:
        size = len(data)
        if size < 126:
            head = bytes([0x80 | opcode, 0x80 | size])
        elif size < 65536:
            head = bytes([0x80 | opcode, 0x80 | 126]) + struct.pack("!H", size)
        else:
            head = bytes([0x80 | opcode, 0x80 | 127]) + struct.pack("!Q", size)
        mask = os.urandom(4)
        self.writer.write(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        await self.writer.drain()

    async def _frame(self) -> tuple[bool, int, bytes]:
        first, second = await self.reader.readexactly(2)
        size = second & 0x7F
        if size == 126:
            size = struct.unpack("!H", await self.reader.readexactly(2))[0]
        elif size == 127:
            size = struct.unpack("!Q", await self.reader.readexactly(8))[0]
        return bool(first & 0x80), first & 0x0F, await self.reader.readexactly(size)

    async def _receive(self) -> dict[str, Any]:
        parts: list[bytes] = []
        while True:
            final, opcode, data = await asyncio.wait_for(self._frame(), TIMEOUT)
            if opcode == 8:
                raise RegistryError("Home Assistant closed the WebSocket")
            if opcode == 9:
                await self._send(data, 10)
            elif opcode in (0, 1):
                parts.append(data)
                if final:
                    answer: dict[str, Any] = json.loads(b"".join(parts))
                    return answer

    async def call(self, kind: str, **params: Any) -> Any:
        self._id += 1
        await self._send(json.dumps({"id": self._id, "type": kind, **params}).encode())
        while True:
            answer = await self._receive()
            if answer.get("id") != self._id:
                continue
            if not answer.get("success"):
                raise RegistryError(str((answer.get("error") or {}).get("message") or kind))
            return answer.get("result")


def plan(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The app's entities whose ID does not begin with the prefix, and the ID each would get."""
    taken = {str(e["entity_id"]) for e in entries}
    rows = []
    for entry in entries:
        old = str(entry["entity_id"])
        domain, name = old.split(".", 1)
        if (
            entry.get("platform") != "mqtt"
            or not str(entry.get("unique_id", "")).startswith(f"{PREFIX}_")
            or name.startswith(PREFIX)
        ):
            continue
        new = f"{domain}.{PREFIX}_{name}"
        rows.append({"old": old, "new": new, "conflict": new in taken})
    return sorted(rows, key=lambda row: row["old"])


async def _used(core: Core, entity_id: str) -> int | None:
    """How many automations, scripts, scenes and groups use the entity, None when not known."""
    try:
        found = await core.call("search/related", item_type="entity", item_id=entity_id)
    except RegistryError:
        return None
    return sum(len(found.get(kind) or ()) for kind in USED_BY)


async def preview(core: Core | None = None) -> list[dict[str, Any]]:
    async with core or Core() as ha:
        rows = plan(await ha.call("config/entity_registry/list"))
        for row in rows:
            row["used"] = await _used(ha, row["old"])
    return rows


async def rename(core: Core | None = None) -> tuple[int, list[dict[str, str]]]:
    """Give the app's entities the prefix; how many changed, and those that could not."""
    renamed, failed = 0, []
    async with core or Core() as ha:
        for row in plan(await ha.call("config/entity_registry/list")):
            if row["conflict"]:
                failed.append({"old": row["old"], "error": f"{row['new']} exists"})
                continue
            try:
                await ha.call(
                    "config/entity_registry/update",
                    entity_id=row["old"],
                    new_entity_id=row["new"],
                )
            except RegistryError as err:
                failed.append({"old": row["old"], "error": str(err)})
            else:
                renamed += 1
    return renamed, failed
