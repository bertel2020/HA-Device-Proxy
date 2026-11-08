"""Modbus registers as entities: the lines, the decoding, the app's own reads, MQTT."""

import struct
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from device_proxy.ha_mqtt import HaBridge
from device_proxy.listen import ListenProxy
from device_proxy.modbus import ModbusProxy, mqtt_state, restart_key
from device_proxy.modbus_entities import DEVICE_CLASSES, decode, parse_entities, registers_of
from device_proxy.model import AppConfig, Connection, ValidationError

BASE = Connection("Inverter", "", 15020, id="0000000a", kind="modbus", host="192.0.2.5")
LINES = "1 3 40083 int16 none 0.1 W power AC power\n1 4 10 string:4 byte 1 - - Serial number"


def _proxy(text: str = LINES, cls: Any = ModbusProxy) -> Any:
    c = replace(BASE, register_entities=text)
    return cls(c, "lan", lambda *a, **k: None, lambda chunk: None)


def test_lines_are_read() -> None:
    power, serial = parse_entities(LINES + "\n\n")
    assert (power.unit, power.function, power.address, power.type) == (1, 3, 40083, "int16")
    assert (power.scale, power.unit_of_measurement, power.device_class) == (0.1, "W", "power")
    assert (power.name, power.key, power.count) == ("AC power", "reg_1_3_40083", 1)
    assert (serial.type, serial.count, serial.swap, serial.unit_of_measurement) == (
        "string",
        4,
        "byte",
        "",
    )
    assert parse_entities("1 3 0 uint32 word 0,5 kWh energy Total")[0].state_class == (
        "total_increasing"
    )


@pytest.mark.parametrize(
    "line",
    [
        "1 3 0 int16 none 1 W power",  # no name
        "0 3 0 int16 none 1 W power Name",  # unit
        "1 5 0 int16 none 1 W power Name",  # a coil
        "1 3 65536 int16 none 1 W power Name",
        "1 3 65535 int32 none 1 W power Name",  # runs past the last address
        "1 3 0 int8 none 1 W power Name",
        "1 3 0 string none 1 W power Name",  # a text needs its length
        "1 3 0 int16 word 1 W power Name",  # one register has no word order
        "1 3 0 int16 none 0 W power Name",
        "1 3 0 int16 none nan W power Name",
        "1 3 0 int16 none 1 W powerr Name",
        f"1 3 0 int16 none 1 W power {'x' * 65}",
    ],
)
def test_wrong_lines_are_refused(line: str) -> None:
    with pytest.raises(ValueError, match="line 2"):
        parse_entities(f"1 3 9 int16 none 1 W power Fine\n{line}")


def test_a_register_only_once_and_not_too_many() -> None:
    with pytest.raises(ValueError, match="listed already"):
        parse_entities("1 3 0 int16 none 1 - - A\n1 3 0 uint16 none 1 - - B")
    many = "\n".join(f"1 3 {a} int16 none 1 - - R{a}" for a in range(51))
    with pytest.raises(ValueError, match="at most 50"):
        parse_entities(many)


@pytest.mark.parametrize(
    ("line", "registers", "value"),
    [
        ("1 3 0 int16 none 1 - - x", [0xFFFE], -2),
        ("1 3 0 uint16 none 0.1 - - x", [1234], 123.4),
        ("1 3 0 int16 byte 1 - - x", [0x0100], 1),
        ("1 3 0 uint32 none 1 - - x", [0x0001, 0x0002], 0x00010002),
        ("1 3 0 uint32 word 1 - - x", [0x0002, 0x0001], 0x00010002),
        ("1 3 0 uint32 word_byte 1 - - x", [0x0200, 0x0100], 0x00010002),
        ("1 3 0 float32 none 1 - - x", [0x41C8, 0x0000], 25.0),
        ("1 3 0 float32 none 1 - - x", [0x7FC0, 0x0000], None),  # NaN
        ("1 3 0 int64 none 1 - - x", [0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF], -1),
        ("1 3 0 string:2 none 1 - - x", [0x4142, 0x4300], "ABC"),
        ("1 3 0 string:2 byte 1 - - x", [0x4241, 0x0043], "ABC"),
    ],
)
def test_decoding_as_in_the_panel(line: str, registers: list[int], value: object) -> None:
    assert decode(registers, parse_entities(line)[0]) == value


def test_registers_of_an_answer() -> None:
    entity = parse_entities("1 3 0 uint32 none 1 - - x")[0]
    assert registers_of(bytes([3, 4, 0, 1, 0, 2]), entity) == [1, 2]
    for bad in (None, b"", bytes([0x83, 2]), bytes([3, 2, 0, 1]), bytes([4, 4, 0, 1, 0, 2])):
        assert registers_of(bad, entity) is None


async def test_the_app_reads_its_registers_without_counting_them_for_the_clients() -> None:
    proxy = _proxy()
    proxy.reachable = True
    asked: list[tuple[int, bytes]] = []

    async def ask(unit: int, pdu: bytes, **kwargs: Any) -> bytes | None:
        asked.append((unit, pdu))
        function, _address, count = struct.unpack(">BHH", pdu)
        if function == 4:
            return bytes([0x84, 0x0B])  # the second one answers with an exception
        return bytes([function, count * 2]) + (1234).to_bytes(2, "big")

    proxy.ask = ask
    await proxy._entity_round()
    assert asked == [
        (1, struct.pack(">BHH", 3, 40083, 1)),
        (1, struct.pack(">BHH", 4, 10, 4)),
    ]
    assert proxy.entity_values == {"reg_1_3_40083": 123.4, "reg_1_4_10": None}
    assert proxy.stats.requests == 0
    state = proxy.state()
    assert state["entity_values"] == proxy.entity_values

    proxy.c = replace(proxy.c, register_entities="1 3 40083 int16 none 0.1 W power AC power")
    await proxy._entity_round()  # an entity taken away is gone from the values
    assert list(proxy.entity_values) == ["reg_1_3_40083"]


async def test_a_device_that_is_not_reachable_is_not_asked() -> None:
    proxy = _proxy()
    proxy.reachable = False
    proxy.entity_values = {"reg_1_3_40083": 5.0}

    async def ask(unit: int, pdu: bytes, **kwargs: Any) -> bytes | None:
        raise AssertionError("asked")

    proxy.ask = ask
    await proxy._entity_round()
    assert proxy.entity_values == {"reg_1_3_40083": None, "reg_1_4_10": None}


async def test_a_failing_read_does_not_stop_the_others() -> None:
    proxy = _proxy()
    proxy.reachable = True

    async def ask(unit: int, pdu: bytes, **kwargs: Any) -> bytes | None:
        if pdu[0] == 3:
            raise RuntimeError("a bug")
        return bytes([4, 8]) + b"ABCDEFGH"

    proxy.ask = ask
    await proxy._entity_round()
    assert proxy.entity_values == {"reg_1_3_40083": None, "reg_1_4_10": "BADCFEHG"}


async def test_listening_on_a_bus_takes_the_registers_heard() -> None:
    c = replace(
        BASE,
        link="rtu_listen",
        device="/dev/ttyUSB0",
        register_entities="1 3 100 uint16 none 1 - - Heard\n1 3 200 uint16 none 1 - - Not heard",
    )
    proxy = ListenProxy(c, "lan", lambda *a, **k: None, lambda chunk: None)
    proxy.reachable = True
    proxy.sniffer.read = lambda unit, function, address, count, age, now: (  # type: ignore[method-assign]
        [7] if address == 100 else None
    )
    await proxy._entity_round()
    assert proxy.entity_values == {"reg_1_3_100": 7, "reg_1_3_200": None}
    assert proxy.stats.requests == 0  # nothing went to the bus, nothing counted


def test_they_are_checked_and_need_no_restart() -> None:
    new = {"name": "M", "port": 15020, "kind": "modbus", "host": "192.0.2.5"}
    assert Connection.from_dict({**new, "register_entities": LINES}).register_entities
    with pytest.raises(ValidationError) as err:
        Connection.from_dict({**new, "register_entities": "1 3"})
    assert "line 1" in err.value.errors["register_entities"]
    with pytest.raises(ValidationError) as err:
        Connection.from_dict({**new, "entity_seconds": 2})
    assert "entity_seconds" in err.value.errors
    changed = replace(BASE, register_entities=LINES, entity_seconds=60)
    assert restart_key(BASE, "lan") == restart_key(changed, "lan")


def test_entities_in_home_assistant() -> None:
    c = replace(BASE, register_entities=LINES)

    class Controller:
        config = AppConfig(connections=(c,))
        active: tuple[Connection, ...] = ()
        ser2net_version = ""

    bridge = HaBridge(Controller())  # type: ignore[arg-type]
    configs = bridge.configs()
    power = configs["homeassistant/sensor/device_proxy_0000000a/reg_1_3_40083/config"]
    assert power["name"] == "AC power"
    assert power["unique_id"] == "device_proxy_0000000a_reg_1_3_40083"
    assert power["value_template"] == "{{ value_json.reg_1_3_40083 }}"
    assert (power["unit_of_measurement"], power["device_class"], power["state_class"]) == (
        "W",
        "power",
        "measurement",
    )
    serial = configs["homeassistant/sensor/device_proxy_0000000a/reg_1_4_10/config"]
    assert not {"unit_of_measurement", "device_class", "state_class"} & set(serial)


def test_the_values_go_into_the_state_of_the_connection() -> None:
    state = {"reachable": True, "requests": 1, "failed": 0, "time_avg_ms": 1.0, "answered": 1}
    assert "reg_1_3_0" not in mqtt_state(state)
    assert mqtt_state({**state, "entity_values": {"reg_1_3_0": 4.5}})["reg_1_3_0"] == 4.5


def test_the_panel_offers_the_same_device_classes() -> None:
    panel = Path(__file__).parents[1] / "panel-src" / "src" / "modbus.js"
    line = next(x for x in panel.read_text().splitlines() if "DEVICE_CLASSES =" in x)
    assert tuple(line.split("[", 1)[1].split("]")[0].replace('"', "").split(", ")) == DEVICE_CLASSES
