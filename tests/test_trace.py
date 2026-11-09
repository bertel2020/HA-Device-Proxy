import os
import re
import time
from pathlib import Path

from device_proxy.config import blocks
from device_proxy.devices import scan
from device_proxy.model import AppConfig, Connection
from device_proxy.trace import Chunk, Recorder, TraceHub, TraceTail, recording_stem

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

    folder = tmp_path / "trace"
    mtimes = iter(range(1000, 1100, 10))
    times = iter(range(1_794_000_000, 1_794_000_100, 10))
    recorder = Recorder(folder, "ehz", max_bytes=40, keep=2, clock=lambda: float(next(times)))
    for _ in range(4):
        assert recorder.write(chunks, "rx")
        os.utime(recorder.files()[-1], (0, next(mtimes)))
    # every write passes 40 bytes here, so each begins a file; the newest and 2 older ones stay
    names = [p.name for p in recorder.files()]
    assert len(names) == 3 and all(re.fullmatch(r"ehz-\d{8}-\d{6}\.log", n) for n in names)
    assert names == sorted(names)
    newest = (folder / names[-1]).read_text()
    assert " RX 1B 1B 1B 1B 01 01 01 01 76 05" in newest and " TX " not in newest


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
    hub = TraceHub(tmp_path / "rec", tmp_path / "shm")
    hub.feed("a", Chunk(1.0, "rx", b"abc"))
    new = await hub.poll({"a": ("a", "both")}, 1 << 20, 1)
    assert [c.data for c in new["a"]] == [b"abc"]
    assert hub.flow["a"].rx_bytes == 3 and [c.seq for c in hub.live["a"]] == [1]
    assert len(list((tmp_path / "rec").glob("a-*.log"))) == 1
    await hub.poll({}, 1 << 20, 1)
    assert "a" not in hub.live


async def test_a_recording_that_cannot_be_written_does_not_stop_the_live_view(
    tmp_path: Path,
) -> None:
    (tmp_path / "rec").write_text("a file where the folder should be")
    hub = TraceHub(tmp_path / "rec", tmp_path / "shm")
    hub.feed("a", Chunk(1.0, "rx", b"abc"))
    hub.feed("b", Chunk(1.0, "rx", b"xyz"))
    new = await hub.poll({"a": ("a", "both"), "b": ("b", "off")}, 1 << 20, 1)
    assert [c.data for c in new["a"]] == [b"abc"] and [c.data for c in new["b"]] == [b"xyz"]
    assert hub.flow["b"].rx_bytes == 3


def _recorder(folder: Path, name: str = "ehz", **kwargs: int) -> tuple[Recorder, list[float]]:
    """A recorder with a clock of its own: the list holds "now"."""
    now = [1_794_000_000.0]
    limits = {"max_bytes": 1 << 20, "keep": 3, **kwargs}
    return Recorder(folder, name, **limits, clock=lambda: now[0]), now


def _write(recorder: Recorder, now: list[float], **kwargs: bool) -> Path:
    assert recorder.write([Chunk(now[0], "rx", b"x")], "rx", **kwargs)
    path = recorder.files()[-1]
    os.utime(path, (now[0], now[0]))
    now[0] += 10
    return path


def test_a_recording_goes_on_in_its_file_and_a_switch_begins_a_new_one(tmp_path: Path) -> None:
    recorder, now = _recorder(tmp_path)
    first = _write(recorder, now)
    assert _write(recorder, now) == first  # a restart of the app: still the same file
    second = _write(recorder, now, fresh=True)
    assert second != first and second.name > first.name
    assert [p.name for p in recorder.files()] == [first.name, second.name]


def test_files_above_the_limit_go_also_when_it_was_lowered_and_old_names_with_them(
    tmp_path: Path,
) -> None:
    tmp_path.joinpath("ehz.log").write_text("old running\n")
    tmp_path.joinpath("ehz.log.1").write_text("old\n")
    os.utime(tmp_path / "ehz.log", (100, 100))
    os.utime(tmp_path / "ehz.log.1", (50, 50))
    for keep_alone in ("ehzweiter.log", "ehz-capture-20261109-104012.jsonl", "ehz-2.log"):
        tmp_path.joinpath(keep_alone).write_text("not this connection's recording\n")
    recorder, now = _recorder(tmp_path, keep=2)
    new = _write(recorder, now)  # an old file does not go on: when it began is not known
    assert re.fullmatch(r"ehz-\d{8}-\d{6}\.log", new.name)
    assert [p.name for p in recorder.files()] == ["ehz.log.1", "ehz.log", new.name]
    second = _write(recorder, now, fresh=True)
    assert [p.name for p in recorder.files()] == ["ehz.log", new.name, second.name]
    lowered, now = _recorder(tmp_path, keep=0)
    now[0] += 100
    third = _write(lowered, now, fresh=True)
    assert [p.name for p in lowered.files()] == [third.name]
    assert all((tmp_path / n).exists() for n in ("ehzweiter.log", "ehz-2.log"))
    assert (tmp_path / "ehz-capture-20261109-104012.jsonl").exists()


def test_the_connection_of_a_recording_file_is_found_by_its_name() -> None:
    for name in (
        "pump.log",
        "pump.log.1",
        "pump-20261109-104012.log",
        "pump-capture-20261109-104012.jsonl",
        "pump-capture-20261109-104012-2.jsonl",
    ):
        assert recording_stem(name) == "pump"
    assert recording_stem("pump-2.log") == "pump-2"


async def test_switching_a_recording_on_begins_a_file(tmp_path: Path) -> None:
    hub = TraceHub(tmp_path / "rec", tmp_path / "shm")
    folder = tmp_path / "rec"

    async def poll(mode: str, at: int) -> None:
        hub.feed("a", Chunk(1.0, "rx", b"abc"))
        await hub.poll({"a": ("a", mode)}, 1 << 20, 3)
        for path in folder.glob("a-*.log"):
            if path.stat().st_mtime > at:
                os.utime(path, (at, at))

    await poll("both", 100)  # the first poll after a start goes on in the newest file
    start = sorted(folder.glob("a-*.log"))
    assert len(start) == 1
    first = start[0]
    await poll("both", 200)
    assert sorted(folder.glob("a-*.log")) == [first]
    await poll("off", 300)
    time.sleep(1.1)  # the name has the second it began
    await poll("both", 400)
    assert len(list(folder.glob("a-*.log"))) == 2
