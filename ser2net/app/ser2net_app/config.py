"""The ser2net.yaml the app hands to ser2net, built from its connections.

ser2net reads it at start and again on SIGHUP; a reload only touches the connections that
changed, so the others keep their clients. The admin port is bound to the loopback address
only: the app reads status from it, nobody else can reach it.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

ADMIN_PORT = 18398
UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
MODES = ("raw", "rfc2217", "telnet")
PARITIES = ("n", "e", "o")
HEADER = "# Written by the Ser2Net app. Changes here are overwritten on the next save.\n"


@dataclass(frozen=True)
class Connection:
    name: str
    device: str
    port: int
    baud: int = 9600
    data_bits: int = 8
    parity: str = "n"
    stop_bits: int = 1
    mode: str = "raw"
    max_clients: int = 1
    enabled: bool = True
    bind: str | None = None  # None: all addresses
    serial_flags: tuple[str, ...] = ("local",)
    options: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 1 <= self.port <= 65535:
            raise ValueError(f"{self.name}: port {self.port} is not between 1 and 65535")
        if self.mode not in MODES:
            raise ValueError(f"{self.name}: mode {self.mode!r} is not one of {', '.join(MODES)}")
        if self.parity not in PARITIES:
            raise ValueError(f"{self.name}: parity {self.parity!r} is not n, e or o")
        if self.data_bits not in (5, 6, 7, 8) or self.stop_bits not in (1, 2):
            raise ValueError(f"{self.name}: format {self.serial_format} is not valid")
        if self.max_clients < 1:
            raise ValueError(f"{self.name}: max_clients must be at least 1")

    @property
    def serial_format(self) -> str:
        return f"{self.baud}{self.parity}{self.data_bits}{self.stop_bits}"

    @property
    def accepter(self) -> str:
        stack = {"raw": "", "rfc2217": "telnet(rfc2217),", "telnet": "telnet,"}[self.mode]
        address = f"{self.bind}," if self.bind else ""
        return f"{stack}tcp,{address}{self.port}"

    @property
    def connector(self) -> str:
        return ",".join(["serialdev", self.device, self.serial_format, *self.serial_flags])


def alias(name: str, taken: set[str]) -> str:
    """A YAML anchor for the connection name, unique among the ones already taken."""
    text = name.lower().translate(UMLAUTS)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "_", text).strip("_") or "connection"
    candidate, number = base, 2
    while candidate in taken:
        candidate, number = f"{base}_{number}", number + 1
    taken.add(candidate)
    return candidate


def scalar(value: str) -> str:
    """A YAML scalar; quoted when a plain one would be read differently."""
    if value and re.fullmatch(r"[A-Za-z0-9_./,()=+@-][A-Za-z0-9_./,:()=+@ -]*", value):
        if ": " not in value and not value.endswith(" "):
            return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(connections: list[Connection], admin_port: int = ADMIN_PORT) -> str:
    ports = [c.port for c in connections]
    if len(set(ports)) != len(ports):
        raise ValueError("two connections use the same port")
    lines = ["%YAML 1.1", "---", HEADER.rstrip("\n"), ""]
    lines += ["admin:", f"  accepter: tcp,127.0.0.1,{admin_port}", ""]
    taken: set[str] = set()
    for c in connections:
        lines += [
            f"connection: &{alias(c.name, taken)}",
            f"  accepter: {scalar(c.accepter)}",
            f"  enable: {'on' if c.enabled else 'off'}",
            f"  connector: {scalar(c.connector)}",
            "  options:",
            f"    max-connections: {c.max_clients}",
        ]
        lines += [f"    {key}: {scalar(value)}" for key, value in c.options]
        lines.append("")
    return "\n".join(lines)
