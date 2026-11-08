import ipaddress
import json
from pathlib import Path

import pytest

from device_proxy.clients import (
    LAST_SECONDS,
    LEARN_SECONDS,
    KnownClients,
    host_of,
    is_local,
    local_kind,
    parse_names,
    plain_host,
    with_name,
)
from device_proxy.config import block, remaddr, remaddr_without
from device_proxy.model import Connection, client_allowed


def test_names_and_hosts() -> None:
    assert parse_names("192.168.1.20 evcc\n\n# comment\nfe80::1  Laptop von Anna # x\n") == {
        "192.168.1.20": "evcc",
        "fe80::1": "Laptop von Anna",
    }
    with pytest.raises(ValueError, match="line 1"):
        parse_names("evcc 192.168.1.20")
    with pytest.raises(ValueError, match="line 2: a name"):
        parse_names("10.0.0.1 a\n10.0.0.2")
    assert host_of("192.168.1.20:50114") == "192.168.1.20"
    assert host_of("[fe80::1]:50114") == "fe80::1"
    assert is_local("127.0.0.1") and is_local("172.30.32.5") and is_local("::ffff:127.0.0.1")
    assert is_local("192.168.1.2", own="192.168.1.2") and not is_local("192.168.1.3", "192.168.1.2")


def test_new_clients_after_learning(tmp_path: Path) -> None:
    now = [1000.0]
    path = tmp_path / "known.json"
    known = KnownClients(path, clock=lambda: now[0])
    # no file yet: what connects in the first minutes is taken as known, quietly
    assert not known.seen("192.168.1.20:5000", "Zähler", {})
    now[0] += LEARN_SECONDS + 1
    assert not known.seen("192.168.1.20:6000", "Zähler", {})  # learnt
    assert not known.seen("127.0.0.1:6000", "Zähler", {})  # Home Assistant
    assert not known.seen("192.168.1.30:6000", "Zähler", {"192.168.1.30": "evcc"})  # named
    assert known.seen("192.168.1.40:6000", "Zähler", {})  # new
    assert not known.seen("192.168.1.40:6001", "Zähler", {})  # reported once
    assert list(known.new) == ["192.168.1.40"]

    again = KnownClients(path, clock=lambda: now[0])  # after a restart: no learning
    assert again.new.keys() == {"192.168.1.40"} and "192.168.1.20" in again.known
    assert again.seen("192.168.1.50:1", "Zähler", {})
    assert again.acknowledge("192.168.1.40") and not again.acknowledge("192.168.1.40")
    again.named({"192.168.1.50": "Laptop"})
    assert not again.new
    assert json.loads(path.read_text())["new"] == {}


def test_blocked_clients(tmp_path: Path) -> None:
    now = [1000.0]
    path = tmp_path / "known.json"
    known = KnownClients(path, clock=lambda: now[0])
    now[0] += LEARN_SECONDS + 1
    assert known.seen("192.168.1.40:6000", "Zähler", {})
    assert known.block("192.168.1.40") and not known.block("192.168.1.40")
    assert not known.new  # no longer waits for a decision, and no longer reported
    assert not known.seen("192.168.1.40:6001", "Zähler", {})
    assert known.block("192.168.1.41")

    again = KnownClients(path, clock=lambda: now[0])  # stays blocked over a restart
    assert again.blocked.keys() == {"192.168.1.40", "192.168.1.41"}
    assert again.unblock("192.168.1.40") and not again.unblock("192.168.1.40")
    assert not again.seen("192.168.1.40:6002", "Zähler", {})  # known now, not new again
    assert "192.168.1.40" in again.known and "192.168.1.40" not in again.blocked

    assert plain_host("::ffff:192.168.1.40") == "192.168.1.40"
    assert plain_host("fe80::1%eth0") == "fe80::1"
    assert plain_host("?") == "?"


def serial(**values: object) -> Connection:
    return Connection("Zähler", "/dev/ttyUSB0", 3335, **values)  # type: ignore[arg-type]


def test_blocked_host_is_cut_out_of_the_networks() -> None:
    net = "192.168.79.0/24"
    limit = remaddr_without(serial(remaddr=net), "all", ["192.168.79.144"])
    assert ipaddress.ip_network(net).num_addresses - 1 == sum(
        ipaddress.ip_network(n).num_addresses for n in limit.split()
    )
    assert not client_allowed(limit, "all", "192.168.79.144")
    assert client_allowed(limit, "all", "192.168.79.143")
    assert client_allowed(limit, "all", "192.168.79.145")
    assert not client_allowed(limit, "all", "192.168.80.1")  # still only that network

    # outside what the connection lets in: nothing changes, no reconnect
    assert remaddr_without(serial(remaddr=net), "all", ["10.0.0.1"]) == net
    assert remaddr_without(serial(), "lan:192.168.79.0/24", ["10.0.0.1"]) == ""
    assert remaddr_without(serial(), "local", ["192.168.79.144"]) == ""

    # the only address allowed: not an empty list, that would follow the global setting
    only = remaddr_without(serial(remaddr="192.168.79.144"), "all", ["192.168.79.144"])
    assert only == "127.0.0.1/32"


def test_blocked_host_when_anyone_may_connect() -> None:
    limit = remaddr_without(serial(), "all", ["192.168.79.144"])
    assert not client_allowed(limit, "all", "192.168.79.144")
    assert not client_allowed(limit, "all", "::ffff:192.168.79.144")
    for host in ("192.168.79.20", "8.8.8.8", "127.0.0.1", "2001:db8::1", "fd00::1", "::1"):
        assert client_allowed(limit, "all", host), host
    assert "/0" not in limit and not any(n.startswith("::f") for n in limit.split())

    c = serial(remaddr=limit)
    written = remaddr(c, "all")
    assert "192.168.79.144" not in written and written.endswith(",0")
    assert "remaddr" in block(c, "all")


def test_blocked_v6_host_leaves_v4_open() -> None:
    limit = remaddr_without(serial(), "all", ["2001:db8::1"])
    assert not client_allowed(limit, "all", "2001:db8::1")
    assert client_allowed(limit, "all", "2001:db8::2")
    assert client_allowed(limit, "all", "192.168.79.144")


def test_with_name() -> None:
    text = with_name("", "192.168.1.20", "  Symcon   Server ")
    assert text == "192.168.1.20 Symcon Server"
    text = with_name(text, "192.168.1.21", "Laptop")
    assert parse_names(text) == {"192.168.1.20": "Symcon Server", "192.168.1.21": "Laptop"}
    assert parse_names(with_name(text, "192.168.1.20", "")) == {"192.168.1.21": "Laptop"}
    with pytest.raises(ValueError, match="#"):
        with_name("", "192.168.1.20", "a # b")
    with pytest.raises(ValueError, match="at most"):
        with_name("", "192.168.1.20", "x" * 41)


def test_local_kind() -> None:
    assert local_kind("192.168.79.22", "192.168.79.22") == "home_assistant"
    assert local_kind("127.0.0.1") == "home_assistant"
    assert local_kind("172.30.32.6") == "app"
    assert local_kind("192.168.79.20", "192.168.79.22") is None


def test_last_seen(tmp_path: Path) -> None:
    now = [1000.0 + LEARN_SECONDS]
    path = tmp_path / "known.json"
    path.write_text(json.dumps({"known": {"192.168.1.20": 1.0}}))
    known = KnownClients(path, clock=lambda: now[0])
    assert not known.seen("192.168.1.20:1", "Zähler", {})
    assert known.last["192.168.1.20"] == {"time": now[0], "connection": "Zähler"}
    first = now[0]
    now[0] += LAST_SECONDS - 1
    known.touch("192.168.1.20:1", "Zähler")  # not written again so soon
    assert known.last["192.168.1.20"]["time"] == first
    now[0] += 1
    known.touch("192.168.1.20:1", "Wechselrichter")
    assert known.last["192.168.1.20"] == {"time": now[0], "connection": "Wechselrichter"}
    assert KnownClients(path).last == known.last

    known.touch("192.168.1.99:1", "Zähler")  # on no list
    assert "192.168.1.99" not in known.last
    # a name makes it known by itself: taking the name away later does not make it new
    assert not known.seen("192.168.1.30:1", "Zähler", {"192.168.1.30": "evcc"})
    assert "192.168.1.30" in known.known
    assert not known.seen("192.168.1.30:2", "Zähler", {})
