"""Home Assistant MQTT discovery: one device per connection with its entities.

Per connection: device present, clients, data rate, bytes from the device, last data, line
errors, a switch to turn the connection on and off, buttons that disconnect its clients and
restart the connection (and for a USB reset of a local adapter or a power cycle); for a Modbus
connection the device reachable, clients, requests, unanswered requests, answer time, the switch
and the buttons; an EnOcean gateway with a fallback has buttons to switch.
States go as one JSON per connection to <base>/<id>/state, the switch listens on
<base>/<id>/enabled/set. <base>/status is the availability (the broker sets it to offline
when the app goes away). Removed connections get an empty retained config, so Home
Assistant removes their entities.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import urllib.request
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from . import i18n
from .events import Event
from .kinds import PROXIED
from .meter import ENTITIES, entity_values
from .model import AppConfig
from .mqtt import Broker, MqttClient, supervisor_broker

if TYPE_CHECKING:
    from .controller import Controller

_LOGGER = logging.getLogger(__name__)

NAMES = i18n.section("entities")


def panel_url() -> str:
    """The link to the app's page inside Home Assistant, "" when not running as an app."""
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        return ""
    request = urllib.request.Request(
        "http://supervisor/addons/self/info", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            slug = (json.load(response).get("data") or {}).get("slug")
    except (OSError, ValueError) as err:
        _LOGGER.info("The app's own slug not read: %s", err)
        return ""
    return f"homeassistant://hassio/ingress/{slug}" if slug else ""


# What can start an automation in Home Assistant; everything else stays in the app's events.
_REFUSED = (
    "client_refused",
    "client_refused_network",
    "client_refused_exclusive",
    "client_refused_blocked",
)
_RESTARTS = (
    "connection_restarted",
    "auto_restart_gave_up",
    "auto_restart_failed",
    "usb_reset_failed",
    "power_cycle_failed",
)
EVENT_TYPES = {
    "serial": (
        "device_missing",
        "device_back",
        "client_new",
        "client_stuck",
        "stuck_disconnected",
        "line_errors",
        "keep_open_failed",
        *_RESTARTS,
    ),
    "modbus": (
        "modbus_down",
        "modbus_back",
        "client_new",
        *_REFUSED,
        "write_blocked",
        "write_blocked_register",
        *_RESTARTS,
    ),
    "enocean": (
        "enocean_down",
        "enocean_back",
        "enocean_failover",
        "enocean_failback",
        "enocean_fallback_unready",
        "duty_cycle_high",
        "client_new",
        "client_dropped",
        *_REFUSED,
        *_RESTARTS,
    ),
}
APP_EVENT_TYPES: tuple[str, ...] = ("ser2net_restart", "ser2net_start_failed")


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
            on_state=self._state_changed,
        )
        self.broker: Broker | None = None
        self._announced: set[str] = set()
        self._last: dict[str, str] = {}
        self._sending: set[asyncio.Task[None]] = set()

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
        settings = self.c.config.settings
        self.c.panel_url = self.c.panel_url or await asyncio.to_thread(panel_url)
        if settings.mqtt_host:
            self.broker = Broker(
                settings.mqtt_host,
                settings.mqtt_port,
                settings.mqtt_user,
                settings.mqtt_password,
                settings.mqtt_tls,
            )
        else:
            self.broker = await asyncio.to_thread(supervisor_broker)
        if self.broker is None:
            _LOGGER.info("MQTT: no broker in Home Assistant, entities are off")
            self.c.events.emit("info", "mqtt_no_broker")  # MQTT is on by default
            return
        publisher = asyncio.create_task(self._publish_loop(stop))
        try:
            await self.client.run(self.broker, stop)
        finally:
            publisher.cancel()

    def _state_changed(self, up: bool, error: str) -> None:
        if up:
            self.c.events.emit("info", "mqtt_connected", broker=self.state["broker"])
        else:
            self.c.events.emit("warning", "mqtt_lost", broker=self.state["broker"], error=error)

    async def _connected(self) -> None:
        self._announced.clear()
        self._last.clear()
        await self.client.publish(f"{self.base}/status", "online", retain=True)
        await self.client.subscribe(f"{self.base}/+/enabled/set")
        await self.client.subscribe(f"{self.base}/+/+/press")
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
                except Exception:  # a bug must not stop the states for good
                    _LOGGER.exception("MQTT: publishing the states failed")

    def _links(self) -> dict[str, str]:
        """What every device of the app shows on its page in Home Assistant."""
        link = {"configuration_url": self.c.panel_url} if self.c.panel_url else {}
        return {"sw_version": os.environ.get("APP_VERSION", "dev"), **link}

    def _device(self, connection_id: str, name: str, model: str) -> dict[str, Any]:
        return {
            "identifiers": [f"device_proxy_{connection_id}"],
            "name": name,
            "manufacturer": "Device Proxy app",
            "model": model,
            "via_device": "device_proxy",
            **self._links(),
        }

    def configs(self) -> dict[str, dict[str, Any]]:
        """Discovery topic → config of every entity there should be."""
        settings = self.c.config.settings
        names = NAMES[settings.notify_language]
        prefix, base = settings.mqtt_prefix, self.base
        availability = [{"topic": f"{base}/status"}]
        hub = {
            "identifiers": ["device_proxy"],
            "name": "Device Proxy",
            "manufacturer": "Device Proxy app",
            **self._links(),
        }
        result: dict[str, dict[str, Any]] = {
            f"{prefix}/binary_sensor/device_proxy/running/config": {
                "name": names["running"],
                "unique_id": "device_proxy_running",
                "state_topic": f"{base}/app/state",
                "value_template": "{{ 'ON' if value_json.running else 'OFF' }}",
                "device_class": "running",
                "availability": availability,
                "device": hub,
            },
            f"{prefix}/event/device_proxy/events/config": {
                "name": names["events"],
                "unique_id": "device_proxy_events",
                "state_topic": f"{base}/app/event",
                "event_types": list(APP_EVENT_TYPES),
                "icon": "mdi:bell-outline",
                "availability": availability,
                "device": hub,
                "has_entity_name": True,
            },
        }
        for c in self.c.active + self.c.config.proxied:
            state = f"{base}/{c.id}/state"
            kind = PROXIED.get(c.kind)
            # Home Assistant's list of devices shows name and model: the model says whose it is
            device = self._device(c.id, c.name, f"Device Proxy · {names[f'kind_{c.kind}']}")

            def entity(
                key: str,
                c_id: str = c.id,
                state: str = state,
                device: dict[str, Any] = device,
                **extra: Any,
            ) -> dict[str, Any]:
                return {
                    "name": names.get(key, key),  # a register's name comes with extra
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
                icon=kind.icon if kind else "mdi:serial-port",
            )
            buttons = [("disconnect", "mdi:lan-disconnect"), ("restart", "mdi:restart")]
            if c.uses_device:
                buttons.append(("usb_reset", "mdi:usb-port"))
            if c.power_switch:
                buttons.append(("power_cycle", "mdi:power-cycle"))
            if c.kind == "enocean" and c.fallback:
                buttons += [
                    ("to_fallback", "mdi:swap-horizontal"),
                    ("to_main", "mdi:backup-restore"),
                ]
            for action, icon in buttons:
                button = entity(action, command_topic=f"{base}/{c.id}/{action}/press", icon=icon)
                button.pop("state_topic")  # a button has no state
                result[f"{prefix}/button/device_proxy_{c.id}/{action}/config"] = button
            result[f"{prefix}/event/device_proxy_{c.id}/events/config"] = entity(
                "events",
                state=f"{base}/{c.id}/event",
                event_types=list(EVENT_TYPES[c.kind]),
                icon="mdi:bell-outline",
            )
            result[f"{prefix}/sensor/device_proxy_{c.id}/clients/config"] = entity(
                "clients",
                value_template="{{ value_json.clients }}",
                state_class="measurement",
                icon="mdi:lan-connect",
            )
            if kind:
                result.update(kind.mqtt_entities(prefix, c, entity))
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
            if c.meter_entities:
                for key, unit, device_class, state_class in ENTITIES.values():
                    result[f"{prefix}/sensor/device_proxy_{c.id}/{key}/config"] = entity(
                        key,
                        value_template=f"{{{{ value_json.{key} }}}}",
                        unit_of_measurement=unit,
                        device_class=device_class,
                        state_class=state_class,
                    )
            result[f"{prefix}/sensor/device_proxy_{c.id}/line_errors/config"] = entity(
                "line_errors",
                value_template="{{ value_json.line_errors }}",
                state_class="total_increasing",
                icon="mdi:alert-circle-outline",
                entity_category="diagnostic",
            )
        return result

    def send_event(self, event: Event) -> None:
        """Pass an event on to its event entity; a repeat that is summed up stays out."""
        if event.count > 1 or not self.client.connected.is_set():
            return
        if event.connection is None:
            allowed, topic = APP_EVENT_TYPES, f"{self.base}/app/event"
        elif (c := self.c.config.connection(event.connection)) is not None:
            allowed, topic = EVENT_TYPES[c.kind], f"{self.base}/{c.id}/event"
        else:
            return
        if event.kind not in allowed:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # raised outside the app's loop: no way to send it from here
            return
        payload = {**event.params, "message": event.message, "event_type": event.kind}
        task = loop.create_task(self._publish_event(topic, payload))
        self._sending.add(task)
        task.add_done_callback(self._sending.discard)

    async def _publish_event(self, topic: str, payload: dict[str, Any]) -> None:
        try:
            await self.client.publish(topic, payload)
        except (OSError, ConnectionError) as err:
            _LOGGER.debug("MQTT: event not sent: %s", err)

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
            if c.get("meter_entities"):
                state.update(entity_values(self.c.meter(c["id"])))
            kind = PROXIED.get(c["kind"])
            if kind and c.get(c["kind"]) is not None:
                state.update(kind.mqtt_state(c[c["kind"]]))
            text = json.dumps(state)
            key = f"state:{c['id']}"
            if force or self._last.get(key) != text:
                await self.client.publish(f"{self.base}/{c['id']}/state", text, retain=True)
                self._last[key] = text
        ids = {f"state:{c['id']}" for c in connections}
        for key in [k for k in self._last if k.startswith("state:") and k not in ids]:
            await self.client.publish(f"{self.base}/{key[6:]}/state", b"", retain=True)  # gone
            self._last.pop(key)

    async def clear(self, keep: set[str]) -> None:
        """Before this bridge stops for good (other prefix, MQTT off): the discovery configs it
        announced that the next one will not, so their entities do not stay as unavailable."""
        if not self.client.connected.is_set():
            return
        for topic in [t for t in self._last if t.endswith("/config") and t not in keep]:
            await self.client.publish(topic, b"", retain=True)
            self._last.pop(topic)

    async def _stale_config(self, topic: str, payload: bytes) -> None:
        """A retained discovery config of this app for an entity that no longer exists."""
        prefix = f"{self.c.config.settings.mqtt_prefix}/"  # may have slashes of its own
        parts = topic.removeprefix(prefix).split("/") if topic.startswith(prefix) else []
        if not payload or len(parts) != 4 or parts[3] != "config" or topic in self.configs():
            return
        if parts[1] == "device_proxy" or parts[1].startswith("device_proxy_"):
            await self.client.publish(topic, b"", retain=True)
            self._last.pop(topic, None)

    async def _message(self, topic: str, payload: bytes) -> None:
        if topic.endswith("/config"):
            await self._stale_config(topic, payload)
            return
        # <base>/<id>/enabled/set, and the base may have slashes of its own
        head = f"{self.base}/"
        parts = topic.removeprefix(head).split("/") if topic.startswith(head) else []
        if len(parts) == 3 and parts[2] == "press":
            _LOGGER.info("MQTT: button %s of %s", parts[1], parts[0])
            try:
                await self.c.press(parts[0], parts[1])
            except Exception as err:  # also AdminError: ser2net's admin socket not there
                _LOGGER.warning("MQTT: button %s of %s: %s", parts[1], parts[0], err)
            return
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
