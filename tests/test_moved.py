from pathlib import Path

from device_proxy.controller import Controller
from device_proxy.db import Database
from device_proxy.devices import Device, moved
from device_proxy.events import EventLog
from device_proxy.model import AppConfig, Connection
from device_proxy.store import Store
from device_proxy.trace import TraceHub


def _ch340(tty: str, serial: str = "") -> Device:
    return Device(tty, vendor_id="1a86", product_id="7523", serial=serial, product="USB Serial")


def test_moved_matches_the_kind_and_a_serial_number() -> None:
    print_ = {"vendor_id": "1a86", "product_id": "7523", "serial": "", "product": "USB Serial"}
    devices = [_ch340("/dev/ttyUSB1"), _ch340("/dev/ttyUSB2"), Device("/dev/ttyACM0")]
    assert [d.tty for d in moved(print_, devices, {"/dev/ttyUSB2"})] == ["/dev/ttyUSB1"]
    devices[0].by_path = ["/dev/serial/by-path/usb-0:1.4"]  # named by another connection
    assert moved(print_, devices, {"/dev/serial/by-path/usb-0:1.4", "/dev/ttyUSB2"}) == []
    with_serial = {**print_, "serial": "B"}
    devices = [_ch340("/dev/ttyUSB1", "A"), _ch340("/dev/ttyUSB2", "B")]
    assert [d.tty for d in moved(with_serial, devices, set())] == ["/dev/ttyUSB2"]


def test_a_missing_device_is_found_on_another_port(tmp_path: Path) -> None:
    plugged = tmp_path / "ttyUSB0"
    plugged.touch()
    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    config = AppConfig(connections=(Connection("Zähler", str(plugged), 3335, id="0000000a"),))
    store.save(AppConfig(), config, "test")
    controller = Controller(
        store,
        EventLog(db),
        tmp_path / "s.yaml",
        trace=TraceHub(tmp_path / "t", tmp_path / "shm"),
        prints_file=tmp_path / "prints.json",
    )
    controller.config = config
    controller.devices = [_ch340(str(plugged))]
    controller.check_devices()
    assert controller.prints["0000000a"]["vendor_id"] == "1a86"
    assert controller.moved_to(config.connections[0]) == []  # it is there

    plugged.unlink()  # unplugged, and plugged in elsewhere
    controller.devices = [_ch340(str(tmp_path / "ttyUSB3"))]
    controller.check_devices()
    found = controller.moved_to(config.connections[0])
    assert [d["tty"] for d in found] == [str(tmp_path / "ttyUSB3")]
    again = Controller(
        store,
        EventLog(db),
        tmp_path / "s.yaml",
        trace=TraceHub(tmp_path / "t", tmp_path / "shm"),
        prints_file=tmp_path / "prints.json",
    )
    assert again.prints == controller.prints  # kept over a restart
