"""What the app knows about the devices on a 1-Wire bus."""

from pathlib import Path

import pytest

from device_proxy import onewire_bus
from device_proxy.onewire_bus import Bus, device_of, parse_names

SENSOR = "28.A1B2C3D4E5F6"
OTHER = "28.0F1E2D3C4B5A"
SWITCH = "3A.112233445566"


class Clock:
    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now


def bus(path: Path, clock: Clock) -> Bus:
    return Bus("0000000d", path, clock)


def kinds(events: list[onewire_bus.Event]) -> list[tuple[str, str]]:
    return [(kind, values.get("device", "")) for _level, kind, values in events]


def test_missing_back_and_new_devices_also_after_a_restart(tmp_path: Path) -> None:
    clock, path = Clock(), tmp_path / "devices.json"
    b = bus(path, clock)
    assert b.listed([SENSOR, SWITCH]) == []  # the first list: nothing is new yet
    clock.now += 30
    assert b.listed([SWITCH]) == []  # one list without it: not missing yet
    clock.now += 30
    assert kinds(b.listed([SWITCH])) == [("onewire_device_missing", SENSOR)]
    assert b.missing() == [SENSOR]
    assert b.rows()[0]["id"] == SENSOR and b.rows()[0]["missing_since"] == clock.now - 60
    # the app starts again while the sensor is still gone: it stays known
    clock.now += 600
    b = bus(path, clock)
    b.listed([SWITCH])
    assert kinds(b.listed([SWITCH])) == [("onewire_device_missing", SENSOR)]
    assert kinds(b.listed([SENSOR, SWITCH])) == [("onewire_device_back", SENSOR)]
    assert b.missing() == []
    # a device first seen once the bus has been known for a while is new
    clock.now += onewire_bus.NEW_AFTER
    assert kinds(b.listed([SENSOR, SWITCH, OTHER])) == [("onewire_device_new", OTHER)]
    assert next(r for r in b.rows() if r["id"] == OTHER)["new"]
    # taken off on purpose: forgotten, no longer missing
    for _ in range(onewire_bus.MISSING_AFTER):
        b.listed([SENSOR, SWITCH])
    assert b.missing() == [OTHER] and b.forget(OTHER.lower()) and b.missing() == []
    assert OTHER not in bus(path, clock).devices
    assert not b.forget(OTHER)


def test_another_connection_keeps_its_own_devices(tmp_path: Path) -> None:
    clock, path = Clock(), tmp_path / "devices.json"
    bus(path, clock).listed([SENSOR])
    Bus("0000000e", path, clock).listed([SWITCH])
    assert set(bus(path, clock).devices) == {SENSOR}


def test_values_85_degrees_and_errors_from_the_answers(tmp_path: Path) -> None:
    clock = Clock()
    b = bus(tmp_path / "d.json", clock)
    b.listed([SENSOR, SWITCH])
    assert b.answered(f"/uncached/{SENSOR}/temperature", 9, b"     21.5") == []
    assert b.answered(f"/bus.0/{SWITCH}/PIO.A", 1, b"0") == []
    assert b.answered("/settings/timeout/volatile", 2, b"15") == []  # no device
    assert b.answered(f"/{SENSOR}/memory", 100, b"\x00\x01" * 50) == []  # no value
    events = b.answered(f"/{SENSOR}/temperature12", 9, b"     85.0")
    assert events == [("warning", "onewire_value_85", {"device": SENSOR, "path": "temperature12"})]
    clock.now += 60
    assert b.answered(f"/{SENSOR}/temperature", 9, b"     85") == []  # once an hour
    assert b.answered(f"/{SWITCH}/temperature", 9, b"85") == []  # no thermometer
    b.answered(f"/{SENSOR}/humidity", -2, b"", "ENOENT")
    row = next(r for r in b.rows() if r["id"] == SENSOR)
    assert row["values"]["temperature"]["value"] == "85"
    assert (row["bad"], row["errors"], row["last_error"]) == (2, 1, "ENOENT humidity")
    switch = next(r for r in b.rows() if r["id"] == SWITCH)
    assert switch["values"]["PIO.A"]["value"] == "0" and switch["bad"] == 0
    # not on the list of the bus: nothing is kept
    assert b.answered("/10.000000000000/temperature", 9, b"20") == []
    assert "10.000000000000" not in b.devices


def test_a_temperature_that_does_not_move(tmp_path: Path) -> None:
    clock = Clock()
    b = bus(tmp_path / "d.json", clock)
    b.listed([SENSOR])
    for _ in range(onewire_bus.FROZEN_READS):
        b.answered(f"/{SENSOR}/temperature", 9, b"     21.5")
        clock.now += onewire_bus.FROZEN_AFTER / onewire_bus.FROZEN_READS
    assert b.rows()[0]["frozen"]
    b.answered(f"/{SENSOR}/temperature", 9, b"   21.5625")
    assert not b.rows()[0]["frozen"]


def test_the_owservers_error_counters(tmp_path: Path) -> None:
    clock = Clock()
    b = bus(tmp_path / "d.json", clock)
    assert b.statistics_state() is None
    b.counted({"CRC8_errors": 1, "CRC8_tries": 100, "CRC16_tries": 100, "BUS_level_errors": 2})
    state = b.statistics_state()
    assert state is not None
    assert (state["crc_errors"], state["crc_share"], state["bus_errors"]) == (1, 0.5, 2)
    assert state["rising_at"] is None
    clock.now += 60
    b.counted({"CRC8_errors": 3, "CRC8_tries": 200, "CRC16_tries": 100, "BUS_level_errors": 2})
    assert b.statistics_state()["rising_at"] == clock.now  # type: ignore[index]


def test_names_and_paths() -> None:
    assert parse_names(f"{SENSOR.lower()}  Living   room\n\n{SWITCH} Garage") == {
        SENSOR: "Living room",
        SWITCH: "Garage",
    }
    with pytest.raises(ValueError, match="not a 1-Wire ID"):
        parse_names("FE-E9-12-34 Kitchen")
    with pytest.raises(ValueError, match="1 to 64"):
        parse_names(SENSOR)
    assert device_of(f"/uncached/bus.0/{SENSOR.lower()}/temperature") == (SENSOR, "temperature")
    assert device_of("/statistics/errors/CRC8_errors") is None


def test_an_ibutton_comes_and_goes_without_being_missing(tmp_path: Path) -> None:
    clock = Clock()
    b = bus(tmp_path / "d.json", clock)
    button = "01.0000123456AB"
    b.listed([SENSOR, button])  # on the reader of the DS1490F
    for _ in range(onewire_bus.MISSING_AFTER + 2):
        clock.now += 30
        assert b.listed([SENSOR]) == []  # taken off: no event
    assert b.missing() == []
    row = next(r for r in b.rows() if r["id"] == button)
    assert row["transient"] and not row["present"] and row["missing_since"] is None
    assert row["last"] == clock.now - 30 * (onewire_bus.MISSING_AFTER + 2)
    assert b.listed([SENSOR, button]) == []  # put on again: known, nothing to say


def test_the_supply_of_each_temperature_sensor_is_asked_once(tmp_path: Path) -> None:
    b = bus(tmp_path / "d.json", Clock())
    b.listed([SENSOR, OTHER, SWITCH])
    assert b.needs_power() == [SENSOR, OTHER]  # thermometers only
    b.powered(SENSOR, 12, b"           0")
    b.powered(OTHER, -2, b"")  # no answer: not known, not asked again in this run
    assert b.needs_power() == []
    rows = {r["id"]: r["power"] for r in b.rows()}
    assert rows == {SENSOR: "parasite", OTHER: "", SWITCH: ""}
    b.powered(SENSOR, 12, b"           1")
    assert next(r for r in b.rows() if r["id"] == SENSOR)["power"] == "external"


def test_the_exact_chip_is_asked_once_and_kept(tmp_path: Path) -> None:
    clock, path = Clock(), tmp_path / "d.json"
    b = bus(path, clock)
    b.listed([SENSOR, SWITCH])
    assert b.needs_type() == [SENSOR, SWITCH]
    b.typed(SENSOR, 8, b"DS18B20\0")
    b.typed(SWITCH, -2, b"")  # no answer: not asked again in this run
    assert b.needs_type() == []
    assert {r["id"]: r["chip"] for r in b.rows()} == {SENSOR: "DS18B20", SWITCH: ""}
    # kept in the file: known while the sensor is missing, and not asked again
    b = bus(path, clock)
    assert b.devices[SENSOR].chip == "DS18B20"
    b.listed([SWITCH])
    assert b.needs_type() == [SWITCH]


def test_every_property_read_is_kept_up_to_a_limit(tmp_path: Path) -> None:
    clock = Clock()
    b = bus(tmp_path / "d.json", clock)
    b.listed([SWITCH])
    for i in range(onewire_bus.VALUES_MAX + 5):
        clock.now += 1
        b.answered(f"/{SWITCH}/page.{i}", 1, b"0")
    values = b.rows()[0]["values"]
    assert len(values) == onewire_bus.VALUES_MAX
    assert "page.0" not in values and f"page.{onewire_bus.VALUES_MAX + 4}" in values


def test_a_ds2438_temperature_that_does_not_move_but_no_85(tmp_path: Path) -> None:
    clock = Clock()
    b = bus(tmp_path / "d.json", clock)
    humidity = "26.0123456789AB"
    b.listed([humidity])
    for _ in range(onewire_bus.FROZEN_READS):
        assert b.answered(f"/{humidity}/temperature", 9, b"     85") == []  # no power-on value
        b.answered(f"/{humidity}/humidity", 9, b"     55.1")
        clock.now += onewire_bus.FROZEN_AFTER / onewire_bus.FROZEN_READS
    row = b.rows()[0]
    assert row["frozen"] and row["bad"] == 0
