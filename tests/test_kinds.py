from dataclasses import replace
from pathlib import Path

import pytest

from device_proxy.controller import Controller
from device_proxy.db import Database
from device_proxy.events import EventLog
from device_proxy.kinds import PROXIED
from device_proxy.model import KINDS, AppConfig, Connection, ValidationError
from device_proxy.store import Store
from device_proxy.trace import TraceHub


def test_every_kind_but_serial_has_a_proxy() -> None:
    assert set(KINDS) == {"serial", *PROXIED}


def test_device_and_remote_follow_the_link() -> None:
    serial = Connection("eHZ", "/dev/ttyUSB0", 2001)
    tcp = Connection("WR", "", 5020, kind="modbus", host="192.168.1.5")
    rtu = Connection("Bus", "/dev/ttyUSB1", 5021, kind="modbus", link="rtu")
    assert (serial.uses_device, serial.remote) == (True, False)
    assert (tcp.uses_device, tcp.remote) == (False, True)
    assert (rtu.uses_device, rtu.remote) == (True, False)
    with pytest.raises(ValidationError) as err:
        Connection.from_dict({"name": "Bus", "port": 5021, "kind": "modbus", "link": "rtu"})
    assert "device" in err.value.errors
    Connection.from_dict({"name": "WR", "port": 5020, "kind": "modbus", "host": "wr.local"})


def test_two_proxies_for_one_network_device_collide() -> None:
    a = Connection("A", "", 5020, kind="modbus", host="WR.local")
    b = Connection("B", "", 5021, kind="modbus", host="wr.local")
    with pytest.raises(ValidationError) as err:
        AppConfig(connections=(a, b)).validate()
    assert "connections.1.host" in err.value.errors


async def test_proxies_start_from_the_table(tmp_path: Path) -> None:
    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    modbus = Connection(
        "WR", "", 15020, id="0000000b", kind="modbus", host="127.0.0.1", host_port=9
    )
    config = AppConfig(connections=(Connection("eHZ", "/dev/null", 3335, id="0000000a"), modbus))
    store.save(AppConfig(), config, "test")
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    controller.config = config
    assert config.proxied == (modbus,)
    try:
        assert await controller._reconcile_proxies() == ["WR"]
        assert set(controller.proxies) == {"0000000b"}
        snapshot = controller.snapshot()
        rows = {c["id"]: c for c in snapshot["connections"]}  # type: ignore[attr-defined]
        assert "modbus" in rows["0000000b"] and rows["0000000b"]["present"] is None
        assert "modbus" not in rows["0000000a"]
        topics = controller.mqtt.configs()
        assert any(t.endswith("device_proxy_0000000b/answer_time/config") for t in topics)
        assert any(t.endswith("device_proxy_0000000a/line_errors/config") for t in topics)
        # a change of the name only keeps the proxy running
        controller.config = replace(
            config, connections=(config.connections[0], replace(modbus, name="Wechselrichter"))
        )
        assert await controller._reconcile_proxies() == []
    finally:
        controller.config = AppConfig()
        await controller._reconcile_proxies()
