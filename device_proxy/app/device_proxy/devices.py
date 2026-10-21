"""Serial devices of the host: names, USB details, line error counters, FTDI latency.

/dev/serial/by-id names stay the same after a restart; adapters without a serial number
(many CH340) can share one by-id name or have none, then by-path (the USB port) tells them
apart. The line counters come from the driver (TIOCGICOUNT) and are read only while
ser2net has the device open anyway, so the app never opens a device on its own (opening
can raise DTR and reset some devices).
"""

from __future__ import annotations

import fcntl
import glob
import os
import struct
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SYS = Path("/sys")
DEV = Path("/dev")
TTY_PATTERNS = ("ttyUSB*", "ttyACM*", "ttyAMA*", "ttyS[0-9]*", "ttyXRUSB*", "ttyCH343USB*")
TIOCGICOUNT = 0x545D
ICOUNT = struct.Struct("20i")  # cts dsr rng dcd rx tx frame overrun parity brk buf_overrun ...


@dataclass
class Device:
    tty: str  # /dev/ttyUSB0
    by_id: list[str] = field(default_factory=list)
    by_path: list[str] = field(default_factory=list)
    vendor_id: str = ""
    product_id: str = ""
    manufacturer: str = ""
    product: str = ""
    serial: str = ""
    driver: str = ""
    ambiguous: bool = False  # another adapter of the same kind without a serial number

    @property
    def stable(self) -> str:
        """The name to configure: by-id when it is unique, else by-path, else the tty."""
        if self.by_id and not self.ambiguous:
            return self.by_id[0]
        if self.by_path:
            return self.by_path[0]
        return self.by_id[0] if self.by_id else self.tty

    @property
    def ftdi(self) -> bool:
        return self.driver == "ftdi_sio"

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "stable": self.stable, "ftdi": self.ftdi}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _usb_info(tty: str, sys_root: Path) -> dict[str, str]:
    device = sys_root / "class" / "tty" / tty / "device"
    info = {"driver": os.path.basename(os.path.realpath(device / "driver"))}
    if not device.exists():
        info["driver"] = ""
        return info
    node = Path(os.path.realpath(device))
    for _ in range(6):  # up to the USB device that has idVendor
        if (node / "idVendor").exists():
            info.update(
                vendor_id=_read(node / "idVendor"),
                product_id=_read(node / "idProduct"),
                manufacturer=_read(node / "manufacturer"),
                product=_read(node / "product"),
                serial=_read(node / "serial"),
            )
            break
        node = node.parent
    return info


def scan(dev_root: Path = DEV, sys_root: Path = SYS) -> list[Device]:
    found: dict[str, Device] = {}
    for pattern in TTY_PATTERNS:
        for path in sorted(glob.glob(str(dev_root / pattern))):
            tty = os.path.realpath(path)
            found.setdefault(tty, Device(tty))
    for kind in ("by-id", "by-path"):
        for link in sorted(glob.glob(str(dev_root / "serial" / kind / "*"))):
            tty = os.path.realpath(link)
            device = found.setdefault(tty, Device(tty))
            (device.by_id if kind == "by-id" else device.by_path).append(link)
    for device in found.values():
        info = _usb_info(os.path.basename(device.tty), sys_root)
        for key, value in info.items():
            setattr(device, key, value)
    kinds: dict[tuple[str, str], list[Device]] = {}
    for device in found.values():
        if device.vendor_id and not device.serial:
            kinds.setdefault((device.vendor_id, device.product_id), []).append(device)
    for same in kinds.values():
        if len(same) > 1:
            for device in same:
                device.ambiguous = True
    serial_ports = [d for d in found.values() if d.vendor_id or d.by_id or d.by_path]
    return sorted(serial_ports or found.values(), key=lambda d: d.tty)


def device_for(path: str, devices: list[Device]) -> Device | None:
    target = os.path.realpath(path)
    return next((d for d in devices if d.tty == target), None)


def line_counters(path: str) -> dict[str, int] | None:
    """The driver's counters of the device (frame, overrun, parity, break, buffer overrun)."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOCTTY)
    except OSError:
        return None
    try:
        raw = fcntl.ioctl(fd, TIOCGICOUNT, bytes(ICOUNT.size))
    except OSError:
        return None  # the driver does not count
    finally:
        os.close(fd)
    values = ICOUNT.unpack(raw)
    return {
        "frame": values[6],
        "overrun": values[7],
        "parity": values[8],
        "break": values[9],
        "buffer_overrun": values[10],
    }


def set_low_latency(path: str, sys_root: Path = SYS) -> str:
    """FTDI latency_timer to 1 ms. Returns "set", "already", "not_ftdi" or "read_only"."""
    tty = os.path.basename(os.path.realpath(path))
    timer = sys_root / "bus" / "usb-serial" / "devices" / tty / "latency_timer"
    if not timer.exists():
        return "not_ftdi"
    if _read(timer) == "1":
        return "already"
    try:
        timer.write_text("1", encoding="utf-8")
    except OSError:
        return "read_only"  # /sys is read-only in the container: needs a udev rule on the host
    return "set"
