from device_proxy.addresses import addresses
from device_proxy.model import Connection, Settings


def test_addresses_per_kind_of_client() -> None:
    c = Connection("eHZ", "/dev/ttyUSB0", 3335)
    lan = {a["target"]: a for a in addresses(c, Settings(listen="lan"), "192.168.1.10")}
    assert lan["ha"]["urls"]["tcp"] == "tcp://127.0.0.1:3335"
    assert lan["apps"]["urls"]["socket"] == "socket://172.30.32.1:3335"
    assert lan["lan"]["urls"]["tcp"] == "tcp://192.168.1.10:3335"
    assert all(a["reachable"] for a in lan.values())
    local = {a["target"]: a["reachable"] for a in addresses(c, Settings(listen="local"), None)}
    assert local == {"ha": True, "apps": False, "lan": False}


def test_lan_address_follows_the_allowed_clients() -> None:
    def lan(remaddr: str) -> dict:
        c = Connection("eHZ", "/dev/ttyUSB0", 3335, remaddr=remaddr)
        return {a["target"]: a for a in addresses(c, Settings(listen="lan"), "192.168.1.10")}["lan"]

    assert lan("192.168.1.50")["reachable"]  # one LAN machine, not the host itself
    assert not lan("172.30.32.0/23")["reachable"]
    assert lan("172.30.32.0/23")["why"] == "clients"
