"""Reads a ser2net 4 ser2net.yaml (version 1 or 2) into the app's connections.

Version 1 files are not standard YAML (the key "connection" repeats, its name is the anchor),
so they are read as a node tree, not as a dict. Defines (*(name), =(name)) are filled in,
defaults that the forms know are applied, ser2net's own defaults are kept (e.g. "local" is
off unless set, the app's forms turn it on for new connections). Whatever the forms cannot
hold is reported per connection or for the file, with a code and values for the interface.
"""

from __future__ import annotations

import glob
import ipaddress
import os
import re
from dataclasses import dataclass, field, replace
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from . import legacy
from .model import (
    MANAGED_OPTIONS,
    OPTION_KEY,
    RESERVED_PORTS,
    AppConfig,
    Connection,
    ValidationError,
)

Note = dict[str, Any]  # {"code": ..., values}

V2_KEYS = {"connections", "defines", "defaults", "delete_defaults", "admins", "leds", "rotators"}
SERIAL_FLAGS = {"local", "rtscts", "xonxoff", "nobreak", "hangup-when-done"}
SPEED = re.compile(r"(?:speed=)?(\d+)(?:([NEOMSneoms])([5-8])([12]))?")
BY_ID = "/dev/serial/by-id"
BY_PATH = "/dev/serial/by-path"


class ReadError(ValueError):
    """The file cannot be read at all; .note says why."""

    def __init__(self, note: Note) -> None:
        super().__init__(note.get("message", note["code"]))
        self.note = note


@dataclass
class ImportItem:
    alias: str
    connection: Connection | None  # None: cannot be taken over
    notes: list[Note] = field(default_factory=list)


@dataclass
class ImportResult:
    version: int
    items: list[ImportItem]
    notes: list[Note] = field(default_factory=list)


class _Loader(yaml.SafeLoader):
    """Keeps the anchor of each node: in version 1 it is the connection's name."""

    def __init__(self, stream: str) -> None:
        super().__init__(stream)
        self.node_anchors: dict[int, str] = {}

    def compose_node(self, parent: Node | None, index: Any) -> Node | None:
        event = self.peek_event()  # type: ignore[no-untyped-call]
        anchor = getattr(event, "anchor", None)
        node = super().compose_node(parent, index)
        if node is not None and anchor and not isinstance(event, yaml.AliasEvent):
            self.node_anchors[id(node)] = anchor
        return node


def _pairs(node: Node | None) -> list[tuple[str, Node]]:
    if not isinstance(node, MappingNode):
        return []
    return [(str(k.value), v) for k, v in node.value if isinstance(k, ScalarNode)]


def _scalar(node: Node | None) -> str | None:
    return str(node.value) if isinstance(node, ScalarNode) else None


def _bool(text: str | None, default: bool) -> bool:
    if text is None or text == "":
        return default
    return text.strip().lower() in ("true", "on", "yes", "1")


def split_top(text: str) -> list[str]:
    """Split a gensio string at commas outside parentheses."""
    parts, depth, current = [], 0, ""
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    parts.append(current.strip())
    return parts


def _head(token: str) -> tuple[str, list[str]]:
    name, _, rest = token.partition("(")
    options = [o.strip() for o in rest.rstrip(")").split(",") if o.strip()] if rest else []
    return name.strip(), options


class _Defines:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.unresolved: set[str] = set()

    def fill(self, text: str) -> str:
        def sub(match: re.Match[str]) -> str:
            name = match.group(2)
            if name in self.values:
                return self.values[name]
            self.unresolved.add(name)
            return match.group(0)

        return re.sub(r"([*=])\(([A-Za-z0-9_.-]+)\)", sub, text)


def parse(text: str) -> tuple[int, list[tuple[str, dict[str, Any]]], list[Note]]:
    """The connections of a ser2net.yaml as (name, raw definition), plus file notes."""
    loader = _Loader(text)
    try:
        documents: list[Node] = []
        while loader.check_node():
            node = loader.get_node()
            if node is not None:
                documents.append(node)
    except yaml.YAMLError as err:
        mark = getattr(err, "problem_mark", None)
        raise ReadError(
            {
                "code": "yaml",
                "line": mark.line + 1 if mark else None,
                "message": str(err).splitlines()[0],
            }
        ) from None
    finally:
        loader.dispose()
    keys = {key for doc in documents for key, _ in _pairs(doc)}
    version = 2 if keys & V2_KEYS else 1
    defines = _Defines()
    defaults: dict[str, tuple[str, str | None]] = {}  # name → (value, class)
    notes: list[Note] = []
    raw: list[tuple[str, dict[str, Any]]] = []
    for doc in documents:
        for key, value in _pairs(doc):
            if key == "define":
                name = loader.node_anchors.get(id(value))
                if name and (scalar := _scalar(value)) is not None:
                    defines.values[name] = scalar
            elif key == "defines":
                for name, item in _pairs(value):
                    defines.values[name] = _scalar(item) or ""
            elif key == "default":
                d = dict((k, _scalar(v)) for k, v in _pairs(value))
                if d.get("name"):
                    defaults[str(d["name"])] = (d.get("value") or "", d.get("class"))
            elif key == "defaults":
                for name, item in _pairs(value):
                    d = dict((k, _scalar(v)) for k, v in _pairs(item))
                    defaults[name] = (d.get("value") or "", d.get("class"))
            elif key == "connection":
                name = loader.node_anchors.get(id(value), f"connection{len(raw) + 1}")
                raw.append((name, _definition(value, defines)))
            elif key == "connections":
                for name, item in _pairs(value):
                    raw.append((name, _definition(item, defines)))
            elif key in ("admin", "admins"):
                notes.append({"code": "admin_ignored"})
            elif key == "include":
                notes.append({"code": "include_ignored", "path": _scalar(value)})
            elif key in ("rotator", "rotators", "led", "leds", "delete_defaults"):
                notes.append({"code": "section_ignored", "section": key})
    for _, definition in raw:
        definition["defaults"] = defaults
    if defines.unresolved:
        notes.append({"code": "define_unresolved", "names": sorted(defines.unresolved)})
    return version, raw, notes


def _definition(node: Node, defines: _Defines) -> dict[str, Any]:
    result: dict[str, Any] = {"options": {}}
    for key, value in _pairs(node):
        if key == "options":
            for option, item in _pairs(value):
                text = _scalar(item)
                if text is None and isinstance(item, SequenceNode):
                    text = ";".join(str(_scalar(v)) for v in item.value)
                result["options"][option] = defines.fill(text or "")
        else:
            result[key] = defines.fill(_scalar(value) or "")
    return result


def _accepter(text: str, notes: list[Note]) -> dict[str, Any] | None:
    tokens = split_top(text)
    mode, index = "raw", 0
    while index < len(tokens):
        name, options = _head(tokens[index])
        if name == "telnet":
            mode = "rfc2217" if "rfc2217" in options or "rfc2217=true" in options else "telnet"
            index += 1
        else:
            break
    if index >= len(tokens):
        return None
    name, options = _head(tokens[index])
    if name != "tcp":
        return None
    nodelay = any(o in ("nodelay", "nodelay=true") for o in options)
    for option in options:
        if option not in ("nodelay", "nodelay=true", "nodelay=false"):
            notes.append({"code": "accepter_option_dropped", "option": option})
    args = [a for a in tokens[index + 1 :] if a not in ("ipv4", "ipv6")]
    if not args or not args[-1].isdigit():
        return None
    bind = args[-2] if len(args) >= 2 else ""
    if bind in ("0.0.0.0", "::", "*"):
        bind = ""
    return {"mode": mode, "nodelay": nodelay, "bind": bind.strip("[]"), "port": int(args[-1])}


def _connector(
    text: str, defaults: dict[str, tuple[str, str | None]], notes: list[Note]
) -> dict[str, Any] | None:
    tokens = split_top(text)
    if len(tokens) < 2 or _head(tokens[0])[0] not in ("serialdev", "sdev"):
        return None
    result: dict[str, Any] = {
        "device": tokens[1],
        "baud": 9600,
        "data_bits": 8,
        "parity": "n",
        "stop_bits": 1,
        "local": False,  # ser2net's default; the app's forms turn it on for new ones
        "rtscts": False,
        "xonxoff": False,
        "nobreak": False,
        "hangup_when_done": False,
        "dtr": "",
        "rts": "",
        "rs485": "",
    }
    applied: list[str] = []
    for name, (value, cls) in defaults.items():
        if cls not in (None, "serialdev"):
            continue
        if name in SERIAL_FLAGS:
            result[name.replace("-", "_")] = _bool(value, False)
            applied.append(name)
        elif name == "speed" and (m := SPEED.fullmatch(value)):
            _speed(result, m)
            applied.append(name)
    for token in tokens[2:]:
        flag, _, value = token.partition("=")
        if m := SPEED.fullmatch(token):
            _speed(result, m)
        elif flag in SERIAL_FLAGS:
            result[flag.replace("-", "_")] = _bool(value or "true", True)
        elif flag in ("dtr", "rts") and value in ("on", "off"):
            result[flag] = value
        elif flag == "rs485":
            result["rs485"] = value
        else:
            notes.append({"code": "serial_option_dropped", "option": token})
    result["_defaults"] = applied
    return result


def _speed(result: dict[str, Any], m: re.Match[str]) -> None:
    result["baud"] = int(m.group(1))
    if m.group(2):
        result["parity"] = m.group(2).lower()
        result["data_bits"] = int(m.group(3))
        result["stop_bits"] = int(m.group(4))


def _remaddr(text: str, notes: list[Note]) -> str:
    networks = []
    for item in re.split(r"[;\s]+", text.strip()):
        if not item:
            continue
        address, _, port = item.lstrip("!").rpartition(",")
        if not address:
            address, port = item.lstrip("!"), "0"
        if port not in ("", "0"):
            notes.append({"code": "remaddr_port_dropped", "address": item})
        try:
            networks.append(str(ipaddress.ip_network(address.strip("[]"), strict=False)))
        except ValueError:
            notes.append({"code": "remaddr_dropped", "address": item})
    return " ".join(networks)


def stable_device(device: str, notes: list[Note]) -> str:
    """A /dev/serial/by-id (else by-path) name for /dev/ttyUSB3 and the like."""
    if device.startswith(("/dev/serial/by-id/", "/dev/serial/by-path/")):
        if not os.path.exists(device):
            notes.append({"code": "device_missing", "device": device})
        return device
    if not os.path.exists(device):
        notes.append({"code": "device_missing", "device": device})
        notes.append({"code": "device_unstable", "device": device})
        return device
    target = os.path.realpath(device)
    for folder in (BY_ID, BY_PATH):
        for link in sorted(glob.glob(f"{folder}/*")):
            if os.path.realpath(link) == target:
                notes.append({"code": "device_renamed", "device": device, "stable": link})
                return link
    notes.append({"code": "device_unstable", "device": device})
    return device


def convert(name: str, definition: dict[str, Any]) -> ImportItem:
    notes: list[Note] = []
    defaults: dict[str, tuple[str, str | None]] = definition.get("defaults", {})
    accepter = _accepter(definition.get("accepter", ""), notes)
    if accepter is None:
        return ImportItem(
            name, None, [{"code": "accepter_unsupported", "accepter": definition.get("accepter")}]
        )
    connector = _connector(definition.get("connector", ""), defaults, notes)
    if connector is None:
        return ImportItem(
            name,
            None,
            [{"code": "connector_unsupported", "connector": definition.get("connector")}],
        )
    del connector["_defaults"]
    connector["device"] = stable_device(connector["device"], notes)
    options = dict(definition.get("options", {}))
    for option, (value, cls) in defaults.items():
        if (
            cls is None
            and option not in options
            and option
            in (
                "max-connections",
                "kickolduser",
                "chardelay",
                "remaddr",
            )
        ):
            options[option] = value
    try:
        values: dict[str, Any] = {
            "name": name[:64],
            **connector,
            **accepter,
            "enabled": _bool(definition.get("enable"), True),
            "timeout": int(definition.get("timeout") or 0),
            "max_clients": int(options.pop("max-connections", "1") or 1),
            "kickolduser": _bool(options.pop("kickolduser", None), False),
            "chardelay": _bool(options.pop("chardelay", None), True),
            "connector_retry_time": int(options.pop("connector-retry-time", "0") or 0),
        }
    except ValueError as err:
        return ImportItem(name, None, [*notes, {"code": "invalid", "errors": {"": str(err)}}])
    for key in ("banner", "openstr", "closestr"):
        if key in options:
            values[key] = options.pop(key)
    if "remaddr" in options:
        values["remaddr"] = _remaddr(options.pop("remaddr"), notes)
    traces = {k: options.pop(k) for k in list(options) if k.startswith("trace-")}
    reads = "trace-read" in traces or "trace-both" in traces
    writes = "trace-write" in traces or "trace-both" in traces
    if reads or writes:
        values["trace"] = "both" if reads and writes else "rx" if reads else "tx"
        notes.append({"code": "trace_files_moved"})
    extra = []
    for key, value in options.items():
        if not OPTION_KEY.fullmatch(key) or key in MANAGED_OPTIONS:
            notes.append({"code": "option_dropped", "option": key})
            continue
        if re.search(r"[*=]\{", value):
            notes.append({"code": "external_file", "option": key})
        extra.append((key, value))
        notes.append({"code": "option_extra", "option": key})
    values["extra"] = tuple(extra)
    try:
        connection = Connection(**values)
        connection.validate()
    except (TypeError, ValueError) as err:
        errors = err.errors if isinstance(err, ValidationError) else {"": str(err)}
        return ImportItem(name, None, [*notes, {"code": "invalid", "errors": errors}])
    return ImportItem(name, connection, notes)


def read(text: str) -> ImportResult:
    """Connections of a ser2net.yaml (version 1 or 2), an old ser2net.conf (version 0) or
    the configuration of ha-modbusproxy / modbus-proxy (modbus_import.py) or the options of
    the EnOcean Proxy app (enocean_import.py)."""
    from . import enocean_import, modbus_import  # they build on this module's types

    if enocean_import.looks_enocean_proxy(text):
        return enocean_import.read(text)
    if modbus_import.looks_modbus_proxy(text):
        return modbus_import.read(text)
    if legacy.looks_legacy(text):
        version = 0
        raw, notes = legacy.parse(text)
    else:
        version, raw, notes = parse(text)
    if not raw:
        notes.append({"code": "no_connections"})
    return ImportResult(version, [convert(name, d) for name, d in raw], notes)


def same_device(a: Connection, b: Connection) -> bool:
    """Do both connections use one device (a serial device, or a Modbus device's address)?"""
    if a.uses_device and b.uses_device:
        return a.device == b.device
    remote = [x for x in (a, b) if x.remote]
    return len(remote) == 2 and (a.host.lower(), a.host_port) == (b.host.lower(), b.host_port)


def conflicts(current: AppConfig, item: ImportItem) -> dict[str, str]:
    """Existing connections the item collides with: {"port"|"device"|"name": name}."""
    c = item.connection
    if c is None:
        return {}
    found: dict[str, str] = {}
    for existing in current.connections:
        if existing.port == c.port:
            found.setdefault("port", existing.name)
        if same_device(existing, c):
            found.setdefault("device", existing.name)
        if existing.name.casefold() == c.name.casefold():
            found.setdefault("name", existing.name)
    return found


def merge(
    current: AppConfig,
    result: ImportResult,
    *,
    replace_all: bool,
    take: set[str],
    on_conflict: dict[str, str],
) -> AppConfig:
    """The configuration after the import.

    take: aliases to import. on_conflict per alias: "replace" (the existing connections it
    collides with go; it keeps the id of one of them, so its clients stay if nothing else
    changed), "new_port" (only for a port collision: the next free port) or "skip".
    """
    base = AppConfig(current.settings) if replace_all else current
    connections = list(base.connections)
    for item in result.items:
        if item.alias not in take or item.connection is None:
            continue
        c = item.connection
        found = {} if replace_all else conflicts(AppConfig(connections=tuple(connections)), item)
        choice = on_conflict.get(item.alias, "skip") if found else "add"
        if choice == "skip":
            continue
        if choice == "new_port":
            if set(found) - {"port", "name"}:
                continue  # a device can serve one connection only
            used = {x.port for x in connections} | RESERVED_PORTS.keys()
            port = c.port
            while port in used:
                port += 1
            if port > 65535:
                continue  # no free port above: skipped, the rest of the import still goes
            c = replace(c, port=port)
        elif choice == "replace":
            gone = [
                x
                for x in connections
                if x.port == c.port or same_device(x, c) or x.name.casefold() == c.name.casefold()
            ]
            if gone:
                c = replace(c, id=gone[0].id)
            connections = [x for x in connections if x not in gone]
        names = {x.name.casefold() for x in connections}
        name, number = c.name, 2
        while name.casefold() in names:
            name, number = f"{c.name} ({number})", number + 1
        connections.append(replace(c, name=name))
    config = AppConfig(base.settings, tuple(connections))
    config.validate()
    return config
