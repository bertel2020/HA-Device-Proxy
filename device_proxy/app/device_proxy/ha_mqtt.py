"""Home Assistant MQTT discovery: one device per connection with its entities.

Per connection: device present, clients, data rate, bytes from the device, last data, line
errors and a switch to turn the connection on and off; for a Modbus connection the device
reachable, clients, requests, unanswered requests, answer time and the switch.
States go as one JSON per connection to <base>/<id>/state, the switch listens on
<base>/<id>/enabled/set. <base>/status is the availability (the broker sets it to offline
when the app goes away). Removed connections get an empty retained config, so Home
Assistant removes their entities.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from .model import AppConfig
from .mqtt import Broker, MqttClient, supervisor_broker

if TYPE_CHECKING:
    from .controller import Controller

_LOGGER = logging.getLogger(__name__)

NAMES = {
    "de": {
        "present": "Gerät angeschlossen",
        "clients": "Clients",
        "rate": "Datenrate",
        "received": "Daten vom Gerät",
        "last_data": "Letzte Daten",
        "line_errors": "Leitungsfehler",
        "enabled": "Aktiv",
        "running": "ser2net läuft",
        "reachable": "Gerät erreichbar",
        "requests": "Anfragen",
        "failed": "Anfragen ohne Antwort",
        "answer_time": "Antwortzeit",
    },
    "en": {
        "present": "Device connected",
        "clients": "Clients",
        "rate": "Data rate",
        "received": "Data from the device",
        "last_data": "Last data",
        "line_errors": "Line errors",
        "enabled": "Active",
        "running": "ser2net running",
        "reachable": "Device reachable",
        "requests": "Requests",
        "failed": "Unanswered requests",
        "answer_time": "Answer time",
    },
}


class HaBridge:
    def __init__(self, controller: Controller) -> None:
        self.c = controller
        settings = controller.config.settings
        self.base = settings.mqtt_base
        self.client = MqttClient(
            "device-proxy",
            self._message,
            self._connected,
            will=(f"{self.base}/status", b"offline"),
        )
        self.broker: Broker | None = None
        self._announced: set[str] = set()
        self._last: dict[str, str] = {}

    @property
    def state(self) -> dict[str, Any]:
        return {
            "enabled": self.c.config.settings.mqtt_enabled,
            "broker": f"{self.broker.host}:{self.broker.port}" if self.broker else None,
            "connected": self.client.connected.is_set(),
            "error": self.client.error,
        }

    async def run(self, stop: asyncio.Event) -> None:
        if not self.c.config.settings.mqtt_enabled:
            return
        self.broker = await asyncio.to_thread(supervisor_broker)
        if self.broker is None:
            _LOGGER.info("MQTT: no broker in Home Assistant, entities are off")
            return
        publisher = asyncio.create_task(self._publish_loop(stop))
        try:
            await self.client.run(self.broker, stop)
        finally:
            publisher.cancel()

    async def _connected(self) -> None:
        self._announced.clear()
        self._last.clear()
        await self.client.publish(f"{self.base}/status", "online", retain=True)
        await self.client.subscribe(f"{self.base}/+/enabled/set")
        # what an earlier run left behind (retained) comes back here and is cleared if stale
        await self.client.subscribe(f"{self.c.config.settings.mqtt_prefix}/+/+/+/config")
        await self.announce()
        await self.publish_states(force=True)

    async def _publish_loop(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            await asyncio.sleep(self.c.config.settings.mqtt_interval)
            if self.client.connected.is_set():
                try:
                    await self.announce()
                    await self.publish_states()
                except (OSError, ConnectionError) as err:
                    _LOGGER.debug("MQTT publish failed: %s", err)

    def _device(self, connection_id: str, name: str, model: str) -> dict[str, Any]:
        return {
            "identifiers": [f"device_proxy_{connection_id}"],
            "name": name,
            "manufacturer": "Device Proxy app",
            "model": model,
            "via_device": "device_proxy",
        }

    def configs(self) -> dict[str, dict[str, Any]]:
        """Discovery topic → config of every entity there should be."""
        settings = self.c.config.settings
        names = NAMES[settings.notify_language]
        prefix, base = settings.mqtt_prefix, self.base
        availability = [{"topic": f"{base}/status"}]
        result: dict[str, dict[str, Any]] = {
            f"{prefix}/binary_sensor/device_proxy/running/config": {
                "name": names["running"],
                "unique_id": "device_proxy_running",
                "state_topic": f"{base}/app/state",
                "value_template": "{{ 'ON' if value_json.running else 'OFF' }}",
                "device_class": "running",
                "availability": availability,
                "device": {
                    "identifiers": ["device_proxy"],
                    "name": "Device Proxy",
                    "manufacturer": "Device Proxy app",
                    **({"sw_version": self.c.ser2net_version} if self.c.ser2net_version else {}),
                },
            }
        }
        for c in self.c.active + self.c.config.modbus:
            state = f"{base}/{c.id}/state"
            model = "Modbus proxy" if c.kind == "modbus" else "Serial connection"
            device = self._device(c.id, c.name, model)

            def entity(
                key: str,
                c_id: str = c.id,
                state: str = state,
                device: dict[str, Any] = device,
                **extra: Any,
            ) -> dict[str, Any]:
                return {
                    "name": names[key],
                    "unique_id": f"device_proxy_{c_id}_{key}",
                    "state_topic": state,
                    "availability": availability,
                    "device": device,
                    "has_entity_name": True,
                    **extra,
                }

            result[f"{prefix}/switch/device_proxy_{c.id}/enabled/config"] = entity(
                "enabled",
                value_template="{{ 'ON' if value_json.enabled else 'OFF' }}",
                command_topic=f"{base}/{c.id}/enabled/set",
                icon="mdi:lan" if c.kind == "modbus" else "mdi:serial-port",
            )
            result[f"{prefix}/sensor/device_proxy_{c.id}/clients/config"] = entity(
                "clients",
                value_template="{{ value_json.clients }}",
                state_class="measurement",
                icon="mdi:lan-connect",
            )
            if c.kind == "modbus":
                result.update(self._modbus_entities(prefix, c.id, entity))
                continue
            result[f"{prefix}/binary_sensor/device_proxy_{c.id}/present/config"] = entity(
                "present",
                value_template="{{ 'ON' if value_json.present else 'OFF' }}",
                device_class="plug",
            )
            result[f"{prefix}/sensor/device_proxy_{c.id}/rate/config"] = entity(
                "rate",
                value_template="{{ value_json.rate }}",
                unit_of_measurement="B/s",
                device_class="data_rate",
                state_class="measurement",
            )
            result[f"{prefix}/sensor/device_proxy_{c.id}/received/config"] = entity(
                "received",
                value_template="{{ value_json.received }}",
                unit_of_measurement="B",
                device_class="data_size",
                state_class="total_increasing",
            )
            result[f"{prefix}/sensor/device_proxy_{c.id}/last_data/config"] = entity(
                "last_data",
                value_template="{{ value_json.last_data }}",
                device_class="timestamp",
            )
            result[f"{prefix}/sensor/device_proxy_{c.id}/line_errors/config"] = entity(
                "line_errors",
                value_template="{{ value_json.line_errors }}",
                state_class="total_increasing",
                icon="mdi:alert-circle-outline",
                entity_category="diagnostic",
            )
        return result

    @staticmethod
    def _modbus_entities(prefix: str, connection_id: str, entity: Any) -> dict[str, dict[str, Any]]:
        key = f"device_proxy_{connection_id}"
        return {
            f"{prefix}/binary_sensor/{key}/reachable/config": entity(
                "reachable",
                value_template="{{ 'ON' if value_json.reachable else 'OFF' }}",
                device_class="connectivity",
            ),
            f"{prefix}/sensor/{key}/requests/config": entity(
                "requests",
                value_template="{{ value_json.requests }}",
                state_class="total_increasing",
                icon="mdi:swap-horizontal",
            ),
            f"{prefix}/sensor/{key}/failed/config": entity(
                "failed",
                value_template="{{ value_json.failed }}",
                state_class="total_increasing",
                icon="mdi:alert-circle-outline",
                entity_category="diagnostic",
            ),
            f"{prefix}/sensor/{key}/answer_time/config": entity(
                "answer_time",
                value_template="{{ value_json.answer_time }}",
                unit_of_measurement="ms",
                device_class="duration",
                state_class="measurement",
                entity_category="diagnostic",
            ),
        }

    async def announce(self) -> None:
        configs = self.configs()
        for topic, config in configs.items():
            text = json.dumps(config, ensure_ascii=False, sort_keys=True)
            if self._last.get(topic) != text:
                await self.client.publish(topic, text, retain=True)
                self._last[topic] = text
        for topic in [t for t in self._last if t.endswith("/config") and t not in configs]:
            await self.client.publish(topic, b"", retain=True)  # entity removed
            self._last.pop(topic)

    async def publish_states(self, *, force: bool = False) -> None:
        snapshot = self.c.snapshot()
        app = json.dumps({"running": bool(snapshot["ser2net_running"])})
        if force or self._last.get("app") != app:
            await self.client.publish(f"{self.base}/app/state", app, retain=True)
            self._last["app"] = app
        connections: list[dict[str, Any]] = snapshot["connections"]  # type: ignore[assignment]
        for c in connections:
            last = c["last_data"]
            state = {
                "present": bool(c["present"]),
                "enabled": bool(c["enabled"]),
                "clients": len(c["clients"]),
                "rate": round(c["rate_from_device"], 1),
                "received": c["bytes_from_device"],
                "last_data": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(last))
                if last
                else None,
                "line_errors": sum((c["line_errors"] or {}).values()),
            }
            if c.get("modbus") is not None:
                m = c["modbus"]
                state.update(
                    reachable=m["reachable"] is True,
                    requests=m["requests"],
                    failed=m["failed"],
                    answer_time=m["time_avg_ms"] if m["answered"] else None,
                )
            text = json.dumps(state)
            key = f"state:{c['id']}"
            if force or self._last.get(key) != text:
                await self.client.publish(f"{self.base}/{c['id']}/state", text, retain=True)
                self._last[key] = text

    async def _stale_config(self, topic: str, payload: bytes) -> None:
        """A retained discovery config of this app for an entity that no longer exists."""
        parts = topic.split("/")
        if not payload or len(parts) != 5 or parts[4] != "config" or topic in self.configs():
            return
        if parts[0] == self.c.config.settings.mqtt_prefix and (
            parts[2] == "device_proxy" or parts[2].startswith("device_proxy_")
        ):
            await self.client.publish(topic, b"", retain=True)
            self._last.pop(topic, None)

    async def _message(self, topic: str, payload: bytes) -> None:
        if topic.endswith("/config"):
            await self._stale_config(topic, payload)
            return
        # <base>/<id>/enabled/set, and the base may have slashes of its own
        head = f"{self.base}/"
        parts = topic.removeprefix(head).split("/") if topic.startswith(head) else []
        if len(parts) != 3 or parts[1:] != ["enabled", "set"]:
            return
        connection_id = parts[0]
        current = self.c.config.connection(connection_id)
        if current is None or (self.c.uses_custom and current.kind == "serial"):
            return
        enabled = payload.strip().upper() in (b"ON", b"1", b"TRUE")
        if enabled == current.enabled:
            return
        _LOGGER.info("MQTT: %s switched %s", current.name, "on" if enabled else "off")

        def build(config: AppConfig) -> AppConfig:
            latest = config.connection(connection_id)
            return (
                config
                if latest is None
                else config.with_connection(replace(latest, enabled=enabled))
            )

        await self.c.apply(build, "mqtt")
        await self.publish_states()
