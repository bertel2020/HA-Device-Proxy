"""Reads the configuration of the ha-modbusproxy app or of modbus-proxy into Modbus connections.

ha-modbusproxy (its options, as the app's configuration tab shows them in YAML):

    devices:
      - upstreamhost: 192.168.1.10
        upstreamport: 502
        listenport: 502
        timeout: 10
        connection_time: 0.1

or one device as upstreamhost / upstreamport / listenport at the top. modbus-proxy's own
file has devices with modbus: {url, timeout, connection_time} and listen: {bind}. Timeouts
are seconds there, milliseconds here.
"""

from __future__ import annotations

from typing import Any

import yaml

from .importer import ImportItem, ImportResult, Note
from .model import Connection, ValidationError

HA_MODBUSPROXY = 10  # ImportResult.version of the two formats
MODBUS_PROXY = 11
KNOWN = {"upstreamhost", "upstreamport", "listenport", "timeout", "connection_time"}


def _load(text: str) -> Any:
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return None


def looks_modbus_proxy(text: str) -> bool:
    data = _load(text)
    if not isinstance(data, dict):
        return False
    if "upstreamhost" in data:
        return True
    devices = data.get("devices")
    return isinstance(devices, list) and any(
        isinstance(d, dict) and ("upstreamhost" in d or "modbus" in d) for d in devices
    )


def _split(url: str) -> tuple[str, int]:
    """modbus-proxy's "host:port" or "tcp://host:port"."""
    url = url.split("://", 1)[-1]
    if url.startswith("["):
        host, _, rest = url[1:].partition("]")
        return host, int(rest.lstrip(":") or 502)
    host, _, port = url.rpartition(":")
    return (host, int(port)) if host else (url, 502)


def _ms(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    return round(float(value) * 1000)


def _item(
    host: str,
    port: int,
    listen: int,
    timeout: Any,
    delay: Any,
    *,
    bind: str = "",
    unit_map: str = "",
    notes: list[Note] | None = None,
) -> ImportItem:
    alias = f"{host}:{port}"
    notes = notes or []
    values = {
        "name": f"Modbus {host}",
        "device": "",
        "port": listen,
        "kind": "modbus",
        "template": "modbus",
        "link": "tcp",
        "host": host,
        "host_port": port,
        "max_clients": 10,
        "request_timeout_ms": min(max(_ms(timeout, 10000), 100), 60000),
        "connect_delay_ms": min(max(_ms(delay, 0), 0), 10000),
        "bind": "" if bind in ("", "0", "0.0.0.0", "::") else bind,
        "unit_map": unit_map,
        "write_access": "all",  # as before the move: ha-modbusproxy lets every client write
    }
    try:
        return ImportItem(alias, Connection.from_dict(values), notes)
    except ValidationError as err:
        return ImportItem(alias, None, [*notes, {"code": "invalid", "errors": err.errors}])


def read(text: str) -> ImportResult:
    data = _load(text)
    assert isinstance(data, dict)
    notes: list[Note] = [{"code": "modbus_stop_old"}]
    items: list[ImportItem] = []
    devices = [d for d in data.get("devices") or [] if isinstance(d, dict)]
    if any("modbus" in d for d in devices):
        for d in devices:
            modbus, listen = d.get("modbus") or {}, d.get("listen") or {}
            taken = ("modbus", "listen", "unit_id_remapping")
            dropped = [{"code": "option_dropped", "option": k} for k in d if k not in taken]
            remap = d.get("unit_id_remapping") or {}
            unit_map = (
                ", ".join(f"{k}={v}" for k, v in remap.items()) if isinstance(remap, dict) else ""
            )
            try:
                host, port = _split(str(modbus.get("url", "")))
                bind, listen_port = _split(str(listen.get("bind", ":502")))
            except ValueError:
                items.append(
                    ImportItem(
                        str(modbus.get("url", "?")),
                        None,
                        [{"code": "invalid", "errors": {"url": "not host:port"}}],
                    )
                )
                continue
            items.append(
                _item(
                    host,
                    port,
                    listen_port,
                    modbus.get("timeout"),
                    modbus.get("connection_time"),
                    bind=bind,
                    unit_map=unit_map,
                    notes=dropped,
                )
            )
        return ImportResult(MODBUS_PROXY, items, notes)
    timeout, delay = data.get("timeout"), data.get("connection_time")
    if not devices and data.get("upstreamhost"):
        devices = [data]
    for d in devices:
        dropped = [{"code": "option_dropped", "option": k} for k in d if k not in KNOWN]
        try:
            items.append(
                _item(
                    str(d.get("upstreamhost", "")),
                    int(d.get("upstreamport", 502)),
                    int(d.get("listenport", 502)),
                    d.get("timeout", timeout),
                    d.get("connection_time", delay),
                    notes=dropped if d is not data else [],
                )
            )
        except (TypeError, ValueError):
            items.append(
                ImportItem(
                    str(d.get("upstreamhost", "?")),
                    None,
                    [{"code": "invalid", "errors": {"": "port is not a number"}}],
                )
            )
    if not items:
        notes.append({"code": "no_connections"})
    return ImportResult(HA_MODBUSPROXY, items, notes)
