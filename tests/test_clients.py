import json
from pathlib import Path

import pytest

from device_proxy.clients import LEARN_SECONDS, KnownClients, host_of, is_local, parse_names


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
