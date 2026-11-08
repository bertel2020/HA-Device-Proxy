"""Names for client addresses, and the clients never seen before.

The ports have no login, so a host that connects for the first time is worth a look: it is
kept as "new" (an event, a notification) until it is marked as known in the web interface or
given a name. Home Assistant, its apps and this host count as known. When the app starts
without a list of known hosts (a fresh install, an update from before), it learns quietly for
a while: the clients that connect then are taken as known.

A blocked host is kept out of every connection until it is released in the web interface.
"""

from __future__ import annotations

import ipaddress
import json
import logging
import time
from collections.abc import Callable
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

PATH = Path("/data/known_clients.json")
LEARN_SECONDS = 600  # quiet learning after a start without the file
# the Supervisor's network, IPv4 and IPv6: the apps
APPS_NETWORKS = (
    ipaddress.ip_network("172.30.32.0/23"),
    ipaddress.ip_network("fd0c:ac1e:2100::/48"),
)


def host_of(address: str) -> str:
    """The host of "192.168.1.20:50114" or "[fe80::1]:50114"."""
    if address.startswith("["):
        return address[1:].split("]", 1)[0]
    return address.rsplit(":", 1)[0] if address.count(":") == 1 else address


def plain_host(host: str) -> str:
    """The form of an address the lists use: no zone, an IPv4 client on an IPv6 socket as IPv4;
    anything that is no address stays as it is."""
    try:
        ip = ipaddress.ip_address(host.split("%")[0])
    except ValueError:
        return host
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return str(ip)


def parse_names(text: str) -> dict[str, str]:
    """ "192.168.1.20 evcc" per line → {"192.168.1.20": "evcc"}; raises ValueError."""
    names: dict[str, str] = {}
    for number, line in enumerate(text.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        host, _, name = line.partition(" ")
        try:
            host = str(ipaddress.ip_address(host))
        except ValueError:
            raise ValueError(f"line {number}: an IP address first, then the name") from None
        if not name.strip():
            raise ValueError(f"line {number}: a name after the address")
        names[host] = name.strip()
    return names


def is_local(host: str, own: str | None = None) -> bool:
    """Home Assistant, its apps or this host itself."""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return (
        ip.is_loopback
        or any(ip in n for n in APPS_NETWORKS if n.version == ip.version)
        or host == own
    )


class KnownClients:
    def __init__(self, path: Path = PATH, *, clock: Callable[[], float] = time.time) -> None:
        self.path = path
        self.clock = clock
        self.known: dict[str, float] = {}  # host → first seen
        self.new: dict[str, dict[str, object]] = {}  # host → first seen, connection, address
        self.blocked: dict[str, float] = {}  # host → since when; the proxies read this one
        self.learn_until = 0.0
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.known = {str(k): float(v) for k, v in data.get("known", {}).items()}
            self.new = {str(k): dict(v) for k, v in data.get("new", {}).items()}
            self.blocked = {str(k): float(v) for k, v in data.get("blocked", {}).items()}
        except FileNotFoundError:
            self.learn_until = self._now() + LEARN_SECONDS
        except (OSError, ValueError, AttributeError, TypeError) as err:
            _LOGGER.warning("Known clients not read (%s), learning them again", err)
            self.learn_until = self._now() + LEARN_SECONDS

    def _now(self) -> float:
        return self.clock()

    def seen(
        self, address: str, connection: str, names: dict[str, str], own: str | None = None
    ) -> bool:
        """A client connected: True when its host is new (and was not new before)."""
        host = host_of(address)
        if (
            host in self.known
            or host in self.new
            or host in self.blocked
            or host in names
            or is_local(host, own)
        ):
            return False
        now = self._now()
        if now < self.learn_until:
            self.known[host] = now
            self._save()
            return False
        self.new[host] = {"first": now, "connection": connection, "address": address}
        self._save()
        return True

    def acknowledge(self, host: str) -> bool:
        """Marked as known in the web interface."""
        entry = self.new.pop(host, None)
        if entry is None:
            return False
        self.known[host] = float(entry.get("first", self._now()))  # type: ignore[arg-type]
        self._save()
        return True

    def named(self, names: dict[str, str]) -> None:
        """A name makes a new host known."""
        for host in [h for h in self.new if h in names]:
            self.acknowledge(host)

    def block(self, host: str) -> bool:
        """Blocked in the web interface; False when it already is."""
        if host in self.blocked:
            return False
        self.new.pop(host, None)
        self.known.pop(host, None)
        self.blocked[host] = self._now()
        self._save()
        return True

    def unblock(self, host: str) -> bool:
        """Released in the web interface: it counts as known, it was looked at."""
        if self.blocked.pop(host, None) is None:
            return False
        self.known[host] = self._now()
        self._save()
        return True

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            data = {"known": self.known, "new": self.new, "blocked": self.blocked}
            tmp.write_text(json.dumps(data), encoding="utf-8")
            tmp.replace(self.path)
        except OSError as err:
            _LOGGER.warning("Known clients not saved: %s", err)
