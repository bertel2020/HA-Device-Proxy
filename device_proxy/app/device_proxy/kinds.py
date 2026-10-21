"""The kinds of connection beside ser2net's "serial" ones: each runs a proxy in the app.

A kind says how its proxy is built, which changes restart it, and what it adds to the
state, the start events and Home Assistant's entities. The controller and the MQTT bridge
go through this table, so a new kind adds an entry here instead of branches there.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from . import modbus
from .model import Connection
from .trace import Chunk

EventSink = Callable[..., None]  # (level, kind, **params)
TraceSink = Callable[[Chunk], None]
Entity = Callable[..., dict[str, Any]]  # (key, **config) → an entity's discovery config


class ProxyStats(Protocol):
    bytes_to_device: int
    bytes_from_device: int
    last_error: str


class AppProxy(Protocol):
    """What the app needs of a running proxy."""

    c: Connection
    key: Connection  # restart_key() when it was started
    listening: bool
    listen_error: str
    reachable: bool | None  # None: not known yet
    reachable_since: float

    @property
    def stats(self) -> ProxyStats: ...

    @property
    def clients(self) -> Mapping[str, Any]: ...

    async def run(self) -> None: ...

    def state(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class Kind:
    model: str  # the Home Assistant device's model
    icon: str  # of the switch entity
    build: Callable[[Connection, str, EventSink, TraceSink], AppProxy]
    restart_key: Callable[[Connection, str], Connection]
    loaded: Callable[[Connection], dict[str, Any]]  # values of the "<kind>_loaded" event
    client_row: Callable[[Any], dict[str, Any]]  # a client in the state
    mqtt_entities: Callable[[str, str, Entity], dict[str, dict[str, Any]]]
    mqtt_state: Callable[[dict[str, Any]], dict[str, Any]]  # from state()


# model.KINDS lists "serial" and these
PROXIED: dict[str, Kind] = {
    "modbus": Kind(
        model="Modbus proxy",
        icon="mdi:lan",
        build=modbus.ModbusProxy,
        restart_key=modbus.restart_key,
        loaded=modbus.loaded,
        client_row=modbus.client_row,
        mqtt_entities=modbus.mqtt_entities,
        mqtt_state=modbus.mqtt_state,
    ),
}
