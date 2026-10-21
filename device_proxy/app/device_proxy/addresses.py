"""The addresses clients use to reach a connection, per kind of client.

Home Assistant Core runs in the host network and reaches the app on 127.0.0.1; other apps
run in the Supervisor network and reach the host on 172.30.32.1; programs elsewhere use the
host's LAN address. A connection limited to this host ("local") is only reachable by Core.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Any

from .model import Connection, Settings, client_allowed

_LOGGER = logging.getLogger(__name__)

SUPERVISOR_HOST = "172.30.32.1"  # the host as seen from apps in the Supervisor network
APP_SOURCE = "172.30.33.2"  # a typical source address of another app


def _allowed(c: Connection, settings: Settings, source: str) -> bool:
    return client_allowed(c.remaddr, settings.listen, source)


def addresses(c: Connection, settings: Settings, lan_ip: str | None) -> list[dict[str, Any]]:
    local = (settings.listen == "local" and not c.bind) or c.bind.startswith("127.")
    fixed = c.bind if c.bind and not c.bind.startswith("127.") else None
    targets = [
        ("ha", fixed or "127.0.0.1", "127.0.0.1", True),
        ("apps", fixed or SUPERVISOR_HOST, APP_SOURCE, not local),
        ("lan", fixed or lan_ip, lan_ip, not local and (fixed or lan_ip) is not None),
    ]
    result = []
    for target, host, source, reachable in targets:
        if host is None:
            result.append({"target": target, "reachable": False, "urls": {}})
            continue
        if reachable and source:
            reachable = _allowed(c, settings, source)
        shown = f"[{host}]" if ":" in host else host
        if c.kind == "modbus":
            urls = {"modbus": f"{shown}:{c.port}"}
        elif c.mode == "rfc2217":
            urls = {"rfc2217": f"rfc2217://{shown}:{c.port}"}
        else:
            urls = {"tcp": f"tcp://{shown}:{c.port}", "socket": f"socket://{shown}:{c.port}"}
        result.append(
            {"target": target, "host": host, "port": c.port, "reachable": reachable, "urls": urls}
        )
    return result


def host_lan_ip() -> str | None:
    """The host's primary IPv4 address from the Supervisor (needs hassio_api)."""
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        return None
    request = urllib.request.Request(
        "http://supervisor/network/info", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.load(response).get("data", {})
    except (OSError, ValueError) as err:
        _LOGGER.warning("Could not read the host's address from the Supervisor: %s", err)
        return None
    for interface in data.get("interfaces", []):
        if interface.get("primary"):
            for address in (interface.get("ipv4") or {}).get("address", []):
                return str(address).split("/")[0]
    return None
