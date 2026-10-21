"""What a smart meter sends: SML (binary) or D0 (text, IEC 62056-21), checked and decoded.

SML telegrams start with 1B 1B 1B 1B 01 01 01 01 and end with 1B 1B 1B 1B 1A <padding>
<crc>; the CRC is CRC-16/X-25 over everything before it, stored low byte first (as libsml
reads it). The readings are the list entries 77 07 <OBIS> status time unit scaler value.
D0 telegrams start with "/" and end with "!"; readings look like 1-0:1.8.0*255(012345.678*kWh).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

SML_START = bytes.fromhex("1b1b1b1b01010101")
SML_END = bytes.fromhex("1b1b1b1b1a")
UNITS = {27: "W", 30: "Wh", 33: "A", 35: "V", 44: "Hz", 29: "varh", 28: "VA"}
NAMES = {
    "1-0:1.8.0": "import total",
    "1-0:2.8.0": "export total",
    "1-0:16.7.0": "power",
    "1-0:1.8.1": "import tariff 1",
    "1-0:1.8.2": "import tariff 2",
}
D0_LINE = re.compile(rb"(\d+-\d+:\d+\.\d+\.\d+)(?:\*\d+)?\(([^)*]*)(?:\*([^)]*))?\)")


def crc_x25(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc ^ 0xFFFF


@dataclass
class Reading:
    obis: str
    value: float | str
    unit: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "obis": self.obis,
            "name": NAMES.get(self.obis, ""),
            "value": self.value,
            "unit": self.unit,
        }


@dataclass
class Analysis:
    protocol: str = "unknown"  # "sml", "d0" or "unknown"
    telegrams: int = 0
    valid: int = 0  # SML: right CRC; D0: complete
    readings: list[Reading] = field(default_factory=list)
    bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "telegrams": self.telegrams,
            "valid": self.valid,
            "readings": [r.to_dict() for r in self.readings],
            "bytes": self.bytes,
        }


def _tl(data: bytes, pos: int) -> tuple[int, int, int]:
    """SML type-length field at pos: (type, length of the value, position of the value)."""
    first = data[pos]
    kind, length, header = (first >> 4) & 0x7, first & 0x0F, 1
    while first & 0x80:  # more length bytes follow
        pos += 1
        first = data[pos]
        length = (length << 4) | (first & 0x0F)
        header += 1
    if kind == 7:  # list: length is the number of entries
        return kind, length, pos + 1
    return kind, length - header, pos + 1


def _skip(data: bytes, pos: int) -> int:
    kind, length, start = _tl(data, pos)
    if kind == 7:
        for _ in range(length):
            start = _skip(data, start)
        return start
    return start + max(length, 0)


def _number(data: bytes, pos: int) -> tuple[int | None, int]:
    kind, length, start = _tl(data, pos)
    if length <= 0:
        return None, start
    raw = data[start : start + length]
    return int.from_bytes(raw, "big", signed=kind == 5), start + length


def sml_readings(telegram: bytes) -> list[Reading]:
    readings = []
    pos = 0
    while (pos := telegram.find(b"\x77\x07", pos)) >= 0:
        try:
            obis = telegram[pos + 2 : pos + 8]
            if len(obis) < 6:
                break
            p = _skip(telegram, pos + 8)  # status
            p = _skip(telegram, p)  # value time
            unit, p = _number(telegram, p)
            scaler, p = _number(telegram, p)
            kind, length, start = _tl(telegram, p)
        except IndexError:
            break
        pos += 2
        code = f"{obis[0]}-{obis[1]}:{obis[2]}.{obis[3]}.{obis[4]}"
        if kind in (5, 6) and length > 0:
            raw = int.from_bytes(telegram[start : start + length], "big", signed=kind == 5)
            value = raw * 10 ** (scaler or 0)
            readings.append(Reading(code, round(value, 6), UNITS.get(unit or 0, "")))
    return readings


def analyze(data: bytes) -> Analysis:
    result = Analysis(bytes=len(data))
    pos = 0
    while (start := data.find(SML_START, pos)) >= 0:
        end = data.find(SML_END, start + len(SML_START))
        if end < 0 or end + 8 > len(data):
            break
        telegram = data[start : end + 8]
        result.protocol = "sml"
        result.telegrams += 1
        if crc_x25(telegram[:-2]) == telegram[-2] | telegram[-1] << 8:
            result.valid += 1
            result.readings = sml_readings(telegram) or result.readings
        pos = end + 8
    if result.protocol == "sml":
        return result
    pos = 0
    while (start := data.find(b"/", pos)) >= 0:
        end = data.find(b"!", start)
        if end < 0:
            break
        telegram = data[start : end + 1]
        result.protocol = "d0"
        result.telegrams += 1
        readings = []
        for m in D0_LINE.finditer(telegram):
            text = m.group(2).decode(errors="replace")
            try:
                value: float | str = float(text)
            except ValueError:
                value = text
            readings.append(Reading(m.group(1).decode(), value, (m.group(3) or b"").decode()))
        if readings:
            result.valid += 1
            result.readings = readings
        pos = end + 1
    return result


def score(data: bytes) -> float:
    """How much the bytes look like a meter at the right speed (0 = noise, 1 = clean)."""
    if not data:
        return 0.0
    analysis = analyze(data)
    if analysis.protocol == "sml":
        return 0.6 + 0.4 * (analysis.valid / analysis.telegrams) if analysis.telegrams else 0.5
    if analysis.protocol == "d0" and analysis.valid:
        return 0.9
    printable = sum(1 for b in data if 32 <= b < 127 or b in (10, 13))
    return 0.3 * printable / len(data)
