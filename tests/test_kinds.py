import asyncio
from dataclasses import replace
from functools import partial
from pathlib import Path

import pytest

from device_proxy import controller as controller_module
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


async def test_an_enocean_gateway_in_the_controller(tmp_path: Path) -> None:
    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    mgw = Connection(
        "MGW", "", 15021, id="0000000c", kind="enocean", link="tcp", host="127.0.0.1", host_port=9
    )
    config = AppConfig(connections=(mgw,))
    store.save(AppConfig(), config, "test")
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    controller.config = config
    try:
        assert await controller._reconcile_proxies() == ["MGW"]
        proxy = controller.proxies["0000000c"]
        async with asyncio.timeout(5):
            while proxy.reachable is not False:
                await asyncio.sleep(0.01)
        (row,) = controller.snapshot()["connections"]  # type: ignore[misc]
        assert row["enocean"]["protocol"] == "esp2" and row["running"]
        assert row["addresses"][0]["urls"]["tcp"] == "tcp://127.0.0.1:15021"
        problems = controller.problems()
        assert "device_proxy_0000000c_unreachable" in problems
        assert "127.0.0.1:9" in problems["device_proxy_0000000c_unreachable"][1]
        topics = controller.mqtt.configs()
        assert any(t.endswith("device_proxy_0000000c/duty_cycle/config") for t in topics)
    finally:
        controller.config = AppConfig()
        await controller._reconcile_proxies()


async def test_a_proxy_that_ended_by_an_error_starts_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    modbus = Connection(
        "WR", "", 15022, id="0000000d", kind="modbus", host="127.0.0.1", host_port=9
    )
    config = AppConfig(connections=(modbus,))
    store.save(AppConfig(), config, "test")
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    controller.config = config
    monkeypatch.setattr(controller_module, "PROXY_RESTART", 0)
    try:
        await controller._reconcile_proxies()
        first = controller.proxies["0000000d"]

        async def broken() -> None:
            raise RuntimeError("bug")

        task = asyncio.create_task(broken())
        task.add_done_callback(partial(controller._proxy_ended, "0000000d"))
        old = controller._proxy_tasks["0000000d"]
        old.cancel()
        await asyncio.gather(old, return_exceptions=True)
        controller._proxy_tasks["0000000d"] = task
        await asyncio.gather(task, return_exceptions=True)
        await controller._proxy_tick()
        assert controller.proxies["0000000d"] is not first  # a new one
        assert not controller._proxy_tasks["0000000d"].done()
    finally:
        controller.config = AppConfig()
        await controller._reconcile_proxies()
