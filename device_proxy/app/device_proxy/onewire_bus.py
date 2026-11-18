"""What the app knows about the devices on a 1-Wire bus (onewire.py feeds it).

From the device lists: which devices were seen before (kept in /data, so a device that is
gone after a restart of the app still counts as missing), which are missing now (absent
from MISSING_AFTER lists in a row) and which are new (first seen when the bus had been known
for NEW_AFTER seconds already). iButtons (TRANSIENT_FAMILIES) come and go with the reader of
a DS1490F or a wall socket: they are never missing, the state says when one was there last.

From the answers the programs get (the proxy sees them pass, nothing is read for it): the
last value of every property read, errors per device, and for temperatures two typical
faults: 85 °C, the DS18x20's power-on value, which an owserver passes on when a conversion
did not finish (parasite power, a weak bus), and a value that stays exactly the same for
FROZEN_AFTER seconds while it is read FROZEN_READS times (a real sensor moves by 1/16 °C).

The exact chip of each device, read once (<id>/type, e.g. "DS18B20") and kept with the
device, so the list names it while it is missing too.

How each temperature sensor is powered, read once per run of the app when it is first listed
(<id>/power: 1 its own supply, 0 parasite power from the data line): parasite power is the
usual cause of the 85 °C.

From the owserver's own statistics (STATISTICS): CRC and bus errors since it started.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

KNOWN_FILE = Path("/data/onewire_devices.json")  # per connection: the devices seen
MISSING_AFTER = 2  # device lists in a row without a known device: it counts as missing
NEW_AFTER = 300.0  # seconds after the first list: a device seen later is new
SAVE_EVERY = 600.0  # seconds between two saves only for the times last seen
FROZEN_AFTER = 7200.0
FROZEN_READS = 20
POWER_ON = 85.0
BAD_EVENT_EVERY = 3600.0  # at most one 85 °C event per device in this time
TEMPERATURE_FAMILIES = {"10", "22", "28", "3B", "42"}
# a temperature that does not move is a fault on these too: the DS2438 (humidity sensors,
# battery monitors) has one, but no 85 °C power-on value
FROZEN_FAMILIES = TEMPERATURE_FAMILIES | {"26"}
# iButtons that are put on a reader and taken off again: DS1990A (also the DS2401 ID chip,
# which is seldom wired to a bus), DS1991, DS1994, DS1993, DS1992, DS1995, DS1996
TRANSIENT_FAMILIES = {"01", "02", "04", "06", "08", "0A", "0C"}
TEMPERATURE = re.compile(r"(temperature(9|10|11|12)?|fasttemp)")
VALUE_MAX = 40  # longer answers (memory pages) are no value to show
VALUES_MAX = 32  # properties kept per device; the one read longest ago goes first
DEVICE_ID = re.compile(r"[0-9A-F]{2}\.[0-9A-F]{12}")
# /statistics/errors/<name> of the owserver; BUS_* are summed up as bus errors
STATISTICS = (
    "CRC8_errors",
    "CRC8_tries",
    "CRC16_errors",
    "CRC16_tries",
    "BUS_readin_data_errors",
    "BUS_detect_errors",
    "BUS_level_errors",
    "BUS_next_errors",
    "BUS_bit_errors",
    "BUS_byte_errors",
    "BUS_echo_errors",
    "BUS_status_errors",
)

Event = tuple[str, str, dict[str, Any]]  # level, kind, values


@dataclass
class Value:
    text: str
    at: float
    changed_at: float
    reads: int = 1  # since the last change


@dataclass
class Device:
    id: str
    first: float
    last: float
    absent: int = 0  # lists in a row without it
    missing_since: float | None = None
    new: bool = False
    values: dict[str, Value] = field(default_factory=dict)
    errors: int = 0
    last_error: str = ""
    last_error_at: float | None = None
    bad: int = 0  # 85 °C answers
    bad_at: float | None = None
    power: str = ""  # "external", "parasite", "" not known
    chip: str = ""  # what the owserver says in <id>/type; "" not asked yet

    @property
    def family(self) -> str:
        return self.id[:2]

    @property
    def transient(self) -> bool:
        return self.family in TRANSIENT_FAMILIES


def device_of(path: str) -> tuple[str, str] | None:
    """(device ID, property) of a path like /uncached/28.A1B2C3D4E5F6/temperature."""
    parts = [p for p in path.split("/") if p]
    for i, part in enumerate(parts):
        if DEVICE_ID.fullmatch(part.upper()):
            return part.upper(), "/".join(parts[i + 1 :])
    return None


def parse_names(text: str) -> dict[str, str]:
    """ "28.A1B2C3D4E5F6 Wohnzimmer" per line → {ID: name}; raises ValueError."""
    names: dict[str, str] = {}
    for line in text.splitlines():
        device, _, name = line.strip().partition(" ")
        if not device:
            continue
        name = " ".join(name.split())
        if not DEVICE_ID.fullmatch(device.upper()):
            raise ValueError(f"'{device}' is not a 1-Wire ID like 28.A1B2C3D4E5F6")
        if not 1 <= len(name) <= 64:
            raise ValueError(f"'{device}': a name of 1 to 64 characters")
        names[device.upper()] = name
    return names


class Bus:
    def __init__(
        self, connection_id: str, path: Path | None = None, clock: Callable[[], float] = time.time
    ) -> None:
        self.connection_id = connection_id
        self.path = path or KNOWN_FILE
        self.clock = clock
        self.devices: dict[str, Device] = {}
        self.first_list: float | None = None  # this run
        self._saved = 0.0
        for device_id, seen in self._load().get(connection_id, {}).items():
            if DEVICE_ID.fullmatch(device_id) and isinstance(seen, dict):
                first, last = float(seen.get("first", 0)), float(seen.get("last", 0))
                chip = str(seen.get("type", ""))[:32]
                self.devices[device_id] = Device(device_id, first, last, chip=chip)
        self.power_asked: set[str] = set()  # this run
        self.type_asked: set[str] = set()
        self.statistics: dict[str, int] | None = None
        self.statistics_at: float | None = None
        self.errors_rising_at: float | None = None

    # the device lists

    def listed(self, ids: list[str]) -> list[Event]:
        now = self.clock()
        events: list[Event] = []
        known_before = bool(self.devices)
        if self.first_list is None:
            self.first_list = now
        changed = False
        for device_id in ids:
            device = self.devices.get(device_id)
            if device is None:
                new = known_before and now - self.first_list >= NEW_AFTER
                self.devices[device_id] = Device(device_id, now, now, new=new)
                changed = True
                if new:
                    events.append(("info", "onewire_device_new", {"device": device_id}))
                continue
            device.last, device.absent = now, 0
            if device.missing_since is not None:
                events.append(("info", "onewire_device_back", {"device": device_id}))
                device.missing_since = None
        listed = set(ids)
        for device in self.devices.values():
            if device.id in listed:
                continue
            device.absent += 1
            if device.transient:
                continue  # taken off the reader: not missing
            if device.absent == MISSING_AFTER and device.missing_since is None:
                device.missing_since = device.last
                events.append(("warning", "onewire_device_missing", {"device": device.id}))
        if changed or now - self._saved >= SAVE_EVERY:
            self.save()
        return events

    def needs_type(self) -> list[str]:
        """Devices on the bus whose chip is not known yet (asked once per run)."""
        return [
            d.id
            for d in self.devices.values()
            if not d.chip and d.absent == 0 and d.id not in self.type_asked
        ]

    def typed(self, device_id: str, ret: int, value: bytes) -> None:
        self.type_asked.add(device_id)
        device = self.devices.get(device_id)
        text = value.split(b"\0", 1)[0].decode("ascii", "replace").strip()
        if device is not None and ret >= 0 and text and text.isprintable():
            device.chip = text[:32]
            self.save()

    def needs_power(self) -> list[str]:
        """Temperature sensors on the bus whose supply was not asked for yet in this run."""
        return [
            d.id
            for d in self.devices.values()
            if d.family in TEMPERATURE_FAMILIES and d.absent == 0 and d.id not in self.power_asked
        ]

    def powered(self, device_id: str, ret: int, value: bytes) -> None:
        self.power_asked.add(device_id)
        device = self.devices.get(device_id)
        text = value.split(b"\0", 1)[0].strip()
        if device is not None and ret >= 0 and text in (b"0", b"1"):
            device.power = "external" if text == b"1" else "parasite"

    def missing(self) -> list[str]:
        return [d.id for d in self.devices.values() if d.missing_since is not None]

    def forget(self, device_id: str) -> bool:
        """A device taken off the bus on purpose: no longer missing."""
        if self.devices.pop(device_id.upper(), None) is None:
            return False
        self.save()
        return True

    # the answers the programs get

    def answered(self, path: str, ret: int, value: bytes, error: str = "") -> list[Event]:
        found = device_of(path)
        if found is None:
            return []
        device_id, prop = found
        device = self.devices.get(device_id)
        if device is None or not prop:
            return []
        now = self.clock()
        if ret < 0:
            device.errors += 1
            device.last_error, device.last_error_at = f"{error} {prop}", now
            return []
        text = value.split(b"\0", 1)[0]
        if not 0 < len(text) <= VALUE_MAX or not text.isascii():
            return []
        shown = text.decode().strip()
        if not shown.isprintable():
            return []
        old = device.values.get(prop)
        if old is None and len(device.values) >= VALUES_MAX:
            del device.values[min(device.values, key=lambda p: device.values[p].at)]
        if old is None or old.text != shown:
            device.values[prop] = Value(shown, now, now)
        else:
            old.at, old.reads = now, old.reads + 1
        if not (device.family in TEMPERATURE_FAMILIES and TEMPERATURE.fullmatch(prop)):
            return []
        try:
            number = float(shown)
        except ValueError:
            return []
        if number != POWER_ON:
            return []
        device.bad += 1
        quiet = device.bad_at is not None and now - device.bad_at < BAD_EVENT_EVERY
        device.bad_at = now
        if quiet:
            return []
        return [("warning", "onewire_value_85", {"device": device_id, "path": prop})]

    # the owserver's statistics

    def counted(self, values: dict[str, int]) -> None:
        old = self.statistics
        if old is not None and _errors(values) > _errors(old):
            self.errors_rising_at = self.clock()
        self.statistics, self.statistics_at = values, self.clock()

    # for the state

    def rows(self) -> list[dict[str, Any]]:
        now = self.clock()
        rows = []
        for d in sorted(self.devices.values(), key=lambda d: (d.missing_since is None, d.id)):
            values = {}
            frozen = False
            for prop, v in d.values.items():
                temperature = d.family in FROZEN_FAMILIES and TEMPERATURE.fullmatch(prop)
                still = temperature and now - v.changed_at >= FROZEN_AFTER
                frozen = frozen or bool(still and v.reads >= FROZEN_READS)
                values[prop] = {"value": v.text, "at": v.at, "changed_at": v.changed_at}
            rows.append(
                {
                    "id": d.id,
                    "family": d.family,
                    "first": d.first,
                    "last": d.last,
                    "present": d.missing_since is None and d.absent == 0,
                    "missing_since": d.missing_since,
                    "new": d.new,
                    "transient": d.transient,
                    "values": values,
                    "errors": d.errors,
                    "last_error": d.last_error,
                    "last_error_at": d.last_error_at,
                    "bad": d.bad,
                    "bad_at": d.bad_at,
                    "frozen": frozen,
                    "power": d.power,
                    "chip": d.chip,
                }
            )
        return rows

    def statistics_state(self) -> dict[str, Any] | None:
        s = self.statistics
        if s is None:
            return None
        tries = s.get("CRC8_tries", 0) + s.get("CRC16_tries", 0)
        crc = s.get("CRC8_errors", 0) + s.get("CRC16_errors", 0)
        return {
            "at": self.statistics_at,
            "crc_errors": crc,
            "crc_tries": tries,
            "crc_share": round(100 * crc / tries, 2) if tries else 0.0,
            "bus_errors": sum(v for k, v in s.items() if k.startswith("BUS_")),
            "rising_at": self.errors_rising_at,
            "values": dict(s),
        }

    # the file

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def save(self) -> None:
        data = self._load()
        data[self.connection_id] = {
            d.id: {"first": round(d.first), "last": round(d.last), "type": d.chip}
            for d in self.devices.values()
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data), encoding="utf-8")
            os.replace(tmp, self.path)
            self._saved = self.clock()
        except OSError as err:
            _LOGGER.debug("1-Wire devices not kept: %s", err)


def _errors(values: dict[str, int]) -> int:
    return sum(v for k, v in values.items() if k.endswith("_errors"))
