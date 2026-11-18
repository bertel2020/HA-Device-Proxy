"""The 1-Wire proxy against a fake owserver."""

import asyncio
import errno
import struct
from collections.abc import AsyncIterator, Callable
from dataclasses import replace

import pytest

from device_proxy import onewire
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
        self.values = {f"/{SENSOR}/temperature": b"     21.5", f"/{SWITCH}/PIO.A": b"0"}
        self.ping = False
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
        try:
            while True:
                head = await reader.readexactly(HEADER.size)
                _version, payload, kind, flags, _size, _offset = HEADER.unpack(head)
                body = await reader.readexactly(payload)
                path, _, data = body.partition(b"\0")
                self.requests.append((kind, path.decode(), data))
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
            return [answer(0, DIRALL.encode() + b"\0")]
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
        (ADAPTER, "DS1420"),
        (SWITCH, "DS2413"),
    ]
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
    assert setup.server.connections == 1 + 1  # the probe's and this one
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
        replace(c, link="usb").validate()
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
    assert {e["key"] for e in entities.values()} == {"reachable", "onewire_devices", "requests"}
    state = {"reachable": True, "devices": [{}, {}], "requests": {"read": 4, "dir": 1}}
    assert onewire.mqtt_state(state) == {"reachable": True, "onewire_devices": 2, "requests": 5}
