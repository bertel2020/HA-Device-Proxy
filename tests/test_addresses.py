from ser2net_app.addresses import addresses
from ser2net_app.model import Connection, Settings


def test_addresses_per_kind_of_client() -> None:
    c = Connection("eHZ", "/dev/ttyUSB0", 3335)
    lan = {a["target"]: a for a in addresses(c, Settings(listen="lan"), "192.168.1.10")}
    assert lan["ha"]["urls"]["tcp"] == "tcp://127.0.0.1:3335"
    assert lan["apps"]["urls"]["socket"] == "socket://172.30.32.1:3335"
    assert lan["lan"]["urls"]["tcp"] == "tcp://192.168.1.10:3335"
    assert all(a["reachable"] for a in lan.values())
    local = {a["target"]: a["reachable"] for a in addresses(c, Settings(listen="local"), None)}
    assert local == {"ha": True, "apps": False, "lan": False}
