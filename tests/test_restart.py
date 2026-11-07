"""Restarting a connection (also with a USB reset of its adapter) by hand, from Home
Assistant and automatically after the minutes without data."""

from pathlib import Path
from typing import Any

import pytest

from device_proxy import controller as controller_module
from device_proxy import devices, ha_mqtt
from device_proxy.admin import Client, PortStatus
from device_proxy.controller import AUTO_RESTART_MAX, Controller
from device_proxy.db import Database
from device_proxy.events import EventLog
from device_proxy.model import AppConfig, Connection, Settings, ValidationError
from device_proxy.store import Store
from device_proxy.trace import Flow, TraceHub


def _usb_tree(tmp_path: Path) -> tuple[Path, Path]:
    """sysfs and /dev of a ttyUSB0 on the USB adapter 1-1.3 (bus 1, device 5)."""
    sys_root, dev_root = tmp_path / "sys", tmp_path / "dev"
    adapter = sys_root / "devices" / "usb1" / "1-1" / "1-1.3"
    tty = adapter / "1-1.3:1.0" / "ttyUSB0"
    tty.mkdir(parents=True)
    for name, value in (("busnum", "1"), ("devnum", "5"), ("idVendor", "0403")):
        (adapter / name).write_text(f"{value}\n")
    (sys_root / "class" / "tty" / "ttyUSB0").mkdir(parents=True)
    (sys_root / "class" / "tty" / "ttyUSB0" / "device").symlink_to(tty)
    onboard = sys_root / "devices" / "platform" / "serial0" / "ttyAMA0"
    onboard.mkdir(parents=True)
    (sys_root / "class" / "tty" / "ttyAMA0").mkdir(parents=True)
    (sys_root / "class" / "tty" / "ttyAMA0" / "device").symlink_to(onboard)
    (dev_root / "bus" / "usb" / "001").mkdir(parents=True)
    (dev_root / "bus" / "usb" / "001" / "005").write_bytes(b"")
    (dev_root / "serial" / "by-id").mkdir(parents=True)
    (dev_root / "ttyUSB0").write_bytes(b"")
    (dev_root / "serial" / "by-id" / "usb-FTDI-if00").symlink_to(dev_root / "ttyUSB0")
    return sys_root, dev_root


def test_usb_node_and_reset(tmp_path: Path, monkeypatch: Any) -> None:
    sys_root, dev_root = _usb_tree(tmp_path)
    by_id = str(dev_root / "serial" / "by-id" / "usb-FTDI-if00")
    node, place = devices.usb_node(by_id, dev_root, sys_root)
    assert (node, place) == (dev_root / "bus" / "usb" / "001" / "005", "1-1.3")
    with pytest.raises(ValueError, match="not a USB adapter"):
        devices.usb_node("/dev/ttyAMA0", dev_root, sys_root)
    with pytest.raises(ValueError, match="not there"):
        devices.usb_node("/dev/ttyUSB9", dev_root, sys_root)

    calls: list[int] = []
    monkeypatch.setattr(devices.fcntl, "ioctl", lambda fd, request, arg: calls.append(request))
    assert devices.usb_reset(by_id, dev_root, sys_root) == "1-1.3"
    assert calls == [devices.USBDEVFS_RESET] and devices.USBDEVFS_RESET == 0x5514
    node.unlink()
    with pytest.raises(OSError, match="005"):  # no /dev/bus/usb in the container
        devices.usb_reset(by_id, dev_root, sys_root)


def _controller(tmp_path: Path, *connections: Connection) -> Controller:
    db = Database(tmp_path / "h.db")
    controller = Controller(
        Store(db, tmp_path / "c.json"),
        EventLog(db),
        tmp_path / "s.yaml",
        trace=TraceHub(tmp_path / "t", tmp_path / "shm"),
    )
    controller.config = AppConfig(connections=connections)
    return controller


def _kinds(controller: Controller) -> list[tuple[str, dict[str, Any]]]:
    return [(e.kind, e.params) for e in controller.events.history()]


class _Admin:
    def __init__(self) -> None:
        self.commands: list[str] = []

    async def command(self, text: str) -> str:
        self.commands.append(text)
        return ""


async def test_restart_closes_and_opens_the_port(tmp_path: Path, monkeypatch: Any) -> None:
    device = tmp_path / "ttyUSB0"
    device.write_bytes(b"")
    c = Connection("Stick", str(device), 3333, id="0000000a")
    controller = _controller(tmp_path, c)
    admin = _Admin()
    monkeypatch.setattr(controller, "admin", admin)

    result = await controller.restart_connection(c.id, "ui")
    assert result == {"usb": None, "usb_error": None}
    assert admin.commands == ["setportenable c_0000000a off", "setportenable c_0000000a on"]
    assert ("connection_restarted", {"by": "ui", "usb": ""}) in [
        (k, {x: p[x] for x in ("by", "usb")}) for k, p in _kinds(controller)
    ]
    assert c.id not in controller._paused

    resets: list[str] = []
    monkeypatch.setattr(controller_module, "usb_node", lambda path: (Path("/x"), "1-1.3"))

    def reset(path: str) -> str:
        resets.append(path)
        assert admin.commands[-1].endswith("off")  # while ser2net has let go of it
        return "1-1.3"

    monkeypatch.setattr(controller_module, "usb_reset", reset)
    monkeypatch.setattr(controller_module, "scan", lambda: [])
    admin.commands.clear()
    result = await controller.restart_connection(c.id, "mqtt", usb=True)
    assert result == {"usb": "1-1.3", "usb_error": None} and resets == [str(device)]
    assert admin.commands[-1] == "setportenable c_0000000a on"

    def broken(path: str) -> str:
        raise OSError(13, "/dev/bus/usb/001/005: Permission denied")

    monkeypatch.setattr(controller_module, "usb_reset", broken)
    admin.commands.clear()
    result = await controller.restart_connection(c.id, "ui", usb=True)
    assert "Permission denied" in str(result["usb_error"])
    assert admin.commands[-1] == "setportenable c_0000000a on"  # back on all the same
    assert "usb_reset_failed" in [k for k, _ in _kinds(controller)]


async def test_restart_refuses(tmp_path: Path, monkeypatch: Any) -> None:
    network = Connection("Bridge", "", 3334, id="0000000b", source="tcp", host="192.0.2.5")
    off = Connection("Off", "/dev/ttyUSB1", 3335, id="0000000c", enabled=False)
    onboard = Connection("UART", "/dev/ttyAMA0", 3336, id="0000000d")
    controller = _controller(tmp_path, network, off, onboard)
    admin = _Admin()
    monkeypatch.setattr(controller, "admin", admin)

    def not_usb(path: str) -> tuple[Path, str]:
        raise ValueError("not a USB adapter")

    monkeypatch.setattr(controller_module, "usb_node", not_usb)
    with pytest.raises(ValueError, match="device of this host"):
        await controller.restart_connection(network.id, "ui", usb=True)
    with pytest.raises(ValueError, match="not active"):
        await controller.restart_connection(off.id, "ui")
    with pytest.raises(ValueError, match="not a USB adapter"):
        await controller.restart_connection(onboard.id, "ui", usb=True)
    controller._paused.add(onboard.id)  # e.g. the baud rate detection
    with pytest.raises(ValueError, match="right now"):
        await controller.restart_connection(onboard.id, "ui")
    assert admin.commands == []  # nothing was touched
    controller.config = AppConfig(
        connections=controller.config.connections, settings=Settings(source="custom")
    )
    with pytest.raises(ValueError, match="own ser2net.yaml"):
        await controller.restart_connection(network.id, "ui")


async def test_automatic_restart_after_silence(tmp_path: Path) -> None:
    c = Connection(
        "Meter", "/dev/ttyUSB0", 3333, id="0000000a", silence_minutes=1, silence_restart="usb"
    )
    controller = _controller(tmp_path, c)
    controller.status[c.alias] = PortStatus(
        c.alias, True, c.device, clients=[Client("192.0.2.9:4000")]
    )
    flow = controller.trace.flow.setdefault(c.alias, Flow())
    restarts: list[tuple[float, bool]] = []
    now = 1000.0

    async def restart(connection_id: str, source: str, *, usb: bool = False) -> dict[str, object]:
        assert (connection_id, source) == (c.id, "auto")
        restarts.append((now, usb))
        return {}

    controller.restart_connection = restart  # type: ignore[method-assign]
    for now in (1000.0, 1030.0):  # open since 1000, quiet for less than a minute
        await controller._silence_tick(now)
    assert restarts == []
    now = 1061.0
    await controller._silence_tick(now)
    assert restarts == [(1061.0, True)]
    now = 1100.0
    await controller._silence_tick(now)  # a minute after the restart, not before
    assert len(restarts) == 1
    for _ in range(AUTO_RESTART_MAX - 1):
        now += 61
        await controller._silence_tick(now)
    assert len(restarts) == AUTO_RESTART_MAX
    for _ in range(3):  # it gives up, and says so once
        now += 61
        await controller._silence_tick(now)
    assert len(restarts) == AUTO_RESTART_MAX
    assert [k for k, _ in _kinds(controller)].count("auto_restart_gave_up") == 1

    flow.last_rx = now + 1  # data again: counted anew
    now += 2
    await controller._silence_tick(now)
    now += 61
    await controller._silence_tick(now)
    assert len(restarts) == AUTO_RESTART_MAX + 1

    controller.status[c.alias] = PortStatus(c.alias, True, c.device)  # closed: no clients
    now += 600
    await controller._silence_tick(now)
    assert len(restarts) == AUTO_RESTART_MAX + 1


def test_silence_restart_is_checked() -> None:
    def errors(**values: Any) -> dict[str, str]:
        try:
            Connection.from_dict({"name": "x", "device": "/dev/ttyUSB0", "port": 3333, **values})
        except ValidationError as err:
            return err.errors
        return {}

    assert errors(silence_minutes=5, silence_restart="usb") == {}
    assert "silence_restart" in errors(silence_restart="restart")  # no minutes
    assert "silence_restart" in errors(silence_minutes=5, silence_restart="reboot")
    bridge = {"source": "tcp", "host": "192.0.2.5", "host_port": 4000, "silence_minutes": 5}
    assert errors(**bridge, silence_restart="restart") == {}
    assert "silence_restart" in errors(**bridge, silence_restart="usb")


def test_mqtt_buttons(tmp_path: Path) -> None:
    stick = Connection("Stick", "/dev/ttyUSB0", 3333, id="0000000a")
    bridge = Connection("Bridge", "", 3334, id="0000000b", source="tcp", host="192.0.2.5")
    configs = ha_mqtt.HaBridge(_controller(tmp_path, stick, bridge)).configs()
    for c_id, usb in (("0000000a", True), ("0000000b", False)):
        restart = configs[f"homeassistant/button/device_proxy_{c_id}/restart/config"]
        assert restart["command_topic"] == f"device_proxy/{c_id}/restart/press"
        topic = f"homeassistant/button/device_proxy_{c_id}/usb_reset/config"
        assert (topic in configs) is usb


async def test_press_restarts(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    calls: list[tuple[str, str, bool]] = []

    async def restart(connection_id: str, source: str, *, usb: bool = False) -> dict[str, object]:
        calls.append((connection_id, source, usb))
        return {}

    controller.restart_connection = restart  # type: ignore[method-assign]
    await controller.press("0000000a", "restart")
    await controller.press("0000000a", "usb_reset")
    assert calls == [("0000000a", "mqtt", False), ("0000000a", "mqtt", True)]


async def test_a_failing_background_part_ends_the_app_instead_of_hanging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If ser2net's watcher fails, everything stops and start() raises (the app is started
    again), instead of waiting forever for MQTT with the proxies already gone."""
    import asyncio

    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    stop = asyncio.Event()

    async def fails(stop: asyncio.Event) -> None:
        raise RuntimeError("ser2net watcher broke")

    async def until_stopped(stop: asyncio.Event) -> None:
        await stop.wait()

    async def no_version() -> str:
        return ""

    monkeypatch.setattr(controller.ser2net, "run", fails)
    monkeypatch.setattr(controller.ser2net, "version", no_version)
    monkeypatch.setattr(controller.admin, "run", until_stopped)

    def mqtt() -> None:  # ends only with stop, like the real one
        controller._mqtt_task = asyncio.create_task(until_stopped(stop))

    monkeypatch.setattr(controller, "_start_mqtt", mqtt)
    with pytest.raises(RuntimeError, match="watcher broke"):
        await asyncio.wait_for(controller.start(stop), 5)
    assert stop.is_set()
