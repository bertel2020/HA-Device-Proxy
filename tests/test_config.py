from dataclasses import replace
from pathlib import Path

import pytest

from device_proxy.config import blocks, changed, render
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
    assert 'remaddr: "127.0.0.0/8,0;10.0.0.0/8,0;' in text
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
