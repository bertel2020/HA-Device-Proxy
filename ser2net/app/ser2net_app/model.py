"""The app's configuration: settings and connections, versioned and validated.

Stored as JSON in /data; every value has a default, so older files load. SCHEMA counts the
format; migrate() lifts older versions before they are read.
"""

from __future__ import annotations

import ipaddress
import re
import secrets
from dataclasses import asdict, dataclass, field, fields, replace
from typing import Any

SCHEMA = 1
# ser2net's admin interface: a socket inside the container only, so no other program on the
# host (the app runs in the host network) can reach it; it has no authentication
ADMIN_SOCKET = "/run/ser2net-admin.sock"
INGRESS_PORT = 18399  # the web interface (config.yaml ingress_port)
RESERVED_PORTS = {INGRESS_PORT: "the app's web interface"}
LOG_LEVELS = ("info", "debug")

MODES = ("raw", "rfc2217", "telnet")
PARITIES = ("n", "e", "o", "m", "s")
LINE_STATES = ("", "on", "off")
TRACE_MODES = ("off", "rx", "tx", "both")
LISTEN = ("local", "lan", "all")
SOURCES = ("forms", "custom")
TEMPLATES = ("generic", "ehz_sml", "ehz_d0", "zwave")
PRIVATE_NETWORKS = (
    "127.0.0.0/8",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "::1/128",
    "fc00::/7",
    "fe80::/10",
)
# options the forms set; "weitere Optionen" may not set them a second time
MANAGED_OPTIONS = {
    "max-connections",
    "kickolduser",
    "chardelay",
    "banner",
    "openstr",
    "closestr",
    "connector-retry-time",
    "remaddr",
    "trace-read",
    "trace-write",
    "trace-both",
    "trace-hexdump",
    "trace-timestamp",
}
OPTION_KEY = re.compile(r"[a-z][a-z0-9-]*")
RS485 = re.compile(r"off|\d+:\d+(:(rts_on_send|rts_after_send|rx_during_tx|terminate_bus))*")


class ValidationError(ValueError):
    """One or more fields are wrong: {field: message}; field "" for the whole entry."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("; ".join(f"{k}: {v}" if k else v for k, v in errors.items()))
        self.errors = errors


def new_id() -> str:
    return secrets.token_hex(4)


@dataclass(frozen=True)
class Connection:
    name: str
    device: str
    port: int
    id: str = field(default_factory=new_id)
    enabled: bool = True
    template: str = "generic"
    baud: int = 9600
    data_bits: int = 8
    parity: str = "n"
    stop_bits: int = 1
    mode: str = "raw"
    max_clients: int = 1
    # serial side
    local: bool = True
    rtscts: bool = False
    xonxoff: bool = False
    hangup_when_done: bool = False
    nobreak: bool = False
    dtr: str = ""  # "" keeps the line as it is
    rts: str = ""
    rs485: str = ""
    low_latency: bool = False  # FTDI latency_timer 1 ms
    # connection
    timeout: int = 0
    kickolduser: bool = False
    chardelay: bool = True
    remaddr: str = ""  # "" follows the global listen setting
    banner: str = ""
    openstr: str = ""
    closestr: str = ""
    connector_retry_time: int = 0  # 0: ser2net's default
    # TCP side
    nodelay: bool = False
    bind: str = ""  # "" follows the global listen setting
    extra: tuple[tuple[str, str], ...] = ()
    # app features
    keep_open: bool = False  # the app stays connected, so the device is open without clients
    stuck_disconnect: bool = False  # disconnect the clients when one stops reading
    trace: str = "off"
    notify_missing: bool = True
    notify_no_client: bool = False
    silence_minutes: int = 0

    @property
    def alias(self) -> str:
        """The connection's name inside ser2net: stable when the connection is renamed."""
        return f"c_{self.id}"

    @property
    def serial_format(self) -> str:
        return f"{self.baud}{self.parity}{self.data_bits}{self.stop_bits}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["extra"] = [list(pair) for pair in self.extra]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Connection:
        errors: dict[str, str] = {}
        values: dict[str, Any] = {}
        for f in fields(cls):
            if f.name not in data:
                continue
            raw = data[f.name]
            try:
                values[f.name] = _coerce(f.name, raw, f.type)
            except (TypeError, ValueError):
                errors[f.name] = "has the wrong type"
        for required in ("name", "device", "port"):
            if required not in values and required not in errors:
                errors[required] = "is missing"
        if errors:
            raise ValidationError(errors)
        connection = cls(**values)
        connection.validate()
        return connection

    def validate(self) -> None:
        e: dict[str, str] = {}
        if not self.name.strip() or len(self.name) > 64:
            e["name"] = "1 to 64 characters"
        if not re.fullmatch(r"[0-9a-f]{8}", self.id):
            e["id"] = "is not an id of this app"
        if not self.device.startswith("/dev/") or re.search(r"[,\s]", self.device):
            e["device"] = "a path under /dev without commas or spaces"
        if not 1 <= self.port <= 65535:
            e["port"] = "between 1 and 65535"
        elif self.port in RESERVED_PORTS:
            e["port"] = f"used by {RESERVED_PORTS[self.port]}"
        if self.template not in TEMPLATES:
            e["template"] = f"one of {', '.join(TEMPLATES)}"
        if not 50 <= self.baud <= 4_000_000:
            e["baud"] = "between 50 and 4000000"
        if self.data_bits not in (5, 6, 7, 8):
            e["data_bits"] = "5 to 8"
        if self.parity not in PARITIES:
            e["parity"] = "n, e, o, m or s"
        if self.stop_bits not in (1, 2):
            e["stop_bits"] = "1 or 2"
        if self.mode not in MODES:
            e["mode"] = f"one of {', '.join(MODES)}"
        if not 1 <= self.max_clients <= 100:
            e["max_clients"] = "between 1 and 100"
        elif self.keep_open and self.max_clients < 2:
            e["max_clients"] = "at least 2 when the device is kept open (the app uses one)"
        for name in ("dtr", "rts"):
            if getattr(self, name) not in LINE_STATES:
                e[name] = "on, off or empty"
        if self.rs485 and not RS485.fullmatch(self.rs485):
            e["rs485"] = "off or <delay before>:<delay after>[:<conf>]"
        if not 0 <= self.timeout <= 86400:
            e["timeout"] = "0 to 86400 seconds"
        if not 0 <= self.connector_retry_time <= 86400:
            e["connector_retry_time"] = "0 to 86400 seconds"
        if self.remaddr:
            try:
                parse_networks(self.remaddr)
            except ValueError as err:
                e["remaddr"] = str(err)
        if self.bind:
            try:
                ipaddress.ip_address(self.bind)
            except ValueError:
                e["bind"] = "an IP address of this host"
        for key, _ in self.extra:
            if not OPTION_KEY.fullmatch(key):
                e["extra"] = f"{key!r} is not an option name"
            elif key in MANAGED_OPTIONS:
                e["extra"] = f"{key} has its own field"
        for name in ("banner", "openstr", "closestr"):
            if len(getattr(self, name)) > 1000:
                e[name] = "at most 1000 characters"
        if self.trace not in TRACE_MODES:
            e["trace"] = f"one of {', '.join(TRACE_MODES)}"
        if not 0 <= self.silence_minutes <= 1440:
            e["silence_minutes"] = "0 to 1440 minutes"
        if e:
            raise ValidationError(e)


@dataclass(frozen=True)
class Settings:
    listen: str = "lan"
    log_level: str = "info"
    source: str = "forms"  # "custom": the user's own ser2net.yaml is used as it is
    history_days: int = 30
    trace_file_mb: int = 5
    trace_keep: int = 3
    debounce_count: int = 3  # this many of one event within debounce_minutes ...
    debounce_minutes: int = 5  # ... are summed up into one
    # notifications in Home Assistant
    notify_grace: int = 30  # seconds a problem must last
    notify_dismiss: bool = True  # remove the notification when the problem is gone
    notify_service: str = ""  # e.g. mobile_app_phone, "" for none
    notify_resolved: bool = False  # also tell the notify service when it is over
    notify_stuck: bool = True
    notify_line_errors: bool = False
    notify_ser2net: bool = True
    notify_language: str = "de"
    no_client_minutes: int = 2
    # entities in Home Assistant over MQTT discovery
    mqtt_enabled: bool = True  # only with a broker in Home Assistant
    mqtt_prefix: str = "homeassistant"
    mqtt_base: str = "ser2net"
    mqtt_interval: int = 10  # seconds between state updates

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        errors: dict[str, str] = {}
        values: dict[str, Any] = {}
        for f in fields(cls):
            if f.name in data:
                try:
                    values[f.name] = _coerce(f.name, data[f.name], f.type)
                except (TypeError, ValueError):
                    errors[f.name] = "has the wrong type"
        if errors:
            raise ValidationError(errors)
        settings = cls(**values)
        e: dict[str, str] = {}
        if settings.listen not in LISTEN:
            e["listen"] = f"one of {', '.join(LISTEN)}"
        if settings.log_level not in LOG_LEVELS:
            e["log_level"] = f"one of {', '.join(LOG_LEVELS)}"
        if settings.source not in SOURCES:
            e["source"] = f"one of {', '.join(SOURCES)}"
        if not 1 <= settings.history_days <= 365:
            e["history_days"] = "1 to 365 days"
        if not 1 <= settings.trace_file_mb <= 100:
            e["trace_file_mb"] = "1 to 100 MB"
        if not 0 <= settings.trace_keep <= 20:
            e["trace_keep"] = "0 to 20 files"
        if not 2 <= settings.debounce_count <= 100:
            e["debounce_count"] = "2 to 100"
        if not 1 <= settings.debounce_minutes <= 120:
            e["debounce_minutes"] = "1 to 120 minutes"
        if not 0 <= settings.notify_grace <= 3600:
            e["notify_grace"] = "0 to 3600 seconds"
        if settings.notify_service and not re.fullmatch(r"[a-z0-9_]+", settings.notify_service):
            e["notify_service"] = "a notify service name like mobile_app_phone"
        if settings.notify_language not in ("de", "en"):
            e["notify_language"] = "de or en"
        if not 1 <= settings.no_client_minutes <= 1440:
            e["no_client_minutes"] = "1 to 1440 minutes"
        for key in ("mqtt_prefix", "mqtt_base"):
            if not re.fullmatch(r"[A-Za-z0-9_-]+(/[A-Za-z0-9_-]+)*", getattr(settings, key)):
                e[key] = "an MQTT topic without wildcards"
        if not 2 <= settings.mqtt_interval <= 3600:
            e["mqtt_interval"] = "2 to 3600 seconds"
        if e:
            raise ValidationError(e)
        return settings


@dataclass(frozen=True)
class AppConfig:
    settings: Settings = field(default_factory=Settings)
    connections: tuple[Connection, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "settings": self.settings.to_dict(),
            "connections": [c.to_dict() for c in self.connections],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        data = migrate(data)
        errors: dict[str, str] = {}
        try:
            settings = Settings.from_dict(data.get("settings", {}))
        except ValidationError as err:
            settings = Settings()
            errors.update({f"settings.{k}": v for k, v in err.errors.items()})
        connections = []
        for index, item in enumerate(data.get("connections", [])):
            try:
                connections.append(Connection.from_dict(item))
            except ValidationError as err:
                errors.update({f"connections.{index}.{k}": v for k, v in err.errors.items()})
        if errors:
            raise ValidationError(errors)
        config = cls(settings, tuple(connections))
        config.validate()
        return config

    def validate(self) -> None:
        e: dict[str, str] = {}
        seen: dict[str, dict[Any, str]] = {"port": {}, "device": {}, "name": {}, "id": {}}
        for index, c in enumerate(self.connections):
            for key, value in (("port", c.port), ("device", c.device), ("id", c.id)):
                if value in seen[key]:
                    e[f"connections.{index}.{key}"] = f"also used by {seen[key][value]}"
                seen[key].setdefault(value, c.name)
            folded = c.name.strip().casefold()
            if folded in seen["name"]:
                e[f"connections.{index}.name"] = "another connection has this name"
            seen["name"].setdefault(folded, c.name)
        if e:
            raise ValidationError(e)

    def connection(self, connection_id: str) -> Connection | None:
        return next((c for c in self.connections if c.id == connection_id), None)

    def with_connection(self, connection: Connection) -> AppConfig:
        """This config with the connection added, or replaced when its id exists."""
        items = [c for c in self.connections if c.id != connection.id]
        index = next((i for i, c in enumerate(self.connections) if c.id == connection.id), None)
        items.insert(len(items) if index is None else index, connection)
        return replace(self, connections=tuple(items))

    def without_connection(self, connection_id: str) -> AppConfig:
        return replace(
            self, connections=tuple(c for c in self.connections if c.id != connection_id)
        )


def migrate(data: dict[str, Any]) -> dict[str, Any]:
    schema = data.get("schema", SCHEMA)
    if not isinstance(schema, int) or schema > SCHEMA:
        raise ValidationError({"schema": f"version {schema} is newer than this app knows"})
    # no older versions yet; lift them here one step at a time when SCHEMA grows
    return data


def parse_networks(text: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Addresses or networks separated by commas, semicolons or spaces."""
    networks = []
    for item in re.split(r"[,;\s]+", text.strip()):
        if not item:
            continue
        try:
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            raise ValueError(f"{item!r} is not an address or network") from None
    if not networks:
        raise ValueError("no address or network given")
    return networks


def _coerce(name: str, value: Any, kind: Any) -> Any:
    kind = str(kind)
    if kind == "bool":
        if not isinstance(value, bool):
            raise TypeError(name)
        return value
    if kind == "int":
        if isinstance(value, bool) or not isinstance(value, int | str):
            raise TypeError(name)
        return int(value)
    if kind == "str":
        if not isinstance(value, str):
            raise TypeError(name)
        return value
    if name == "extra":
        pairs = []
        for item in value:
            key, text = item
            if not isinstance(key, str) or not isinstance(text, str):
                raise TypeError(name)
            pairs.append((key, text))
        return tuple(pairs)
    raise TypeError(name)
