import pytest

from ser2net_app.config import Connection, render

PATH = "/dev/serial/by-path/pci-0000:00:1d.0-usb-0:1.3:1.0-port0"


def test_render_connection() -> None:
    text = render(
        [
            Connection(
                "eHZ Stromzähler",
                PATH,
                3335,
                max_clients=5,
                options=(("banner", "Hallo: Welt"),),
            ),
            Connection("Z-Wave", "/dev/ttyACM0", 3333, baud=115200, mode="rfc2217", enabled=False),
        ]
    )
    assert "admin:\n  accepter: tcp,127.0.0.1,18398" in text
    assert "connection: &ehz_stromzaehler\n  accepter: tcp,3335\n  enable: on" in text
    assert f"connector: serialdev,{PATH},9600n81,local" in text
    assert "max-connections: 5" in text
    assert 'banner: "Hallo: Welt"' in text
    assert "accepter: telnet(rfc2217),tcp,3333\n  enable: off" in text


def test_render_refuses_a_port_twice() -> None:
    with pytest.raises(ValueError, match="same port"):
        render([Connection("a", "/dev/ttyUSB0", 3333), Connection("b", "/dev/ttyUSB1", 3333)])
