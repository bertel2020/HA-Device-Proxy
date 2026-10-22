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
LISTEN = ("local", "apps", "lan", "all")
SOURCES = ("forms", "custom")
ENOCEAN_TEMPLATES = ("fam_usb", "fam14", "fgw14_usb", "usb300", "mgw_eth", "symcon_lan", "enocean")
TEMPLATES = ("generic", "ehz_sml", "ehz_d0", "zwave", "modbus", *ENOCEAN_TEMPLATES)
KINDS = ("serial", "modbus", "enocean")  # shared by ser2net, or by a proxy in the app (kinds.py)
LINKS = {  # how a proxy reaches its device
    "modbus": ("tcp", "rtu", "rtu_tcp"),
    "enocean": ("serial", "tcp"),
}
SERIAL_LINKS = {"rtu", "serial"}  # the links that open a serial device of this host
ESP_PROTOCOLS = ("esp2", "esp3")
WRITE_ACCESS = ("all", "none", "listed")

HOST = re.compile(r"[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?|\[?[0-9A-Fa-f:.]+\]?")
PRIVATE_NETWORKS = (
    "127.0.0.0/8",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "::1/128",
    "fc00::/7",
    "fe80::/10",
)
# Home Assistant itself and the other apps (the Supervisor's network)
APPS_NETWORKS = ("127.0.0.0/8", "::1/128", "172.30.32.0/23")
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
    device: str  # the serial device ("" for a Modbus device reached over the network)
    port: int  # the TCP port the clients connect to
    id: str = field(default_factory=new_id)
    enabled: bool = True
    kind: str = "serial"
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
    # Modbus proxy (kind "modbus")
    link: str = "tcp"  # Modbus TCP, Modbus RTU on the serial device, or RTU over TCP
    host: str = ""  # the device's address for "tcp" and "rtu_tcp"
    host_port: int = 502
    request_timeout_ms: int = 3000  # for the device's answer
    connect_delay_ms: int = 0  # wait after connecting before the first request
    retries: int = 1  # further attempts when the device does not answer
    request_gap_ms: int = 0  # extra pause between two requests
    device_connections: int = 1  # connections to a network device, requests in parallel
    write_access: str = "all"  # which clients may write: "all", "none" or "listed"
    write_clients: str = ""  # for "listed": addresses or networks
    cache_ms: int = 0  # reads answered from the last answer this long (0: always ask)
    unit_map: str = ""  # "1=3, 2=5": a client's unit 1 goes to the device's unit 3
    probe_seconds: int = 0  # read a register after this long without requests (0: off)
    probe_unit: int = 1
    probe_function: int = 3  # 3 holding or 4 input registers
    probe_address: int = 0
    # EnOcean gateway (kind "enocean", enocean.py)
    esp_protocol: str = "esp2"
    send_gap_ms: int = 10  # pause after each frame sent to the gateway
    replay_size: int = 1000  # radio telegrams kept while no replaying client is connected
    replay_max_age_s: int = 900
    replay_persist: bool = False  # keep the replay buffer over a restart of the app (/data)

    @property
    def uses_device(self) -> bool:
        """Has a serial device: ser2net's connections and a proxy's on a local adapter."""
        return self.kind == "serial" or self.link in SERIAL_LINKS

    @property
    def remote(self) -> bool:
        """A proxy that reaches its device over the network (host and host_port)."""
        return self.kind != "serial" and not self.uses_device

    @property
    def upstream(self) -> str:
        """Where a proxy's device is, for messages."""
        if self.uses_device:
            return f"{self.device} {self.serial_format}"
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"{host}:{self.host_port}"

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
        required_fields = ["name", "port"]
        probe = replace(_BLANK, kind=values.get("kind", "serial"), link=values.get("link", "tcp"))
        if probe.uses_device:
            required_fields.append("device")
        for required in required_fields:
            if required not in values and required not in errors:
                errors[required] = "is missing"
        if errors:
            raise ValidationError(errors)
        values.setdefault("device", "")  # a proxy that reaches its device over the network
        connection = cls(**values)
        connection.validate()
        return connection

    def validate(self) -> None:
        e: dict[str, str] = {}
        if not self.name.strip() or len(self.name) > 64:
            e["name"] = "1 to 64 characters"
        if not re.fullmatch(r"[0-9a-f]{8}", self.id):
            e["id"] = "is not an id of this app"
        if self.kind not in KINDS:
            e["kind"] = f"one of {', '.join(KINDS)}"
        if self.uses_device and (
            not self.device.startswith("/dev/") or re.search(r"[,\s]", self.device)
        ):
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
        elif self.keep_open and self.kind == "serial" and self.max_clients < 2:
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
        if self.kind != "serial":
            self._validate_link(e)
        if self.kind == "modbus":
            self._validate_modbus(e)
        elif self.kind == "enocean":
            self._validate_enocean(e)
        if e:
            raise ValidationError(e)

    def _validate_link(self, e: dict[str, str]) -> None:
        links = LINKS.get(self.kind, ())
        if self.link not in links:
            e["link"] = f"one of {', '.join(links)}"
        elif self.remote:
            if not HOST.fullmatch(self.host) or len(self.host) > 253:
                e["host"] = "a host name or IP address"
            elif self.host in ("127.0.0.1", "localhost", "::1") and self.host_port == self.port:
                e["host_port"] = "is this connection's own port"
        if not 1 <= self.host_port <= 65535:
            e["host_port"] = "between 1 and 65535"

    def _validate_enocean(self, e: dict[str, str]) -> None:
        if self.esp_protocol not in ESP_PROTOCOLS:
            e["esp_protocol"] = "esp2 or esp3"
        if not 0 <= self.send_gap_ms <= 1000:
            e["send_gap_ms"] = "0 to 1000 ms"
        if not 0 <= self.replay_size <= 100000:
            e["replay_size"] = "0 to 100000 telegrams"
        if not 0 <= self.replay_max_age_s <= 86400:
            e["replay_max_age_s"] = "0 to 86400 seconds"

    def _validate_modbus(self, e: dict[str, str]) -> None:
        if not 100 <= self.request_timeout_ms <= 60000:
            e["request_timeout_ms"] = "100 to 60000 ms"
        if not 0 <= self.connect_delay_ms <= 10000:
            e["connect_delay_ms"] = "0 to 10000 ms"
        if not 0 <= self.retries <= 5:
            e["retries"] = "0 to 5"
        if not 0 <= self.request_gap_ms <= 10000:
            e["request_gap_ms"] = "0 to 10000 ms"
        if not 1 <= self.device_connections <= 4:
            e["device_connections"] = "1 to 4"
        elif self.link == "rtu" and self.device_connections > 1:
            e["device_connections"] = "1 for a serial device"
        if not 0 <= self.cache_ms <= 60000:
            e["cache_ms"] = "0 to 60000 ms"
        try:
            parse_unit_map(self.unit_map)
        except ValueError as err:
            e["unit_map"] = str(err)
        if self.probe_seconds and not 5 <= self.probe_seconds <= 3600:
            e["probe_seconds"] = "0 or 5 to 3600 seconds"
        if not 0 <= self.probe_unit <= 255:
            e["probe_unit"] = "0 to 255"
        elif self.probe_unit == 0 and self.link != "tcp":
            e["probe_unit"] = "not 0 on RTU: a broadcast, nothing answers it"
        if self.probe_function not in (3, 4):
            e["probe_function"] = "3 or 4"
        if not 0 <= self.probe_address <= 65535:
            e["probe_address"] = "0 to 65535"
        if self.write_access not in WRITE_ACCESS:
            e["write_access"] = f"one of {', '.join(WRITE_ACCESS)}"
        elif self.write_access == "listed":
            try:
                parse_networks(self.write_clients)
            except ValueError as err:
                e["write_clients"] = str(err)


_BLANK = Connection(name="", device="", port=0, id="00000000")  # for derived properties


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
    mqtt_base: str = "device_proxy"
    mqtt_interval: int = 10  # seconds between state updates
    mqtt_host: str = ""  # "" = the broker the Supervisor offers
    mqtt_port: int = 1883
    mqtt_user: str = ""
    mqtt_password: str = ""
    mqtt_tls: bool = False
    # EnOcean gateways for the EnOcean Eltako integration (enocean_ha.py)
    enocean_discovery: bool = True
    enocean_status_port: int = 9199  # read-only status, for Home Assistant and the apps only

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
        if settings.mqtt_host and not re.fullmatch(r"[A-Za-z0-9_.:\[\]-]+", settings.mqtt_host):
            e["mqtt_host"] = "a host name or address"
        if not 1 <= settings.mqtt_port <= 65535:
            e["mqtt_port"] = "1 to 65535"
        if not 2 <= settings.mqtt_interval <= 3600:
            e["mqtt_interval"] = "2 to 3600 seconds"
        if not 1024 <= settings.enocean_status_port <= 65535:
            e["enocean_status_port"] = "1024 to 65535"
        elif settings.enocean_status_port in RESERVED_PORTS:
            e["enocean_status_port"] = f"used by {RESERVED_PORTS[settings.enocean_status_port]}"
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
        seen: dict[str, dict[Any, str]] = {
            "port": {},
            "device": {},
            "name": {},
            "id": {},
            "host": {},
        }
        status_port = self.settings.enocean_status_port
        enocean = any(c.kind == "enocean" for c in self.connections)
        for index, c in enumerate(self.connections):
            if enocean and c.port == status_port:
                e[f"connections.{index}.port"] = "used by the status for the EnOcean integration"
            checks: list[tuple[str, Any]] = [("port", c.port), ("id", c.id)]
            if c.uses_device:
                checks.append(("device", c.device))
            if c.remote:
                # two proxies for one device would take its connections from each other
                checks.append(("host", (c.host.lower(), c.host_port)))
            for key, value in checks:
                if value in seen[key]:
                    e[f"connections.{index}.{key}"] = f"also used by {seen[key][value]}"
                seen[key].setdefault(value, c.name)
            folded = c.name.strip().casefold()
            if folded in seen["name"]:
                e[f"connections.{index}.name"] = "another connection has this name"
            seen["name"].setdefault(folded, c.name)
        if e:
            raise ValidationError(e)

    @property
    def serial(self) -> tuple[Connection, ...]:
        """The connections ser2net shares."""
        return tuple(c for c in self.connections if c.kind == "serial")

    @property
    def proxied(self) -> tuple[Connection, ...]:
        """The connections of the app's own proxies (Modbus, EnOcean)."""
        return tuple(c for c in self.connections if c.kind != "serial")

    @property
    def modbus(self) -> tuple[Connection, ...]:
        """The connections of the app's Modbus proxy."""
        return tuple(c for c in self.connections if c.kind == "modbus")

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


def client_allowed(remaddr: str, listen: str, address: str) -> bool:
    """May a client from this address connect (remaddr, else the global listen setting)?"""
    if remaddr:
        networks = parse_networks(remaddr)
    elif listen in ("apps", "lan"):
        networks = [
            ipaddress.ip_network(n)
            for n in (APPS_NETWORKS if listen == "apps" else PRIVATE_NETWORKS)
        ]
    else:
        return True
    try:
        ip = ipaddress.ip_address(address.split("%")[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return any(ip in n for n in networks if n.version == ip.version)


def parse_unit_map(text: str) -> dict[int, int]:
    """ "1=3, 2=5" → {1: 3, 2: 5}: the unit a client asks for → the device's unit."""
    result: dict[int, int] = {}
    for item in re.split(r"[,;\s]+", text.strip()):
        if not item:
            continue
        match = re.fullmatch(r"(\d{1,3})(?:=|->|→)(\d{1,3})", item)
        if not match or not all(0 <= int(n) <= 255 for n in match.groups()):
            raise ValueError(f"{item!r} is not unit=unit (0 to 255)")
        client, device = int(match.group(1)), int(match.group(2))
        if client in result:
            raise ValueError(f"unit {client} twice")
        result[client] = device
    return result


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
