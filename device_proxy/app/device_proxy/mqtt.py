"""A small MQTT 3.1.1 client on asyncio: connect with a last will, publish, subscribe.

Enough for Home Assistant's MQTT discovery: QoS 0 only, retained messages, one subscription
for the switch commands, keepalive pings. Reconnects on its own; the broker comes from the
Supervisor (services/mqtt).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import ssl
import struct
import urllib.request
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

_LOGGER = logging.getLogger(__name__)

CONNECT, CONNACK, PUBLISH, SUBSCRIBE, SUBACK, PINGREQ, PINGRESP, DISCONNECT = (
    1,
    2,
    3,
    8,
    9,
    12,
    13,
    14,
)
KEEPALIVE = 60
REFUSED = {
    1: "protocol version",
    2: "client id",
    3: "server unavailable",
    4: "user or password",
    5: "not authorized",
}


@dataclass
class Broker:
    host: str
    port: int
    username: str = ""
    password: str = ""
    ssl: bool = False


def supervisor_broker() -> Broker | None:
    """The MQTT broker the Supervisor offers (needs services: mqtt:want), or None."""
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        return None
    request = urllib.request.Request(
        "http://supervisor/services/mqtt", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.load(response).get("data") or {}
    except (OSError, ValueError) as err:
        _LOGGER.info("No MQTT broker from the Supervisor (%s)", err)
        return None
    if not data.get("host"):
        return None
    return Broker(
        str(data["host"]),
        int(data.get("port") or 1883),
        str(data.get("username") or ""),
        str(data.get("password") or ""),
        bool(data.get("ssl")),
    )


def _string(text: str | bytes) -> bytes:
    raw = text.encode() if isinstance(text, str) else text
    return struct.pack("!H", len(raw)) + raw


def _packet(kind: int, flags: int, body: bytes) -> bytes:
    length, encoded = len(body), b""
    while True:
        byte, length = length % 128, length // 128
        encoded += bytes([byte | (0x80 if length else 0)])
        if not length:
            break
    return bytes([(kind << 4) | flags]) + encoded + body


class MqttClient:
    def __init__(
        self,
        client_id: str,
        on_message: Callable[[str, bytes], Awaitable[None]],
        on_connect: Callable[[], Awaitable[None]],
        *,
        will: tuple[str, bytes] | None = None,
    ) -> None:
        self.client_id = client_id
        self.on_message = on_message
        self.on_connect = on_connect
        self.will = will
        self.connected = asyncio.Event()
        self.error = ""
        self._writer: asyncio.StreamWriter | None = None
        self._packet_id = 0

    async def run(self, broker: Broker, stop: asyncio.Event) -> None:
        delay = 2.0
        while not stop.is_set():
            try:
                await self._session(broker, stop)
                delay = 2.0
            except (OSError, asyncio.IncompleteReadError, ConnectionError, ValueError) as err:
                self.error = str(err) or type(err).__name__
                _LOGGER.warning("MQTT: %s, connecting again in %.0f s", self.error, delay)
            finally:
                self.connected.clear()
                self._writer = None
            try:
                await asyncio.wait_for(stop.wait(), delay)
            except TimeoutError:
                pass
            delay = min(delay * 2, 60)

    async def _session(self, broker: Broker, stop: asyncio.Event) -> None:
        context = ssl.create_default_context() if broker.ssl else None
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(broker.host, broker.port, ssl=context), 15
        )
        self._writer = writer
        flags = 0x02  # clean session
        payload = _string(self.client_id)
        if self.will:
            flags |= 0x04 | 0x20  # will, retained
            payload += _string(self.will[0]) + _string(self.will[1])
        if broker.username:
            flags |= 0x80
            payload += _string(broker.username)
            if broker.password:
                flags |= 0x40
                payload += _string(broker.password)
        body = _string("MQTT") + bytes([4, flags]) + struct.pack("!H", KEEPALIVE) + payload
        writer.write(_packet(CONNECT, 0, body))
        await writer.drain()
        kind, _, data = await asyncio.wait_for(self._read(reader), 15)
        if kind != CONNACK or len(data) < 2:
            raise ConnectionError("no CONNACK from the broker")
        if data[1]:
            raise ConnectionError(f"broker refused: {REFUSED.get(data[1], data[1])}")
        self.error = ""
        self.connected.set()
        _LOGGER.info("MQTT connected to %s:%s", broker.host, broker.port)
        await self.on_connect()
        pinger = asyncio.create_task(self._ping(stop))
        try:
            while not stop.is_set():
                reading = asyncio.ensure_future(self._read(reader))
                stopping = asyncio.ensure_future(stop.wait())
                done, _ = await asyncio.wait(
                    [reading, stopping],
                    timeout=KEEPALIVE * 1.5,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                stopping.cancel()
                if reading not in done:
                    reading.cancel()
                    if stop.is_set():
                        break
                    raise ConnectionError("broker silent")
                kind, flags, data = reading.result()
                if kind == PUBLISH:
                    topic_length = struct.unpack("!H", data[:2])[0]
                    topic = data[2 : 2 + topic_length].decode(errors="replace")
                    start = 2 + topic_length + (2 if flags & 0x06 else 0)
                    await self.on_message(topic, data[start:])
            if writer and not writer.is_closing():
                if self.will:  # a clean disconnect does not send the will: say it ourselves
                    await self.publish(self.will[0], self.will[1], retain=True)
                writer.write(_packet(DISCONNECT, 0, b""))
                await writer.drain()
        finally:
            pinger.cancel()
            writer.close()

    async def _ping(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            await asyncio.sleep(KEEPALIVE / 2)
            if self._writer is not None:
                self._writer.write(_packet(PINGREQ, 0, b""))
                await self._writer.drain()

    @staticmethod
    async def _read(reader: asyncio.StreamReader) -> tuple[int, int, bytes]:
        head = (await reader.readexactly(1))[0]
        length, shift = 0, 0
        while True:
            byte = (await reader.readexactly(1))[0]
            length |= (byte & 0x7F) << shift
            if not byte & 0x80:
                break
            shift += 7
        return head >> 4, head & 0x0F, await reader.readexactly(length) if length else b""

    async def publish(
        self, topic: str, payload: bytes | str | dict[str, Any], *, retain: bool = False
    ) -> None:
        if self._writer is None or not self.connected.is_set():
            return
        if isinstance(payload, dict):
            payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        raw = payload.encode() if isinstance(payload, str) else payload
        self._writer.write(_packet(PUBLISH, 0x01 if retain else 0, _string(topic) + raw))
        await self._writer.drain()

    async def subscribe(self, topic: str) -> None:
        if self._writer is None:
            return
        self._packet_id = self._packet_id % 65535 + 1
        body = struct.pack("!H", self._packet_id) + _string(topic) + bytes([0])
        self._writer.write(_packet(SUBSCRIBE, 0x02, body))
        await self._writer.drain()
