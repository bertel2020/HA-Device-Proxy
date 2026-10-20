from dataclasses import replace

import pytest

from ser2net_app.config import blocks, changed, render
from ser2net_app.model import AppConfig, Connection, Settings, ValidationError

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
