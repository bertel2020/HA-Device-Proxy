"""The 1-Wire proxy against a fake owserver."""

import asyncio
import errno
import struct
import sys
from collections.abc import AsyncIterator, Callable
from dataclasses import replace
from pathlib import Path

import pytest

from device_proxy import onewire, onewire_bus
from device_proxy.devices import UsbDevice, usb_devices
from device_proxy.kinds import PROXIED
from device_proxy.model import AppConfig, Connection, ValidationError
from device_proxy.onewire import (
    HEADER,
    MSG_DIR,
    MSG_DIRALL,
    MSG_WRITE,
    OneWireProxy,
    ProtocolError,
    answer,
    parse_devices,
    request,
)

MSG_READ = 2
SENSOR = "28.A1B2C3D4E5F6"
ADAPTER = "81.0000005F2A1B"
SWITCH = "3A.112233445566"
# the proxy closed the connection (a reset when the request was not read yet)
CLOSED = (asyncio.IncompleteReadError, ConnectionError)
DIRALL = f"/{SENSOR},/{ADAPTER},/{SWITCH},/bus.0,/settings,/system,/statistics,/structure"


class FakeOwserver:
    """Answers DIRALL, DIR, READ and WRITE like owserver; keeps the connection open only when
    the request asks for persistence, and sends a ping before slow answers."""

    def __init__(self) -> None:
        self.requests: list[tuple[int, str, bytes]] = []
        self.values = {
            f"/{SENSOR}/temperature": b"     21.5",
            f"/{SWITCH}/PIO.A": b"0",
            f"/{SENSOR}/power": b"           0",
            f"/{SWITCH}/type": b"DS2413",
            "/bus.0/interface/settings/name": b"DS9490",
            "/system/configuration/version": b"3.2p4",
            "/statistics/errors/CRC8_errors": b"           3",
            "/statistics/errors/CRC8_tries": b"         300",
        }
        self.ping = False
        self.served: list[tuple[int, int, str]] = []  # (connection, type, path)
        self.dirall = DIRALL
        self.connections = 0
        self._server: asyncio.Server | None = None
        self.port = 0

    async def start(self) -> "FakeOwserver":
        self._server = await asyncio.start_server(self._serve, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def stop(self) -> None:
        assert self._server is not None
        self._server.close()

    async def _serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.connections += 1
        connection = self.connections
        try:
            while True:
                head = await reader.readexactly(HEADER.size)
                _version, payload, kind, flags, _size, _offset = HEADER.unpack(head)
                body = await reader.readexactly(payload)
                path, _, data = body.partition(b"\0")
                self.requests.append((kind, path.decode(), data))
                self.served.append((connection, kind, path.decode()))
                keep = flags & onewire.PERSISTENCE
                if self.ping:
                    writer.write(HEADER.pack(0, -1, 0, 0, 0, 0))
                for message in self._answer(kind, path.decode(), data):
                    writer.write(message[:12] + struct.pack(">i", keep) + message[16:])
                await writer.drain()
                if not keep:
                    break
        except asyncio.IncompleteReadError:
            pass
        finally:
            writer.close()

    def _answer(self, kind: int, path: str, data: bytes) -> list[bytes]:
        if kind == MSG_DIRALL:
            return [answer(0, self.dirall.encode() + b"\0")]
        if kind == MSG_DIR:
            return [answer(0, f"/{SENSOR}".encode()), answer(0, f"/{SWITCH}".encode()), answer(0)]
        if kind == MSG_READ:
            value = self.values.get(path)
            return [answer(-errno.ENOENT)] if value is None else [answer(len(value), value)]
        if kind == MSG_WRITE:
            self.values[path] = data
            return [answer(0)]
        return [answer(-errno.EINVAL)]


class Setup:
    def __init__(self, server: FakeOwserver, proxy: OneWireProxy) -> None:
        self.server, self.proxy = server, proxy
        self.events: list[tuple[str, dict[str, object]]] = []
        self.trace: list[onewire.Chunk] = []

    def kinds(self) -> list[str]:
        return [kind for kind, _ in self.events]


async def _until(condition: Callable[[], bool], timeout: float = 2.0) -> None:
    async with asyncio.timeout(timeout):
        while not condition():
            await asyncio.sleep(0.01)


@pytest.fixture(autouse=True)
def device_book(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The devices seen go to a file of the test, not to /data."""
    path = tmp_path / "onewire_devices.json"
    monkeypatch.setattr(onewire_bus, "KNOWN_FILE", path)
    return path


@pytest.fixture
async def setup() -> AsyncIterator[Setup]:
    server = await FakeOwserver().start()
    c = Connection(
        "1-Wire", "", 0, kind="onewire", link="owserver", host="127.0.0.1",
        host_port=server.port, max_clients=5,
    )  # fmt: skip
    proxy = OneWireProxy(c, "all", lambda *a, **k: None, lambda chunk: None)
    result = Setup(server, proxy)
    proxy.on_event = lambda level, kind, **params: result.events.append((kind, params))
    proxy.on_trace = result.trace.append
    task = asyncio.create_task(proxy.run())
    await _until(lambda: proxy.listening and proxy.reachable is True)
    yield result
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    await server.stop()


async def ask(
    port: int, kind: int, path: str, data: bytes = b"", flags: int = 0
) -> tuple[int, bytes]:
    """One request over a connection of its own, as pyownet does: (return value, payload)."""
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    payload = path.encode() + b"\0" + data
    writer.write(HEADER.pack(0, len(payload), kind, flags, len(data), 0) + payload)
    try:
        while True:
            head = await reader.readexactly(HEADER.size)
            _version, length, ret, _flags, _size, _offset = HEADER.unpack(head)
            if length != -1:
                return ret, await reader.readexactly(length)
    finally:
        writer.close()


# the protocol


def test_messages_and_the_device_list() -> None:
    message = request(MSG_DIRALL, "/")
    assert HEADER.unpack(message[:24]) == (0, 2, MSG_DIRALL, 0, 0, 0)
    assert message[24:] == b"/\0"
    assert parse_devices(DIRALL.encode() + b"\0") == [SENSOR, ADAPTER, SWITCH]
    assert parse_devices(b"/uncached/28.a1b2c3d4e5f6,/28.A1B2C3D4E5F6") == [SENSOR]
    assert parse_devices(b"") == []


async def test_a_request_that_is_no_owserver_message_is_refused() -> None:
    reader = asyncio.StreamReader()
    reader.feed_data(HEADER.pack(0, 10_000_000, MSG_READ, 0, 0, 0))
    with pytest.raises(ProtocolError):
        await onewire.read_request(reader)
    reader = asyncio.StreamReader()  # from another owserver: 16-byte tokens after the path
    reader.feed_data(
        HEADER.pack(onewire.SERVER_MESSAGE | 1, 2, MSG_READ, 0, 0, 0) + b"/\0" + b"t" * 16
    )
    data, kind, _flags, path = await onewire.read_request(reader)
    assert (len(data), kind, path) == (24 + 2 + 16, MSG_READ, "/")


# the proxy


async def test_the_device_list_and_reachability(setup: Setup) -> None:
    state = setup.proxy.state()
    assert state["reachable"] is True
    assert [(d["id"], d["type"]) for d in state["devices"]] == [
        (SENSOR, "DS18B20"),
        (SWITCH, "DS2413"),
        (ADAPTER, "DS1420"),
    ]
    assert (state["present"], state["missing"]) == (3, [])
    assert setup.proxy.probe_ms is not None
    c = setup.proxy.c
    setup.proxy.c = replace(c, host_port=1)  # nothing listens there
    await setup.proxy.probe()
    assert setup.proxy.reachable is False
    assert setup.kinds()[-1] == "onewire_down"
    assert setup.proxy.state()["last_error"]
    setup.proxy.c = c
    await setup.proxy.probe()
    assert setup.kinds()[-1] == "onewire_back"


async def test_reads_pass_through_and_a_host_is_one_client(setup: Setup) -> None:
    port = setup.proxy.port
    assert await ask(port, MSG_READ, f"/{SENSOR}/temperature") == (9, b"     21.5")
    assert await ask(port, MSG_READ, f"/{SENSOR}/temperature") == (9, b"     21.5")
    ret, _ = await ask(port, MSG_READ, "/10.000000000000/temperature")
    assert ret == -errno.ENOENT
    assert list(setup.proxy.clients) == ["127.0.0.1"]  # three connections, one client
    assert setup.kinds().count("client_connected") == 1
    state = setup.proxy.state()
    assert state["requests"]["read"] == 3
    assert state["errors"] == 1
    assert state["last_error"] == "ENOENT /10.000000000000/temperature"
    assert state["answer_ms"]["avg"] is not None
    row = PROXIED["onewire"].client_row(setup.proxy.clients["127.0.0.1"])
    assert (row["requests"], row["errors"], row["last_path"]) == (
        3,
        1,
        "/10.000000000000/temperature",
    )
    infos = [chunk.info for chunk in setup.trace]
    assert f"read /{SENSOR}/temperature · 127.0.0.1" in infos  # the request
    assert f"read /{SENSOR}/temperature = 21.5 · 127.0.0.1" in infos  # the answer
    assert "ENOENT /10.000000000000/temperature · 127.0.0.1" in infos


async def test_a_persistent_connection_with_pings_and_a_directory(setup: Setup) -> None:
    setup.server.ping = True
    reader, writer = await asyncio.open_connection("127.0.0.1", setup.proxy.port)
    flags = onewire.PERSISTENCE

    async def message() -> tuple[int, int, bytes]:
        head = await reader.readexactly(HEADER.size)
        _version, length, ret, got_flags, _size, _offset = HEADER.unpack(head)
        return ret, got_flags, await reader.readexactly(max(length, 0))

    writer.write(request(MSG_DIR, "/", flags))
    received = [await message() for _ in range(4)]  # a ping, two entries, the end
    assert received[0][2] == b"" and received[-1] == (0, flags, b"")
    assert [r[2] for r in received[1:3]] == [f"/{SENSOR}".encode(), f"/{SWITCH}".encode()]
    writer.write(request(MSG_READ, f"/{SWITCH}/PIO.A", flags, 1))  # the same connection
    received = [await message() for _ in range(2)]
    assert received[1][2] == b"0"
    # both requests on one connection to the owserver (the app's own requests, such as the
    # sensors' supply, may run meanwhile on others)
    (dir_on,) = [n for n, kind, path in setup.server.served if kind == MSG_DIR]
    (read_on,) = [n for n, kind, path in setup.server.served if path == f"/{SWITCH}/PIO.A"]
    assert dir_on == read_on
    assert setup.proxy.state()["connections"] == 1
    writer.close()
    await _until(lambda: setup.proxy.state()["connections"] == 0)


async def test_writes_only_from_allowed_clients(setup: Setup) -> None:
    port, path = setup.proxy.port, f"/{SWITCH}/PIO.A"
    assert (await ask(port, MSG_WRITE, path, b"1"))[0] == 0  # write_access "all"
    assert setup.server.values[path] == b"1"
    setup.proxy.c = replace(setup.proxy.c, write_access="listed", write_clients="192.168.1.5")
    assert (await ask(port, MSG_WRITE, path, b"0"))[0] == -errno.EACCES
    assert setup.server.values[path] == b"1"  # never reached the owserver
    assert (await ask(port, MSG_READ, path))[1] == b"1"  # reading still works
    setup.proxy.c = replace(setup.proxy.c, write_clients="127.0.0.1")
    assert (await ask(port, MSG_WRITE, path, b"0"))[0] == 0
    assert setup.proxy.state()["blocked"] == 1
    assert ("onewire_write_blocked", {"address": "127.0.0.1", "path": path}) in setup.events
    # every write in the log, the newest first, with its value and how it ended
    log = [(w["path"], w["value"], w["result"]) for w in setup.proxy.state()["writes"]]
    assert log == [(path, "0", "ok"), (path, "0", "EACCES"), (path, "1", "ok")]


async def test_clients_refused_and_gone(setup: Setup, monkeypatch: pytest.MonkeyPatch) -> None:
    port = setup.proxy.port
    setup.proxy.c = replace(setup.proxy.c, remaddr="192.168.1.0/24")
    with pytest.raises(CLOSED):
        await ask(port, MSG_READ, f"/{SENSOR}/temperature")
    assert setup.kinds()[-1] == "client_refused_network"
    setup.proxy.c = replace(setup.proxy.c, remaddr="", max_clients=1)
    setup.proxy.clients["192.168.1.9"] = onewire._Host("192.168.1.9", "192.168.1.9", 0, 0, 0)
    with pytest.raises(CLOSED):
        await ask(port, MSG_READ, f"/{SENSOR}/temperature")
    assert setup.kinds()[-1] == "client_refused"
    # a port check (connect, say nothing) is no client
    del setup.proxy.clients["192.168.1.9"]
    _reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.close()
    await asyncio.sleep(0.05)
    assert setup.proxy.clients == {}
    await ask(port, MSG_READ, f"/{SENSOR}/temperature")
    await _until(lambda: not setup.proxy.clients["127.0.0.1"].writers)  # its connection ended
    monkeypatch.setattr(onewire, "IDLE_AFTER", 0.0)
    setup.proxy.sweep()
    assert setup.proxy.clients == {}
    assert setup.kinds()[-1] == "client_disconnected"


async def test_an_unreachable_owserver_closes_the_client(setup: Setup) -> None:
    setup.proxy.c = replace(setup.proxy.c, host_port=1)
    with pytest.raises(CLOSED):
        await ask(setup.proxy.port, MSG_READ, f"/{SENSOR}/temperature")
    assert setup.proxy.reachable is False
    assert setup.kinds()[-1] == "onewire_down"


# configuration


def test_a_onewire_connection_from_the_form() -> None:
    c = Connection.from_dict(
        {"name": "1-Wire", "port": 4304, "kind": "onewire", "link": "owserver", "host": "vm"}
    )
    assert (c.host_port, c.write_access, c.uses_device, c.upstream) == (
        4304,
        "all",
        False,
        "vm:4304",
    )
    with pytest.raises(ValidationError) as err:
        replace(c, link="serial").validate()
    assert "link" in err.value.errors
    with pytest.raises(ValidationError) as err:
        replace(c, write_access="listed", write_clients="nope").validate()
    assert "write_clients" in err.value.errors
    with pytest.raises(ValidationError) as err:
        replace(c, host="127.0.0.1").validate()  # itself
    assert "host_port" in err.value.errors
    two = AppConfig(connections=(c, replace(c, id="0000000c", name="B", port=4305)))
    with pytest.raises(ValidationError) as err:
        two.validate()
    assert "connections.1.host" in err.value.errors


def test_a_change_of_access_or_name_keeps_the_proxy_running() -> None:
    c = Connection("1-Wire", "", 4304, kind="onewire", link="owserver", host="vm", host_port=4304)
    key = onewire.restart_key(c, "all")
    same = replace(c, name="Bus", write_access="none", max_clients=3, timeout=60)
    assert onewire.restart_key(same, "all") == key
    assert onewire.restart_key(replace(c, host="other"), "all") != key
    assert onewire.restart_key(replace(c, remaddr="127.0.0.1"), "all") != key


def test_entities() -> None:
    c = Connection("1-Wire", "", 4304, kind="onewire", link="owserver", host="vm")
    entities = onewire.mqtt_entities("homeassistant", c, lambda key, **kw: {"key": key, **kw})
    keys = {"reachable", "onewire_devices", "onewire_missing", "requests"}
    assert {e["key"] for e in entities.values()} == keys
    state = {
        "reachable": True,
        "present": 2,
        "missing": ["28.A"],
        "requests": {"read": 4, "dir": 1},
    }
    assert onewire.mqtt_state(state) == {
        "reachable": True,
        "onewire_devices": 2,
        "onewire_missing": 1,
        "requests": 5,
    }


# the USB adapter of this host, with the app's own owserver (link "usb")

FAKE = Path(__file__).with_name("fake_owserver.py")


@pytest.fixture
def fake_owserver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """owserver is the fake: a script the app starts as it would start owserver; the
    arguments of every start go to the returned file."""
    script = tmp_path / "owserver"
    script.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n')
    script.chmod(0o755)
    starts = tmp_path / "starts.txt"
    monkeypatch.setattr(onewire, "OWSERVER", str(script))
    monkeypatch.setattr(onewire, "FIRST_PROBE", 5.0)
    monkeypatch.setattr(onewire, "OWSERVER_DELAYS", (0.1,))
    monkeypatch.setattr(onewire, "USB_BACK", 0.1)
    monkeypatch.setenv("FAKE_OWSERVER_LOG", str(starts))
    monkeypatch.delenv("FAKE_OWSERVER_MODE", raising=False)
    return starts


def usb_bus() -> Connection:
    return Connection("1-Wire", "", 0, kind="onewire", link="usb", max_clients=5)


USB_ADAPTER = UsbDevice("1-1.2", "/dev/bus/usb/001/004", "DS1490F 2-in-1 Fob", "ds2490")


async def _running(c: Connection, events: list[str]) -> tuple[OneWireProxy, asyncio.Task[None]]:
    proxy = OneWireProxy(c, "all", lambda level, kind, **p: events.append(kind), lambda ch: None)
    proxy.find_adapters = lambda: [USB_ADAPTER]
    task = asyncio.create_task(proxy.run())
    return proxy, task


async def _stop(task: asyncio.Task[None]) -> None:
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def test_the_own_owserver_on_the_usb_adapter(fake_owserver: Path) -> None:
    events: list[str] = []
    proxy, task = await _running(usb_bus(), events)
    try:
        await _until(lambda: proxy.reachable is True, 10)
        assert proxy.owserver is not None and proxy.owserver.running
        args = fake_owserver.read_text().split()
        assert args[args.index("-p") + 1] == f"127.0.0.1:{proxy.owserver.port}"
        assert "-u" in args and "--foreground" in args
        assert "--timeout_volatile=15" in args  # the cache for read values
        await proxy.owserver.restart()  # each start picks a free port again
        await _until(lambda: len(fake_owserver.read_text().splitlines()) == 2)
        again = fake_owserver.read_text().splitlines()[1].split()
        assert again[again.index("-p") + 1] == f"127.0.0.1:{proxy.owserver.port}"
        await proxy._owserver_ready()
        assert proxy.devices == ["28.A1B2C3D4E5F6", "81.0000005F2A1B"]
        assert await ask(proxy.port, MSG_READ, "/28.A1B2C3D4E5F6/temperature") == (9, b"     21.5")
        await proxy.look_after()
        state = proxy.state()
        assert state["source"] == "usb" and state["owserver"]["running"]
        assert state["adapters"] == [
            {"place": "1-1.2", "product": "DS1490F 2-in-1 Fob", "driver": "ds2490"}
        ]
        assert "owserver ready" in state["owserver"]["log"]
    finally:
        await _stop(task)
    await _until(lambda: not proxy.owserver.running)  # ended with the connection


async def test_an_owserver_that_ends_starts_again(
    fake_owserver: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_OWSERVER_MODE", "fail")
    monkeypatch.setattr(onewire, "PROBE_SECONDS", 0.2)
    events: list[str] = []
    proxy, task = await _running(usb_bus(), events)
    try:
        await _until(lambda: proxy.owserver is not None and proxy.owserver.restarts >= 2, 10)
        assert "onewire_owserver_ended" in events
        assert proxy.owserver.last_exit == 1
        assert "Could not open the USB adapter" in proxy.owserver.log[-1]
        monkeypatch.setenv("FAKE_OWSERVER_MODE", "")  # the adapter is back
        await _until(lambda: proxy.reachable is True, 10)
    finally:
        await _stop(task)


async def test_the_watchdog_restarts_owserver_then_resets_the_adapter(
    fake_owserver: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(onewire, "PROBE_SECONDS", 3600)  # the test looks itself
    monkeypatch.setattr(onewire, "PROBE_TIMEOUT", 0.3)
    monkeypatch.setenv("FAKE_OWSERVER_MODE", "hang")  # the DS2490 stopped answering
    events: list[str] = []
    resets: list[str] = []
    proxy, task = await _running(usb_bus(), events)
    proxy.reset_adapter = resets.append
    try:
        assert proxy.owserver is not None
        await _until(lambda: proxy.reachable is False, 10)
        starts = lambda: proxy.owserver.starts  # noqa: E731
        for _round in range(onewire.RESET_AFTER):
            for _miss in range(onewire.WATCHDOG_MISSES):
                await proxy.probe()
                await proxy.look_after()
            assert events[-1] == "onewire_restarted"
        await _until(lambda: proxy.owserver.running and starts() == 1 + onewire.RESET_AFTER, 10)
        assert "onewire_owserver_ended" not in events  # a restart on purpose is no failure
        monkeypatch.setenv("FAKE_OWSERVER_MODE", "")  # after the reset the adapter answers
        for _miss in range(onewire.WATCHDOG_MISSES):
            await proxy.probe()
            await proxy.look_after()
        assert resets == ["/dev/bus/usb/001/004"]
        assert events[-1] == "onewire_usb_reset" and proxy.watchdog.resets == 1
        await _until(lambda: proxy.owserver.running and starts() == 2 + onewire.RESET_AFTER, 10)
        for _try in range(50):  # the new owserver is listening soon
            await proxy.probe()
            if proxy.reachable:
                break
            await asyncio.sleep(0.1)
        await proxy.look_after()
        assert proxy.reachable is True
        assert (proxy.watchdog.misses, proxy.watchdog.restarts) == (0, 0)
    finally:
        await _stop(task)


def test_a_usb_bus_needs_no_address_and_only_one_is_allowed() -> None:
    c = Connection.from_dict({"name": "Bus", "port": 4304, "kind": "onewire", "link": "usb"})
    assert (c.onewire_usb, c.remote, c.uses_device, c.upstream) == (True, False, False, "USB")
    other = replace(c, id="0000000e", name="Bus 2", port=4305)
    with pytest.raises(ValidationError) as err:
        AppConfig(connections=(c, other)).validate()
    assert err.value.errors == {"connections.1.link": "the USB adapter is used by Bus"}
    AppConfig(connections=(c, replace(other, link="owserver", host="vm"))).validate()
    with pytest.raises(ValidationError) as err:
        replace(c, owserver_cache_s=-1).validate()
    assert "owserver_cache_s" in err.value.errors
    # another cache time starts the own owserver again with it
    key = onewire.restart_key(c, "all")
    assert onewire.restart_key(replace(c, owserver_cache_s=60), "all") != key
    owserver = onewire.OwServer(4304, lambda code, delay: None, "owserver", cache_s=0)
    assert owserver.command()[-1] == "--timeout_volatile=0"


def test_usb_devices_from_sysfs(tmp_path: Path) -> None:
    devices = tmp_path / "sys" / "bus" / "usb" / "devices"
    for name, vendor, product, driver in (
        ("1-1.2", "04fa", "2490", "ds2490"),
        ("1-1.3", "0403", "6001", "ftdi_sio"),
    ):
        d = devices / name
        (d / f"{name}:1.0").mkdir(parents=True)
        for key, value in (("idVendor", vendor), ("idProduct", product), ("busnum", "1"),
                           ("devnum", "4"), ("product", "DS1490F")):  # fmt: skip
            (d / key).write_text(value + "\n")
        drivers = tmp_path / "drivers" / driver
        drivers.mkdir(parents=True)
        (d / f"{name}:1.0" / "driver").symlink_to(drivers)
    (devices / "1-1.2:1.0").mkdir()  # an interface, not a device
    found = usb_devices("04fa", "2490", tmp_path / "dev", tmp_path / "sys")
    assert found == [UsbDevice("1-1.2", str(tmp_path / "dev/bus/usb/001/004"), "DS1490F", "ds2490")]


async def test_values_and_counters_reach_the_state(setup: Setup) -> None:
    port = setup.proxy.port
    await ask(port, MSG_READ, f"/{SENSOR}/temperature")
    await setup.proxy.read_statistics()
    state = setup.proxy.state()
    sensor = next(d for d in state["devices"] if d["id"] == SENSOR)
    assert sensor["values"]["temperature"]["value"] == "21.5" and sensor["type"] == "DS18B20"
    assert state["statistics"]["crc_errors"] == 3 and state["statistics"]["crc_share"] == 1.0
    assert sensor["power"] == "parasite"  # asked once when it was listed
    switch = next(d for d in state["devices"] if d["id"] == SWITCH)
    assert (switch["chip"], switch["type"]) == ("DS2413", "DS2413")  # said by the owserver
    assert (sensor["chip"], sensor["type"]) == ("", "DS18B20")  # not said: the usual one
    # what the owserver says about its adapter; what it does not have (address) stays out
    assert state["info"] == {"name": "DS9490", "owserver": "3.2p4"}
    # the owserver no longer lists the switch: missing after MISSING_AFTER lists
    setup.server.dirall = f"/{SENSOR},/{ADAPTER}"
    for _ in range(onewire_bus.MISSING_AFTER):
        await setup.proxy.probe()
    assert setup.proxy.state()["missing"] == [SWITCH]
    assert ("onewire_device_missing", {"device": SWITCH}) in setup.events
    assert setup.proxy.forget(SWITCH) and setup.proxy.state()["missing"] == []


async def test_a_search_of_the_bus_now(setup: Setup) -> None:
    result = await setup.proxy.scan()
    assert result["devices"] == [SENSOR, ADAPTER, SWITCH] and result["ms"] is not None
    assert (MSG_DIRALL, "/uncached/", b"") in setup.server.requests  # not the cached list
    setup.proxy.c = replace(setup.proxy.c, host_port=1)
    with pytest.raises(ValueError):
        await setup.proxy.scan()


async def test_a_connection_that_sends_no_request_is_closed(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(onewire, "FIRST_REQUEST", 0.2)
    reader, writer = await asyncio.open_connection("127.0.0.1", setup.proxy.port)
    writer.write(request(MSG_READ, f"/{SENSOR}/temperature")[:10])  # half a header, then silence
    await _until(lambda: setup.proxy.state()["connections"] == 1)
    assert await asyncio.wait_for(reader.read(), 2) == b""  # closed by the proxy
    await _until(lambda: setup.proxy.state()["connections"] == 0)
    assert setup.proxy.clients == {}  # it never asked: no client
    writer.close()
