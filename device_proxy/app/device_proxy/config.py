"""The ser2net.yaml the app hands to ser2net, built from its connections.

ser2net reads it at start and again on reload; a reload only touches the connections whose
block changed, so the others keep their clients. Each connection is named by its stable
alias (c_<id>), so renaming it changes nothing for ser2net. The admin interface listens on
a Unix socket readable by the container's root only.
"""

from __future__ import annotations

import re
import time
import unicodedata

from .model import ADMIN_SOCKET, PRIVATE_NETWORKS, AppConfig, Connection, parse_networks
from .trace import trace_path

HEADER = "# Written by the Device Proxy app. Changes here are overwritten on the next save."


ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def scalar(value: str) -> str:
    """A YAML scalar; double-quoted with escapes when a plain one would be read differently."""
    if value and re.fullmatch(r"[A-Za-z0-9_./,()=+@-][A-Za-z0-9_./,:()=+@ -]*", value):
        if ": " not in value and not value.endswith(" "):
            return value
    quoted = "".join(
        ESCAPES.get(ch, f"\\x{ord(ch):02x}" if ord(ch) < 0x20 or ord(ch) == 0x7F else ch)
        for ch in value
    )
    return f'"{quoted}"'


def accepter(c: Connection, listen: str) -> str:
    stack = {"raw": "", "rfc2217": "telnet(rfc2217),", "telnet": "telnet,"}[c.mode]
    tcp = "tcp(nodelay)" if c.nodelay else "tcp"
    bind = c.bind or ("127.0.0.1" if listen == "local" else "")
    return f"{stack}{tcp},{bind + ',' if bind else ''}{c.port}"


def connector(c: Connection) -> str:
    flags = [
        name
        for name, on in (
            ("local", c.local),
            ("rtscts", c.rtscts),
            ("xonxoff", c.xonxoff),
            ("hangup-when-done", c.hangup_when_done),
            ("nobreak", c.nobreak),
        )
        if on
    ]
    flags += [f"{line}={state}" for line, state in (("dtr", c.dtr), ("rts", c.rts)) if state]
    if c.rs485:
        flags.append(f"rs485={c.rs485}")
    return ",".join(["serialdev", c.device, c.serial_format, *flags])


def remaddr(c: Connection, listen: str) -> str:
    """ser2net's remaddr: networks with port 0 (any client port), or "" for no limit."""
    if c.remaddr:
        networks = [str(n) for n in parse_networks(c.remaddr)]
        if c.keep_open and not any(n.startswith("127.") for n in networks):
            networks.append("127.0.0.1/32")  # the app's own client
    elif listen == "lan":
        networks = list(PRIVATE_NETWORKS)
    else:
        return ""  # "local" is limited by the bind address, "all" has no limit
    return ";".join(f"{n},0" for n in networks)


def block(c: Connection, listen: str, *, trace: bool = True) -> str:
    """The connection's part of ser2net.yaml; trace: the app's always-on trace (trace.py)."""
    lines = [
        f"connection: &{c.alias}",
        f"  accepter: {scalar(accepter(c, listen))}",
        f"  enable: {'on' if c.enabled else 'off'}",
    ]
    if c.timeout:
        lines.append(f"  timeout: {c.timeout}")
    lines += [f"  connector: {scalar(connector(c))}", "  options:"]
    options: list[tuple[str, str]] = [("max-connections", str(c.max_clients))]
    if c.kickolduser:
        options.append(("kickolduser", "true"))
    if not c.chardelay:
        options.append(("chardelay", "false"))
    if c.connector_retry_time:
        options.append(("connector-retry-time", str(c.connector_retry_time)))
    if limit := remaddr(c, listen):
        options.append(("remaddr", limit))
    for key in ("banner", "openstr", "closestr"):
        if value := getattr(c, key):
            options.append((key, value))
    options += list(c.extra)
    if trace:
        options += [
            ("trace-both", str(trace_path(c.alias))),
            ("trace-hexdump", "true"),
            ("trace-timestamp", "true"),
        ]
    lines += [f"    {key}: {scalar(value)}" for key, value in options]
    return "\n".join(lines) + "\n"


def blocks(config: AppConfig) -> dict[str, str]:
    """Alias → block, to tell which connections a change touches."""
    return {c.alias: block(c, config.settings.listen) for c in config.serial}


def render(config: AppConfig, admin_socket: str = ADMIN_SOCKET) -> str:
    unix = f"unix(delsock,umode=6,gmode=0,omode=0),{admin_socket}"
    parts = [
        "%YAML 1.1\n---\n" + HEADER + "\n",
        f"admin:\n  accepter: {scalar(unix)}\n",
        *blocks(config).values(),
    ]
    return "\n".join(parts)


def changed(old: dict[str, str], new: dict[str, str]) -> set[str]:
    """Aliases whose block differs, including added and removed ones."""
    return {alias for alias in old.keys() | new.keys() if old.get(alias) != new.get(alias)}


UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def readable_alias(name: str, taken: set[str]) -> str:
    """A ser2net name for an exported connection: its name, made safe and unique."""
    text = unicodedata.normalize("NFKD", name.lower().translate(UMLAUTS))
    base = re.sub(r"[^a-z0-9]+", "_", text.encode("ascii", "ignore").decode()).strip("_")
    candidate, number = base or "connection", 2
    while candidate in taken:
        candidate, number = f"{base or 'connection'}_{number}", number + 1
    taken.add(candidate)
    return candidate


def export(config: AppConfig, *, include_disabled: bool = True) -> str:
    """The connections as a ser2net.yaml for any ser2net 4 (without the app's admin socket)."""
    stamp = time.strftime("%Y-%m-%d %H:%M")
    parts = [f"%YAML 1.1\n---\n# Exported from the Device Proxy app on {stamp}\n"]
    taken: set[str] = set()
    for c in config.serial:  # the Modbus proxy is the app's own, not ser2net's
        if c.enabled or include_disabled:
            text = block(c, config.settings.listen, trace=False)
            parts.append(text.replace(f"&{c.alias}", f"&{readable_alias(c.name, taken)}", 1))
    return "\n".join(parts)
