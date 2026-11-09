import asyncio
import json
import struct
from typing import Any

import pytest

from device_proxy import ha_mqtt, ha_registry
from device_proxy.ha_registry import Core, RegistryError

ENTRIES: list[dict[str, Any]] = [
    {
        "entity_id": "sensor.z_wave_datenrate",
        "platform": "mqtt",
        "unique_id": "device_proxy_a_rate",
    },
    {"entity_id": "button.z_wave_usb_reset", "platform": "mqtt", "unique_id": "device_proxy_a_usb"},
    {"entity_id": "sensor.device_proxy_x", "platform": "mqtt", "unique_id": "device_proxy_a_x"},
    {"entity_id": "sensor.other_mqtt", "platform": "mqtt", "unique_id": "other"},
    {"entity_id": "sensor.not_mqtt", "platform": "zha", "unique_id": "device_proxy_b"},
    {"entity_id": "sensor.taken", "platform": "mqtt", "unique_id": "device_proxy_a_t"},
    {"entity_id": "sensor.device_proxy_taken", "platform": "zha", "unique_id": "z"},
]


def test_only_the_apps_entities_without_the_prefix_change() -> None:
    rows = ha_registry.plan(ENTRIES)
    assert [(row["old"], row["conflict"]) for row in rows] == [
        ("button.z_wave_usb_reset", False),
        ("sensor.taken", True),
        ("sensor.z_wave_datenrate", False),
    ]
    assert rows[0]["new"] == "button.device_proxy_z_wave_usb_reset"


def test_new_entities_get_the_prefix() -> None:
    device = {"name": "Z-Wave Küche"}
    assert (
        ha_mqtt.default_entity_id("sensor", {"device": device, "name": "Gerät groß"})
        == "sensor.device_proxy_z_wave_kuche_gerat_gross"
    )
    hub = {"name": "Device Proxy"}
    assert (
        ha_mqtt.default_entity_id("event", {"device": hub, "name": "Ereignisse"})
        == "event.device_proxy_ereignisse"
    )


class FakeCore:
    """The server side of Home Assistant's WebSocket API, as far as the app needs it."""

    def __init__(self, token: str = "secret", refuse: str = "") -> None:
        self.token, self.refuse = token, refuse
        self.calls: list[dict[str, Any]] = []

    @staticmethod
    def _text(data: dict[str, Any]) -> bytes:
        raw = json.dumps(data).encode()
        size = len(raw)
        head = bytes([0x81, size]) if size < 126 else bytes([0x81, 126]) + struct.pack("!H", size)
        return head + raw

    @staticmethod
    async def _read(reader: asyncio.StreamReader) -> dict[str, Any]:
        first, second = await reader.readexactly(2)
        assert first == 0x81 and second & 0x80  # a client's frames are masked
        size = second & 0x7F
        if size == 126:
            size = struct.unpack("!H", await reader.readexactly(2))[0]
        mask = await reader.readexactly(4)
        data = await reader.readexactly(size)
        loaded: dict[str, Any] = json.loads(bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        return loaded

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        head = await reader.readuntil(b"\r\n\r\n")
        assert head.startswith(b"GET /core/websocket HTTP/1.1")
        writer.write(b"HTTP/1.1 101 Switching Protocols\r\n\r\n")
        writer.write(self._text({"type": "auth_required"}))
        auth = await self._read(reader)
        if auth["access_token"] != self.token:
            writer.write(self._text({"type": "auth_invalid"}))
            return
        writer.write(self._text({"type": "auth_ok"}))
        writer.write(bytes([0x89, 1]) + b"x")  # a ping in between
        while True:
            try:
                message = await self._read(reader)
            except asyncio.IncompleteReadError:
                return
            if message.get("type") == "unknown" or not message.get("id"):
                continue  # the pong has opcode 10, see below
            self.calls.append(message)
            kind, base = message["type"], {"id": message["id"], "type": "result"}
            if kind == "config/entity_registry/list":
                writer.write(self._text({**base, "success": True, "result": ENTRIES}))
            elif kind == "search/related":
                result = {"automation": ["a", "b"], "device": ["d"]}
                writer.write(self._text({**base, "success": True, "result": result}))
            elif message.get("entity_id") == self.refuse:
                error = {"message": "nope"}
                writer.write(self._text({**base, "success": False, "error": error}))
            else:
                writer.write(self._text({**base, "success": True, "result": {}}))

    async def __aenter__(self) -> "FakeCore":
        self.server = await asyncio.start_server(self._guarded, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def _guarded(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        # the pong the client sends after the ping is no text frame
        original = reader.readexactly

        async def skip_pong(n: int) -> bytes:
            data = await original(n)
            if n == 2 and data[0] == 0x8A:
                await original((data[1] & 0x7F) + 4)
                return await skip_pong(n)
            return data

        reader.readexactly = skip_pong  # type: ignore[method-assign]
        await self.handle(reader, writer)

    async def __aexit__(self, *_: object) -> None:
        self.server.close()

    def core(self, token: str = "secret") -> Core:
        return Core("127.0.0.1", self.port, token)


async def test_the_preview_says_who_uses_an_id() -> None:
    async with FakeCore() as fake:
        rows = await ha_registry.preview(fake.core())
    assert [row["used"] for row in rows] == [2, 2, 2]


async def test_rename_changes_what_it_can() -> None:
    async with FakeCore(refuse="button.z_wave_usb_reset") as fake:
        renamed, failed = await ha_registry.rename(fake.core())
    assert renamed == 1
    assert failed == [
        {"old": "button.z_wave_usb_reset", "error": "nope"},
        {"old": "sensor.taken", "error": "sensor.device_proxy_taken exists"},
    ]
    update = [c for c in fake.calls if c["type"] == "config/entity_registry/update"][-1]
    assert update["new_entity_id"] == "sensor.device_proxy_z_wave_datenrate"


async def test_a_wrong_token_is_reported() -> None:
    async with FakeCore() as fake:
        with pytest.raises(RegistryError, match="token"):
            await ha_registry.preview(fake.core("wrong"))


async def test_outside_home_assistant_there_is_nothing_to_ask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    with pytest.raises(RegistryError, match="only inside"):
        await ha_registry.preview()
