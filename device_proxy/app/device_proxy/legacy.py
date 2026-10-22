"""Reads the old ser2net 3 format (ser2net.conf) into the same definitions as ser2net.yaml.

<network port>:<state>:<timeout>:<device>:<options>, plus BANNER:, OPENSTR:, CLOSESTR:,
CLOSEON:, SIGNATURE:, TRACEFILE:, DEVICE: and DEFAULT: lines (a default applies to the lines
after it). Each port line becomes a version 4 definition (accepter, connector, options), so
the import treats both formats alike.
"""

from __future__ import annotations

import re
from typing import Any

Note = dict[str, Any]

STATES = ("raw", "rawlp", "telnet", "off")
PORT_LINE = re.compile(r"^[^:#\s][^:\n]*:(raw|rawlp|telnet|off):\d+:", re.MULTILINE)
NAMED = ("BANNER", "SIGNATURE", "OPENSTR", "CLOSESTR", "CLOSEON", "TRACEFILE", "DEVICE")
PARITY = {"NONE": "n", "EVEN": "e", "ODD": "o", "MARK": "m", "SPACE": "s"}
FLAGS = {
    "XONXOFF": "xonxoff",
    "RTSCTS": "rtscts",
    "LOCAL": "local",
    "NOBREAK": "nobreak",
    "HANGUP_WHEN_DONE": "hangup-when-done",
}
VALUE_OPTIONS = (
    "max-connections",
    "remaddr",
    "chardelay-scale",
    "chardelay-min",
    "chardelay-max",
    "dev-to-net-bufsize",
    "net-to-dev-bufsize",
)
DEFAULT_KEYS = {
    "speed",
    "databits",
    "stopbits",
    "parity",
    "xonxoff",
    "rtscts",
    "local",
    "hangup_when_done",
    "nobreak",
    "remctl",
    "telnet_brk_on_sync",
    "kickolduser",
    "chardelay",
    "chardelay-scale",
    "chardelay-min",
    "chardelay-max",
}


def looks_legacy(text: str) -> bool:
    return bool(PORT_LINE.search(text)) and not re.search(
        r"^\s*(connection|connections)\s*:", text, re.MULTILINE
    )


def _lines(text: str) -> list[str]:
    """Lines with continuations (a trailing backslash) joined and comments dropped."""
    joined, current = [], ""
    for raw in text.splitlines():
        if raw.endswith("\\"):
            current += raw[:-1]
            continue
        current += raw
        stripped = current.strip()
        if stripped and not stripped.startswith("#"):
            joined.append(stripped)
        current = ""
    if current.strip():
        joined.append(current.strip())
    return joined


def _split_port_line(line: str) -> list[str] | None:
    """Split at the first four colons outside the port's IPv6 address and the options."""
    match = re.match(r"^(.*?):(raw|rawlp|telnet|off):(\d+):(.*)$", line)
    if not match:
        return None
    port, state, timeout, rest = match.groups()
    device, sep, options = rest.partition(":")
    if device.startswith("sol."):
        return [port, state, timeout, rest, ""]
    return [port, state, timeout, device, options if sep else ""]


def _accepter(port: str, state: str, remctl: bool) -> str | None:
    parts = [p.strip() for p in port.split(",") if p.strip()]
    parts = [p for p in parts if p not in ("ipv4", "ipv6", "tcp")]
    if any(p == "udp" for p in parts) or not parts or not parts[-1].isdigit():
        return None
    address = ",".join(parts)
    if state == "telnet":
        return f"telnet(rfc2217),tcp,{address}" if remctl else f"telnet,tcp,{address}"
    return f"telnet(rfc2217),tcp,{address}" if remctl else f"tcp,{address}"


def parse(text: str) -> tuple[list[tuple[str, dict[str, Any]]], list[Note]]:
    named: dict[str, dict[str, str]] = {key: {} for key in NAMED}
    defaults: dict[str, str] = {}
    notes: list[Note] = []
    raw: list[tuple[str, dict[str, Any]]] = []
    for line in _lines(text):
        head, _, rest = line.partition(":")
        if head in NAMED:
            name, _, value = rest.partition(":")
            named[head][name] = value
            continue
        if head == "DEFAULT":
            key, _, value = rest.partition(":")
            if key in DEFAULT_KEYS:
                defaults[key] = value
            else:
                notes.append({"code": "default_ignored", "name": key})
            continue
        if head == "CONTROLPORT":
            notes.append({"code": "admin_ignored"})
            continue
        if head in ("ROTATOR", "LED"):
            notes.append({"code": "section_ignored", "section": head.lower()})
            continue
        fields = _split_port_line(line)
        if fields is None:
            notes.append({"code": "line_unreadable", "line": line[:80]})
            continue
        port, state, timeout, device, options = fields
        raw.append(_definition(port, state, timeout, device, options, named, defaults, notes))
    return raw, notes


def _definition(
    port: str,
    state: str,
    timeout: str,
    device: str,
    options: str,
    named: dict[str, dict[str, str]],
    defaults: dict[str, str],
    notes: list[Note],
) -> tuple[str, dict[str, Any]]:
    device_name = device
    device = named["DEVICE"].get(device, device)
    speed = defaults.get("speed", "9600")
    parity = PARITY.get(defaults.get("parity", "NONE").upper(), "n")
    data_bits = defaults.get("databits", "8")
    stop_bits = defaults.get("stopbits", "1")
    flags = {flag: _on(defaults.get(flag.replace("-", "_"))) for flag in FLAGS.values()}
    remctl = _on(defaults.get("remctl"))
    opts: dict[str, str] = {}
    for key in ("kickolduser", "telnet_brk_on_sync"):
        if _on(defaults.get(key)):
            opts[key.replace("_", "-")] = "true"
    if key_value := defaults.get("chardelay"):
        opts["chardelay"] = "true" if _on(key_value) else "false"
    for key in ("chardelay-scale", "chardelay-min", "chardelay-max"):
        if key in defaults:
            opts[key] = defaults[key]
    for token in options.split():
        off = token.startswith("-")
        word = token.lstrip("-")
        upper = word.upper()
        key, has_value, value = word.partition("=")
        if word.isdigit():
            speed = word
        elif upper in PARITY:
            parity = PARITY[upper]
        elif re.fullmatch(r"[5-8]DATABITS", upper):
            data_bits = upper[0]
        elif upper in ("1STOPBIT", "2STOPBITS"):
            stop_bits = upper[0]
        elif upper in FLAGS:
            flags[FLAGS[upper]] = not off
        elif word == "remctl":
            remctl = not off
        elif word in ("kickolduser", "telnet_brk_on_sync"):
            opts[word.replace("_", "-")] = "false" if off else "true"
        elif word == "disable-chardelay":
            opts["chardelay"] = "true" if off else "false"
        elif has_value and key in ("tr", "tw", "tb"):
            option = {"tr": "trace-read", "tw": "trace-write", "tb": "trace-both"}[key]
            opts[option] = named["TRACEFILE"].get(value, value)
        elif has_value and key in VALUE_OPTIONS:
            opts[key] = value
        elif re.fullmatch(r"(tr-|tw-|tb-)?(hexdump|timestamp)", word):
            continue  # the app's own traces always have both
        elif has_value and key in ("led-tx", "led-rx"):
            notes.append({"code": "option_dropped", "option": key})
        elif word in named["BANNER"]:
            opts["banner"] = named["BANNER"][word]
        elif word in named["OPENSTR"]:
            opts["openstr"] = named["OPENSTR"][word]
        elif word in named["CLOSESTR"]:
            opts["closestr"] = named["CLOSESTR"][word]
        elif word in named["CLOSEON"]:
            opts["closeon"] = named["CLOSEON"][word]
        elif word in named["SIGNATURE"]:
            opts["signature"] = named["SIGNATURE"][word]
        else:
            notes.append({"code": "legacy_option_dropped", "port": port, "option": token})
    accepter = _accepter(port, state, remctl)
    if state == "rawlp" or device.startswith("sol."):
        connector = f"{'sol' if device.startswith('sol.') else 'rawlp'},{device}"
    else:
        serial = f"{speed}{parity}{data_bits}{stop_bits}"
        on_flags = [flag for flag, on in flags.items() if on]
        connector = ",".join(["serialdev", device, serial, *on_flags])
    name = device_name if device_name in named["DEVICE"] else f"port {port.split(',')[-1]}"
    definition: dict[str, Any] = {
        "accepter": accepter or f"udp,{port}",
        "connector": connector,
        "enable": "off" if state == "off" else "on",
        "timeout": timeout,
        "options": opts,
        "defaults": {},
    }
    return name, definition


def _on(value: str | None) -> bool:
    return value is not None and value.strip().lower() in ("true", "on", "yes", "1")
