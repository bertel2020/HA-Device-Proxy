"""Modbus registers as entities in Home Assistant, read by the app itself.

A connection lists them in register_entities, one line each:

    unit function address type swap scale unit_of_measurement device_class name

e.g. "1 3 40083 int16 none 0.1 W power AC power"; "-" for no unit or class, "string:8" for a
text of 8 registers. Data types and swap are those of Home Assistant's Modbus integration, as
in the panel's "decode values" (panel-src/src/modbus.js), so a value that looks right there is
right here.
"""

from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass

MAX_ENTITIES = 50
# type → registers it takes, struct format
NUMBERS = {
    "int16": (1, ">h"),
    "uint16": (1, ">H"),
    "int32": (2, ">i"),
    "uint32": (2, ">I"),
    "float32": (2, ">f"),
    "int64": (4, ">q"),
    "uint64": (4, ">Q"),
    "float64": (4, ">d"),
}
SWAPS = ("none", "word", "byte", "word_byte")
# the classes the panel offers (panel-src/src/modbus.js): Home Assistant refuses an unknown one
DEVICE_CLASSES = (
    "apparent_power",
    "battery",
    "current",
    "energy",
    "frequency",
    "gas",
    "humidity",
    "power",
    "power_factor",
    "pressure",
    "reactive_power",
    "temperature",
    "voltage",
    "volume",
    "water",
)
_UNIT = re.compile(r"[^\s#]{1,16}")


@dataclass(frozen=True)
class RegisterEntity:
    unit: int
    function: int  # 3 holding or 4 input registers
    address: int
    type: str
    count: int  # registers
    swap: str
    scale: float
    unit_of_measurement: str  # "" for none
    device_class: str  # "" for none
    name: str

    @property
    def key(self) -> str:
        """Stable while the register stays: the entity keeps its history over a rename."""
        return f"reg_{self.unit}_{self.function}_{self.address}"

    @property
    def is_text(self) -> bool:
        return self.type == "string"

    @property
    def state_class(self) -> str:
        return (
            "total_increasing" if self.device_class in ("energy", "gas", "water") else "measurement"
        )


def _int(text: str, what: str, low: int, high: int) -> int:
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"{what} must be a number") from None
    if not low <= value <= high:
        raise ValueError(f"{what} {low} to {high}")
    return value


def _parse_line(line: str) -> RegisterEntity:
    parts = line.split(None, 8)
    if len(parts) != 9:
        raise ValueError("unit function address type swap scale unit class name")
    unit = _int(parts[0], "unit", 1, 255)
    function = _int(parts[1], "function", 3, 4)
    address = _int(parts[2], "address", 0, 65535)
    kind, _, length = parts[3].partition(":")
    if kind == "string":
        count = _int(length or "0", "registers of a text", 1, 125)
    elif kind in NUMBERS and not length:
        count = NUMBERS[kind][0]
    else:
        raise ValueError(f"'{parts[3]}' is not a data type")
    if address + count > 65536:
        raise ValueError("address 0 to 65535")
    swap = parts[4]
    if swap not in SWAPS or (swap in ("word", "word_byte") and (kind == "string" or count == 1)):
        raise ValueError(f"'{swap}' does not fit {kind}")
    try:
        scale = float(parts[5].replace(",", "."))
    except ValueError:
        raise ValueError(f"'{parts[5]}' is not a factor") from None
    if not math.isfinite(scale) or scale == 0:
        raise ValueError(f"'{parts[5]}' is not a factor")
    uom = "" if parts[6] == "-" else parts[6]
    if uom and not _UNIT.fullmatch(uom):
        raise ValueError(f"'{uom}' is not a unit")
    device_class = "" if parts[7] == "-" else parts[7]
    if device_class and device_class not in DEVICE_CLASSES:
        raise ValueError(f"'{device_class}' is not a device class")
    name = " ".join(parts[8].split())
    if len(name) > 64:
        raise ValueError("a name of at most 64 characters")
    return RegisterEntity(
        unit, function, address, kind, count, swap, scale, uom, device_class, name
    )


def parse_entities(text: str) -> list[RegisterEntity]:
    """The lines of register_entities; raises ValueError naming the wrong line."""
    result: dict[str, RegisterEntity] = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            entity = _parse_line(line)
        except ValueError as err:
            raise ValueError(f"line {number}: {err}") from None
        if entity.key in result:
            raise ValueError(f"line {number}: this register is listed already")
        result[entity.key] = entity
    if len(result) > MAX_ENTITIES:
        raise ValueError(f"at most {MAX_ENTITIES} entities")
    return list(result.values())


def decode(registers: list[int], entity: RegisterEntity) -> float | int | str | None:
    """The value of its registers, None when it is no number (a float's NaN)."""
    words = list(reversed(registers)) if entity.swap in ("word", "word_byte") else registers
    data = bytearray(b"".join(w.to_bytes(2, "big") for w in words))
    if entity.swap in ("byte", "word_byte"):
        data[0::2], data[1::2] = data[1::2], data[0::2]
    if entity.is_text:
        return bytes(data).replace(b"\x00", b"").decode("latin-1").strip()
    value: float | int = struct.unpack(NUMBERS[entity.type][1], bytes(data))[0]
    if not math.isfinite(value):
        return None
    if entity.scale == 1 and isinstance(value, int):
        return value
    return round(value * entity.scale, 6)


def registers_of(answer: bytes | None, entity: RegisterEntity) -> list[int] | None:
    """The registers in the device's answer to reading this entity, None when it did not
    give them (no answer, an exception, too short)."""
    size = 2 * entity.count
    if not answer or len(answer) < 2 + size or answer[0] != entity.function or answer[1] != size:
        return None
    return [int.from_bytes(answer[i : i + 2], "big") for i in range(2, 2 + size, 2)]
