import time
from pathlib import Path

from device_proxy.config import blocks
from device_proxy.devices import scan
from device_proxy.model import AppConfig, Connection
from device_proxy.trace import Recorder, TraceTail

NOW = time.time()
STAMP = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(NOW)).encode()
TRACE = (
    STAMP
    + b" OPEN (ipv4,127.0.0.1,40000)\n"
    + STAMP
    + b" term 1b 1b 1b 1b 01 01 01 01 |........|\n"
    + STAMP
    + b" term 76 05                   |v.|\n"
    + STAMP
    + b" tcp  70 69 6e 67             |ping|\n"
    + STAMP
    + b" term 1b"  # not complete yet
)


def test_trace_is_read_along_and_recorded(tmp_path: Path) -> None:
    path = tmp_path / "c_0000000a.trace"
    path.write_bytes(TRACE)
    tail = TraceTail(path)
    chunks = tail.read(now=NOW)
    assert [(c.direction, c.data) for c in chunks] == [
        ("open", b""),
        ("rx", bytes.fromhex("1b1b1b1b010101017605")),
        ("tx", b"ping"),
    ]
    with path.open("ab") as f:
        f.write(b" 1b |.|\n")
    assert [c.data for c in tail.read(now=NOW)] == [b"\x1b\x1b"]

    record = tmp_path / "trace" / "ehz.log"
    recorder = Recorder(record, max_bytes=120, keep=2)
    for _ in range(4):
        recorder.write(chunks, "rx")
    # every write passes 120 bytes here, so each one is rotated away; 2 older ones stay
    assert sorted(p.name for p in record.parent.iterdir()) == ["ehz.log.1", "ehz.log.2"]
    assert " RX 1B 1B 1B 1B 01 01 01 01 76 05" in record.with_name("ehz.log.1").read_text()
    assert " TX " not in record.with_name("ehz.log.1").read_text()


def test_switching_the_recording_does_not_touch_ser2net() -> None:
    c = Connection("eHZ", "/dev/ttyUSB0", 3335, id="0000000a")
    on = Connection("eHZ", "/dev/ttyUSB0", 3335, id="0000000a", trace="both")
    assert blocks(AppConfig(connections=(c,))) == blocks(AppConfig(connections=(on,)))
    assert (
        "trace-both: /dev/shm/ser2net-trace/c_0000000a.trace"
        in blocks(AppConfig(connections=(c,)))["c_0000000a"]
    )


def test_devices_with_and_without_serial_number(tmp_path: Path) -> None:
    dev, sys = tmp_path / "dev", tmp_path / "sys"
    for tty, serial, port in (
        ("ttyUSB0", "A10K3QF2", "1.2"),
        ("ttyUSB1", "", "1.3"),
        ("ttyUSB2", "", "1.4"),
    ):
        (dev / tty).parent.mkdir(parents=True, exist_ok=True)
        (dev / tty).write_text("")
        usb = sys / "devices" / "usb1" / port
        node = usb / f"{port}:1.0" / tty
        node.mkdir(parents=True)
        (usb / "idVendor").write_text("0403" if serial else "1a86")
        (usb / "idProduct").write_text("6001" if serial else "7523")
        if serial:
            (usb / "serial").write_text(serial)
        driver = sys / "bus" / "drivers" / ("ftdi_sio" if serial else "ch341-uart")
        driver.mkdir(parents=True, exist_ok=True)
        (node / "driver").symlink_to(driver)
        tty_class = sys / "class" / "tty" / tty
        tty_class.mkdir(parents=True)
        (tty_class / "device").symlink_to(node)
        by = dev / "serial" / "by-path"
        by.mkdir(parents=True, exist_ok=True)
        (by / f"usb-0:{port}:1.0-port0").symlink_to(dev / tty)
    by_id = dev / "serial" / "by-id"
    by_id.mkdir()
    (by_id / "usb-FTDI_FT232R_A10K3QF2-if00-port0").symlink_to(dev / "ttyUSB0")
    found = {Path(d.tty).name: d for d in scan(dev, sys)}
    assert found["ttyUSB0"].ftdi and not found["ttyUSB0"].ambiguous
    assert found["ttyUSB0"].stable.endswith("by-id/usb-FTDI_FT232R_A10K3QF2-if00-port0")
    assert found["ttyUSB1"].ambiguous and found["ttyUSB2"].ambiguous
    assert found["ttyUSB1"].stable.endswith("by-path/usb-0:1.3:1.0-port0")


async def test_poll_reads_in_a_thread_and_updates_state_in_the_loop(tmp_path: Path) -> None:
    from device_proxy.trace import Chunk, TraceHub

    hub = TraceHub(tmp_path / "rec", tmp_path / "shm")
    hub.feed("a", Chunk(1.0, "rx", b"abc"))
    new = await hub.poll({"a": ("a", "both")}, 1 << 20, 1)
    assert [c.data for c in new["a"]] == [b"abc"]
    assert hub.flow["a"].rx_bytes == 3 and [c.seq for c in hub.live["a"]] == [1]
    assert (tmp_path / "rec" / "a.log").exists()
    await hub.poll({}, 1 << 20, 1)
    assert "a" not in hub.live
