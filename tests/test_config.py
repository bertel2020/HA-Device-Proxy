import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from device_proxy.config import blocks, changed, render, scalar
from device_proxy.model import AppConfig, Connection, Settings, ValidationError

PATH = "/dev/serial/by-path/pci-0000:00:1d.0-usb-0:1.3:1.0-port0"


def test_render() -> None:
    ehz = Connection("eHZ", PATH, 3335, id="0000000a", max_clients=5, banner="Hallo: Welt")
    zwave = Connection(
        "Z-Wave",
        "/dev/ttyACM0",
        3333,
        id="0000000b",
        baud=115200,
        mode="rfc2217",
        nodelay=True,
        enabled=False,
        chardelay=False,
        dtr="on",
    )
    text = render(AppConfig(Settings(listen="lan"), (ehz, zwave)))
    assert (
        "admin:\n  accepter: unix(delsock,umode=6,gmode=0,omode=0),/run/ser2net-admin.sock" in text
    )
    assert "connection: &c_0000000a\n  accepter: tcp,3335\n  enable: on" in text
    assert f"connector: serialdev,{PATH},9600n81,local\n" in text
    assert (
        'remaddr: "127.0.0.0/8,0;::1/128,0;172.30.32.0/23,0;fd0c:ac1e:2100::/48,0;10.0.0.0/8,0;'
        in text
    )
    assert 'banner: "Hallo: Welt"' in text
    assert "accepter: telnet(rfc2217),tcp(nodelay),3333\n  enable: off" in text
    assert "serialdev,/dev/ttyACM0,115200n81,local,dtr=on\n" in text
    assert "chardelay: false" in text
    local = render(AppConfig(Settings(listen="local"), (ehz,)))
    assert "accepter: tcp,127.0.0.1,3335" in local and "remaddr" not in local


def test_only_the_changed_connection_counts_as_changed() -> None:
    a = Connection("a", "/dev/ttyUSB0", 3333, id="0000000a")
    b = Connection("b", "/dev/ttyUSB1", 3334, id="0000000b")
    old = AppConfig(connections=(a, b))
    renamed = old.with_connection(replace(a, name="renamed"))
    assert changed(blocks(old), blocks(renamed)) == set()
    slower = old.with_connection(replace(b, baud=1200))
    assert changed(blocks(old), blocks(slower)) == {"c_0000000b"}


def test_validation_names_the_fields() -> None:
    with pytest.raises(ValidationError) as err:
        AppConfig.from_dict(
            {
                "connections": [
                    {"name": "a", "device": "/dev/ttyUSB0", "port": 3333},
                    {"name": "A", "device": "/dev/ttyUSB0", "port": 3333, "baud": 10},
                ]
            }
        )
    assert set(err.value.errors) == {
        "connections.1.baud",
    }
    with pytest.raises(ValidationError) as err:
        AppConfig.from_dict(
            {
                "connections": [
                    {"name": "a", "device": "/dev/ttyUSB0", "port": 3333},
                    {"name": "A", "device": "/dev/ttyUSB0", "port": 3333},
                ]
            }
        )
    assert set(err.value.errors) == {
        "connections.1.port",
        "connections.1.device",
        "connections.1.name",
    }


async def test_changes_at_the_same_time_do_not_overwrite_each_other(tmp_path: Path) -> None:
    import asyncio
    from dataclasses import replace

    from device_proxy.controller import Controller
    from device_proxy.db import Database
    from device_proxy.events import EventLog
    from device_proxy.model import AppConfig, Connection
    from device_proxy.store import Store
    from device_proxy.trace import TraceHub

    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    start = AppConfig(
        connections=(
            Connection("a", "/dev/null", 3335, id="0000000a"),
            Connection("b", "/dev/null", 3336, id="0000000b"),
        )
    )
    store.save(AppConfig(), start, "test")
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    controller.config = start

    def switch_off(connection_id: str):  # type: ignore[no-untyped-def]
        def build(config: AppConfig) -> AppConfig:
            current = config.connection(connection_id)
            assert current is not None
            return config.with_connection(replace(current, enabled=False))

        return build

    await asyncio.gather(
        controller.apply(switch_off("0000000a"), "test"),
        controller.apply(switch_off("0000000b"), "test"),
    )
    assert [c.enabled for c in controller.config.connections] == [False, False]


def test_a_damaged_config_file_falls_back_to_the_latest_version(tmp_path: Path) -> None:
    from device_proxy.db import Database
    from device_proxy.store import Store

    store = Store(Database(tmp_path / "h.db"), tmp_path / "c.json")
    config = AppConfig(connections=(Connection("a", "/dev/null", 3335, id="0000000a"),))
    store.save(AppConfig(), config, "test")
    (tmp_path / "c.json").write_text('{"connections": [', encoding="utf-8")
    assert store.load() == config
    (tmp_path / "c.json").unlink()
    assert store.load() == config
    assert Store(None, tmp_path / "none.json").load() == AppConfig()


def test_an_invalid_config_without_a_valid_version_keeps_what_is_valid(tmp_path: Path) -> None:
    """Stricter checks of a new version: not everything lost (and with it the HA entities)."""
    from device_proxy.store import Store

    good = Connection("a", "/dev/null", 3335, id="0000000a")
    data = AppConfig(Settings(mqtt_interval=30), (good,)).to_dict()
    data["settings"]["mqtt_port"] = 0  # invalid: back to the default
    data["connections"].append({**good.to_dict(), "id": "0000000b", "name": "b", "port": 1})
    data["connections"].append({**good.to_dict(), "id": "0000000c", "name": "c", "port": 3336})
    path = tmp_path / "c.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    store = Store(None, path)
    config = store.load()
    assert [c.name for c in config.connections] == ["a"]  # b: bad port, c: same device as a
    assert config.settings.mqtt_interval == 30
    assert config.settings.mqtt_port == Settings().mqtt_port
    assert list(tmp_path.glob("c.invalid-*"))  # the original is kept aside
    assert store.load() == config  # and written back: the next start finds it


def test_listen_apps_limits_clients_to_home_assistant_and_the_apps() -> None:
    from device_proxy.model import client_allowed

    assert client_allowed("", "apps", "127.0.0.1")
    assert client_allowed("", "apps", "172.30.33.2")
    assert client_allowed("", "apps", "::ffff:172.30.32.1")
    assert not client_allowed("", "apps", "192.168.1.20")
    assert client_allowed("", "lan", "192.168.1.20")


def test_saving_without_a_change_makes_no_new_version(tmp_path: Path) -> None:
    from device_proxy.db import Database
    from device_proxy.store import Store

    store = Store(Database(tmp_path / "h.db"), tmp_path / "c.json")
    config = AppConfig(connections=(Connection("a", "/dev/null", 3335, id="0000000a"),))
    store.save(AppConfig(), config, "test")
    store.save(config, config, "ui")
    assert len(store.versions()) == 1


def test_history_names_the_new_settings_values_but_not_secrets() -> None:
    from dataclasses import replace

    from device_proxy.model import AppConfig, Settings
    from device_proxy.store import changes

    old = AppConfig()
    new = AppConfig(
        settings=replace(Settings(), listen="apps", mqtt_user="anna", mqtt_password="geheim")
    )
    [item] = changes(old, new)
    assert item["values"] == {"listen": "apps"}
    assert item["fields"] == ["listen", "mqtt_user", "mqtt_password"]


def test_a_serial_bridge_in_the_network_is_a_tcp_connector() -> None:
    bridge = Connection(
        "Lesekopf", "", 3340, id="0000000c", source="tcp", host="192.168.1.50", host_port=8888
    )
    bridge.validate()
    assert not bridge.uses_device and bridge.remote
    assert (
        "  connector: tcp,192.168.1.50,8888\n"
        in blocks(AppConfig(connections=(bridge,)))[bridge.alias]
    )
    with pytest.raises(ValidationError) as err:
        replace(bridge, host="").validate()
    assert "host" in err.value.errors


async def test_maintenance_limits_a_serial_connection_to_one_host(tmp_path: Path) -> None:
    from device_proxy.controller import Controller
    from device_proxy.db import Database
    from device_proxy.events import EventLog
    from device_proxy.store import Store
    from device_proxy.trace import TraceHub

    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    config = AppConfig(connections=(Connection("a", "/dev/null", 3335, id="0000000a"),))
    store.save(AppConfig(), config, "test")
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    controller.config = config
    await controller.set_exclusive("0000000a", "192.168.1.35", 30)
    assert "remaddr: 192.168.1.35/32,0" in (tmp_path / "s.yaml").read_text()
    assert controller.snapshot()["connections"][0]["exclusive"]["host"] == "192.168.1.35"  # type: ignore[index]
    with pytest.raises(ValueError):
        await controller.set_exclusive("0000000a", "laptop", 30)
    controller.exclusive["0000000a"] = ("192.168.1.35", 0)  # its time is up
    await controller._proxy_tick()
    assert "192.168.1.35" not in (tmp_path / "s.yaml").read_text()


def test_a_new_modbus_connection_lets_only_home_assistant_and_the_apps_write(
    tmp_path: Path,
) -> None:
    from device_proxy.model import MODBUS_WRITE_CLIENTS
    from device_proxy.store import Store

    new = {"name": "Inverter", "port": 1502, "kind": "modbus", "host": "192.168.1.20"}
    modbus = Connection.from_dict(new)
    assert (modbus.write_access, modbus.write_clients) == ("listed", MODBUS_WRITE_CLIENTS)
    named = Connection.from_dict({**new, "write_access": "all"})
    assert (named.write_access, named.write_clients) == ("all", "")
    assert Connection.from_dict({**new, "write_clients": "10.0.0.5"}).write_clients == "10.0.0.5"
    # saved (or backed up) before the field existed: every client could write, and still may
    old = {**new, "id": "0000000a"}
    assert AppConfig.from_dict({"connections": [old]}).connections[0].write_access == "all"
    (tmp_path / "c.json").write_text(json.dumps({"connections": [old]}), encoding="utf-8")
    assert Store(None, tmp_path / "c.json").load().connections[0].write_access == "all"
    # the panel's form starts a new Modbus connection with the same clients
    edit = Path(__file__).parents[1] / "panel-src" / "src" / "pages" / "edit.js"
    assert f'write_access: "listed", write_clients: "{MODBUS_WRITE_CLIENTS}"' in edit.read_text()


@pytest.mark.parametrize("template", ["zwave", "zigbee"])
def test_a_new_stick_lets_only_home_assistant_and_the_apps_connect(template: str) -> None:
    from device_proxy.model import ZWAVE_CLIENTS

    new = {"name": "Stick", "port": 3333, "device": "/dev/zero", "template": template}
    assert Connection.from_dict(new).remaddr == ZWAVE_CLIENTS
    assert Connection.from_dict({**new, "remaddr": ""}).remaddr == ""  # chosen: the setting
    assert Connection.from_dict({**new, "template": "generic"}).remaddr == ""
    edit = Path(__file__).parents[1] / "panel-src" / "src" / "pages" / "edit.js"
    assert f'const ZWAVE_CLIENTS = "{ZWAVE_CLIENTS}";' in edit.read_text()
    assert f"{template}: {{ baud: 115200" in edit.read_text()  # the panel has the template too


def test_effects_name_what_saving_sets_up_again_and_stops(tmp_path: Path) -> None:
    from types import SimpleNamespace

    from device_proxy.controller import Controller
    from device_proxy.db import Database
    from device_proxy.events import EventLog
    from device_proxy.modbus import restart_key
    from device_proxy.store import Store
    from device_proxy.trace import TraceHub

    db = Database(tmp_path / "h.db")
    meter = Connection("Meter", "/dev/null", 3335, id="0000000a")
    stick = Connection("Stick", "/dev/zero", 3336, id="0000000b")
    inverter = Connection.from_dict(
        {"name": "Inverter", "port": 1502, "kind": "modbus", "host": "10.0.0.9", "id": "0000000c"}
    )
    config = AppConfig(connections=(meter, stick, inverter))
    controller = Controller(
        Store(db, tmp_path / "c.json"),
        EventLog(db),
        tmp_path / "s.yaml",
        trace=TraceHub(tmp_path / "t", tmp_path / "shm"),
    )
    controller.config = config
    controller.write_config()
    access = config.settings.access
    controller.proxies["0000000c"] = SimpleNamespace(  # type: ignore[assignment]
        c=inverter, key=restart_key(inverter, access), clients={"10.0.0.5": 1, "10.0.0.6": 2}
    )
    assert controller.effects(config) == []
    faster = config.with_connection(replace(meter, baud=19200))
    assert controller.effects(faster) == [{"name": "Meter", "effect": "restart", "clients": 0}]
    other_port = config.with_connection(replace(inverter, port=1503))
    assert controller.effects(other_port) == [
        {"name": "Inverter", "effect": "restart", "clients": 2}
    ]
    renamed = config.with_connection(replace(inverter, name="PV"))  # no restart for a name
    assert controller.effects(renamed) == []
    gone = config.without_connection("0000000b").without_connection("0000000c")
    assert controller.effects(gone) == [
        {"name": "Stick", "effect": "stop", "clients": 0},
        {"name": "Inverter", "effect": "stop", "clients": 2},
    ]


async def test_a_change_keeps_the_version_before_and_what_worked(tmp_path: Path) -> None:
    from types import SimpleNamespace

    from device_proxy.controller import Controller
    from device_proxy.db import Database
    from device_proxy.events import EventLog
    from device_proxy.store import Store
    from device_proxy.trace import TraceHub

    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    meter = Connection("Meter", "/dev/null", 3335, id="0000000a")
    pv = Connection.from_dict(
        {"name": "PV", "port": 1502, "kind": "modbus", "host": "10.0.0.9", "id": "0000000b"}
    )
    start = AppConfig(connections=(meter, replace(pv, enabled=False)))  # starts no proxy
    store.save(AppConfig(), start, "test")
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    controller.config = start
    controller.proxies["0000000b"] = SimpleNamespace(  # type: ignore[assignment]
        c=pv, listening=True, reachable=True, serves=""
    )
    assert controller.working(pv) and not controller.working(meter)  # ser2net is not running
    controller.proxies["0000000b"].reachable = False  # type: ignore[attr-defined]
    assert not controller.working(pv)
    controller.proxies["0000000b"].reachable = None  # type: ignore[attr-defined]
    before = store.latest_id()
    controller.working = lambda c: c.id == "0000000b"  # type: ignore[method-assign]
    controller.proxies.clear()
    await controller.apply(start.with_connection(replace(meter, baud=19200)), "test")
    assert controller.last_change is not None
    assert controller.last_change["version"] == before and controller.last_change["working"] == [
        "0000000b"
    ]
    restored = store.version(int(str(controller.last_change["version"])))
    assert restored is not None and restored.connection("0000000a") == meter


def test_scalars_read_back_as_written() -> None:
    """A banner or option that begins with a YAML indicator is quoted, so ser2net.yaml stays
    readable."""
    for value in ("- Welcome", "-", "@home", ",x", "a: b", "a #b", "x", "/dev/ttyUSB0", "-x"):
        assert yaml.safe_load(f"k: {scalar(value)}")["k"] == value, value
    assert scalar("/dev/ttyUSB0") == "/dev/ttyUSB0"  # plain where it is safe
