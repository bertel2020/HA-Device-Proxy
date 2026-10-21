"""Reads the options of the EnOcean Proxy app (HA-Enocean-Proxy) into EnOcean connections.

As the app's configuration tab shows them in YAML (or as JSON from the Supervisor):

    gateways:
      - name: FAM-USB
        device: /dev/serial/by-id/usb-...     # or tcp://192.168.1.50:5100
        baudrate: 9600
        protocol: esp2
        port: 9100
    send_gap_ms: 10
    replay_size: 1000
    replay_max_age_s: 900
    allowed_clients: []

The app's options were global; here every gateway gets them. Its ports were only open in the
Supervisor's network; this app runs in the host network, so the gateways take Home Assistant
and the other apps only, plus the allowed_clients the old app had.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import urllib.error
import urllib.request
from typing import Any

import yaml

from .importer import ImportItem, ImportResult, Note
from .model import Connection, ValidationError, parse_networks

ENOCEAN_PROXY = 12  # ImportResult.version of the format
SLUG = "enocean_proxy"  # the app's slug, after the repository's prefix
REPOSITORY = "https://github.com/bertel2020/HA-Enocean-Proxy"
HA_ONLY = "127.0.0.1, 172.30.32.0/23"
KNOWN = {"name", "device", "baudrate", "protocol", "port"}
GLOBAL = {
    "gateways",
    "send_gap_ms",
    "replay_size",
    "replay_max_age_s",
    "allowed_clients",
    "log_level",
}


def _load(text: str) -> Any:
    try:
        return yaml.safe_load(text)  # JSON is YAML too
    except yaml.YAMLError:
        return None


def looks_enocean_proxy(text: str) -> bool:
    data = _load(text)
    if not isinstance(data, dict):
        return False
    gateways = data.get("gateways")
    return isinstance(gateways, list) and any(
        isinstance(g, dict) and g.get("protocol") in ("esp2", "esp3") for g in gateways
    )


def _template(protocol: str, link: str, baud: int, port: int) -> str:
    if link == "tcp":
        return {5100: "mgw_eth", 5000: "symcon_lan"}.get(port, "enocean")
    if protocol == "esp3":
        return "usb300" if baud == 57600 else "enocean"
    return "fam_usb" if baud == 9600 else "enocean"  # FAM14 or FGW14-USB: both 57600


def _remaddr(allowed: Any, notes: list[Note]) -> str:
    entries = [str(a).strip() for a in allowed or [] if str(a).strip()]
    if not entries:
        return HA_ONLY
    try:
        parse_networks(", ".join(entries))
    except ValueError as err:
        notes.append({"code": "enocean_allowed_dropped", "error": str(err)})
        return HA_ONLY
    # the old list applied to everyone; Home Assistant must still get in
    return ", ".join(dict.fromkeys([*HA_ONLY.split(", "), *entries]))


def read(text: str) -> ImportResult:
    data = _load(text)
    assert isinstance(data, dict)
    notes: list[Note] = [{"code": "enocean_stop_old"}, {"code": "enocean_lan"}]
    shared: dict[str, Any] = {}
    for key in ("send_gap_ms", "replay_size", "replay_max_age_s"):
        if isinstance(data.get(key), int):
            shared[key] = data[key]
    remaddr = _remaddr(data.get("allowed_clients"), notes)
    notes += [{"code": "option_dropped", "option": k} for k in data if k not in GLOBAL]
    items: list[ImportItem] = []
    for g in data.get("gateways") or []:
        if not isinstance(g, dict):
            continue
        name = str(g.get("name") or "EnOcean")
        item_notes: list[Note] = [
            {"code": "option_dropped", "option": k} for k in g if k not in KNOWN
        ]
        device = str(g.get("device") or "")
        protocol = str(g.get("protocol") or "esp2")
        try:
            baud = int(g.get("baudrate") or 57600)  # the old app's default
            port = int(g.get("port") or 9100)
        except (TypeError, ValueError):
            items.append(
                ImportItem(
                    name,
                    None,
                    [{"code": "invalid", "errors": {"": "port or baud rate is not a number"}}],
                )
            )
            continue
        values: dict[str, Any] = {
            "name": name,
            "port": port,
            "kind": "enocean",
            "esp_protocol": protocol,
            "baud": baud,
            "max_clients": 10,  # the old app had no limit
            "remaddr": remaddr,
            **shared,
        }
        if device.startswith("tcp://"):
            host, _, number = device.removeprefix("tcp://").rstrip("/").rpartition(":")
            host_port = int(number) if number.isdigit() else 0
            values.update(link="tcp", device="", host=host.strip("[]"), host_port=host_port)
        else:
            values.update(link="serial", device=device)
        values["template"] = _template(protocol, values["link"], baud, values.get("host_port", 0))
        try:
            items.append(ImportItem(name, Connection.from_dict(values), item_notes))
        except ValidationError as err:
            items.append(
                ImportItem(name, None, [*item_notes, {"code": "invalid", "errors": err.errors}])
            )
    if not items:
        notes.append({"code": "no_connections"})
    return ImportResult(ENOCEAN_PROXY, items, notes)


# the options straight from the Supervisor


def _supervisor(path: str) -> Any:
    request = urllib.request.Request(
        f"http://supervisor{path}",
        headers={"Authorization": f"Bearer {os.environ['SUPERVISOR_TOKEN']}"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())


def candidates() -> list[str]:
    """Slugs the app may have: a custom repository's apps are "<hash>_<slug>", the hash being
    the first 8 hex digits of the SHA-1 of the repository's URL; "local_" for a local copy."""
    return [
        f"{hashlib.sha1(url.lower().encode()).hexdigest()[:8]}_{SLUG}"
        for url in (REPOSITORY, f"{REPOSITORY}.git")
    ] + [f"local_{SLUG}"]


def _fetch() -> dict[str, Any]:
    if "SUPERVISOR_TOKEN" not in os.environ:
        raise LookupError("not running as a Home Assistant app")
    try:  # the list needs more rights than an app has by default: then the known slugs
        apps = _supervisor("/addons")["data"]["addons"]
        slugs = [a["slug"] for a in apps if a["slug"] == SLUG or a["slug"].endswith(f"_{SLUG}")]
    except urllib.error.HTTPError:
        slugs = candidates()
    for slug in slugs:
        try:
            data = _supervisor(f"/addons/{slug}/info")["data"]
            break
        except urllib.error.HTTPError:
            continue
    else:
        raise LookupError("the EnOcean Proxy app is not installed")
    options = data.get("options")
    if not isinstance(options, dict):
        raise LookupError("the Supervisor does not show its options")
    return {"slug": slug, "state": data.get("state"), "options": options}


async def fetch_options() -> dict[str, Any]:
    """{slug, state, text}: the EnOcean Proxy app's options as YAML for the import."""
    try:
        found = await asyncio.to_thread(_fetch)
    except (OSError, KeyError, TypeError, ValueError) as err:
        raise LookupError(f"the Supervisor did not answer: {err}") from None
    text = yaml.safe_dump(found["options"], allow_unicode=True, sort_keys=False)
    return {"slug": found["slug"], "state": found["state"], "text": text}
