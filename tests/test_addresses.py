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


def test_home_network_list(monkeypatch) -> None:
    from device_proxy import model
    from device_proxy.config import remaddr
    from device_proxy.model import Settings, client_allowed, lan_networks

    monkeypatch.setattr(model, "HOST_NETWORK", "192.168.79.0/24")
    own = Settings(listen="lan")  # the default: "own"
    assert [str(n) for n in lan_networks(own)] == ["192.168.79.0/24"]
    assert own.access == "lan:192.168.79.0/24"
    guest = Settings(listen="lan", lan_networks="own 192.168.80.0/24")
    c = Connection("x", "/dev/ttyX", 3333)
    assert remaddr(c, guest.access) == (
        "127.0.0.0/8,0;::1/128,0;172.30.32.0/23,0;192.168.79.0/24,0;192.168.80.0/24,0"
    )
    assert client_allowed("", guest.access, "192.168.80.7")
    assert client_allowed("", guest.access, "172.30.33.2")  # apps are always in
    assert not client_allowed("", guest.access, "192.168.81.7")
    assert not client_allowed("", guest.access, "8.8.8.8")
    # the own network unchecked and unknown host network: every private network
    monkeypatch.setattr(model, "HOST_NETWORK", None)
    assert client_allowed("", own.access, "10.1.2.3")


def test_home_assistant_under_the_host_name_counts_as_local() -> None:
    """Home Assistant connects to the discovery's host name, the host's LAN address, and so
    comes from there: "Home Assistant and apps" must let it in all the same."""
    from device_proxy.model import from_this_host, peer_allowed

    ha_only = "127.0.0.1, 172.30.32.0/23"
    host = ("192.168.79.22", 36476)
    assert from_this_host(host, ("192.168.79.22", 9100))
    assert peer_allowed(ha_only, "all", host, ("192.168.79.22", 9100))
    # another machine in the LAN, to the same address: still refused
    assert not from_this_host(("192.168.79.30", 5000), ("192.168.79.22", 9100))
    assert not peer_allowed(ha_only, "all", ("192.168.79.30", 5000), ("192.168.79.22", 9100))
    assert not peer_allowed(ha_only, "all", host, None)  # no own address known
    # the host's LAN address listed by hand keeps working
    assert peer_allowed("192.168.79.22", "all", host, ("192.168.79.22", 9100))
    assert peer_allowed("", "apps", ("::ffff:192.168.79.22", 1), ("::ffff:192.168.79.22", 9100))


def test_home_network_validation_and_migration() -> None:
    from device_proxy.model import AppConfig, Settings, ValidationError

    for bad in ("0.0.0.0/0", "::/0", "nonsense"):
        try:
            Settings.from_dict({"lan_networks": bad})
        except ValidationError as err:
            assert "lan_networks" in err.errors
        else:
            raise AssertionError(bad)
    # a configuration from before the list: "lan" stays every private network
    old = AppConfig.from_dict({"schema": 1, "settings": {"listen": "lan"}, "connections": []})
    assert old.settings.lan_networks == "10.0.0.0/8 172.16.0.0/12 192.168.0.0/16"
    new = AppConfig.from_dict({"schema": 1, "settings": {"lan_networks": "own"}})
    assert new.settings.lan_networks == "own"
