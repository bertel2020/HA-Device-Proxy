"""The EnOcean proxy against a fake gateway reached over TCP (like ser2net or an MGW)."""

import asyncio
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import replace
from typing import Any

import pytest

from device_proxy import enocean, esp
from device_proxy.enocean import REPLAY_REQUEST, REPLAY_REQUEST_TS, EnOceanProxy
from device_proxy.esp import Splitter, crc8
from device_proxy.model import Connection, ValidationError

FRAME_A = bytes.fromhex("A55A0B0570000000002163433000")
FRAME_B = bytes.fromhex("A55A0B0550000000002163433000")
COMMAND = bytes.fromhex("A55A6B0501000000FFB744813000")  # TRT RPS: sent over the air
BASE_ID_READ = bytes.fromhex("A55AAB5800000000000000000003")  # TCT, ORG 0x58
BASE_ID_ANSWER = bytes.fromhex("A55A8B98FFB7448000000000000A")  # RMT, ORG 0x98
BUS_POLL_ANSWER = bytes.fromhex("A55A8BF800000000000000000000")  # RMT, ORG 0xF8: FAM14 bus


def esp3(data: bytes, optional: bytes = b"", packet_type: int = 1) -> bytes:
    header = len(data).to_bytes(2, "big") + bytes([len(optional), packet_type])
    return (
        b"\x55" + header + bytes([crc8(header)]) + data + optional + bytes([crc8(data + optional)])
    )


# frames


def test_esp2_frames_from_junk_and_pieces() -> None:
    splitter = Splitter("esp2")
    assert splitter.feed(b"\x00\x13" + FRAME_A[:5]) == []
    assert splitter.feed(FRAME_A[5:] + FRAME_A + FRAME_A[:1]) == [FRAME_A, FRAME_A]
    assert splitter.feed(FRAME_A[1:]) == [FRAME_A]


def test_esp3_frames_and_a_sync_byte_inside_data() -> None:
    first = esp3(bytes.fromhex("F6500021634330"), bytes.fromhex("01FFFFFFFF3700"))
    second = esp3(b"\x55\x55\x55")  # sync bytes inside the data
    splitter = Splitter("esp3")
    assert splitter.feed(b"\x55\x00" + first[:4]) == []  # a false sync before the frame
    assert splitter.feed(first[4:] + second) == [first, second]


def test_crc8_and_unknown_protocol() -> None:
    assert crc8(bytes.fromhex("00070701")) == 0x7A  # ESP3 header of a radio telegram
    with pytest.raises(ValueError):
        Splitter("esp4")


def test_frame_kinds() -> None:
    radio = esp3(bytes.fromhex("F6500021634330"))
    response = esp3(b"\x00", packet_type=2)
    command = esp3(b"\x08", packet_type=5)  # CO_RD_IDBASE
    assert esp.is_radio("esp3", radio) and not esp.is_response("esp3", radio)
    assert esp.is_response("esp3", response) and not esp.is_radio("esp3", response)
    assert esp.expects_response("esp3", command) and esp.expects_response("esp3", radio)

    bus_actor = bytes.fromhex("A55A8B0570000000000000013000")  # RMT ORG 05: actor answer
    poll = bytes.fromhex("A55AABFC00000000000000010000")  # TCT ORG FC: FAM14 poll
    assert esp.is_radio("esp2", FRAME_A) and esp.is_radio("esp2", bus_actor)
    assert not esp.is_radio("esp2", poll) and not esp.expects_response("esp2", poll)
    assert not esp.is_response("esp2", bus_actor)
    assert esp.describe("esp2", poll) == "bus"
    assert esp.describe("esp2", BASE_ID_ANSWER) == "answer"


def test_radio_info() -> None:
    assert esp.radio_info("esp2", FRAME_A) == ("RPS", "00-21-63-43")
    assert esp.radio_info("esp3", esp3(bytes.fromhex("F6500021634330"))) == ("RPS", "00-21-63-43")
    assert esp.radio_info("esp3", esp3(bytes.fromhex("A50000000AFF8000013F"))) == (
        "4BS",
        "FF-80-00-01",
    )
    assert esp.radio_info("esp3", esp3(b"\x00", packet_type=2)) is None
    assert esp.describe("esp2", FRAME_A) == "RPS 00-21-63-43"


def test_base_id_in_answers() -> None:
    assert esp.base_id("esp2", BASE_ID_ANSWER) == "FF-B7-44-80"
    assert esp.base_id("esp2", FRAME_A) is None
    request = esp.base_id_request("esp3")
    answer = esp3(bytes.fromhex("00FFB74480"), b"\x0a", packet_type=2)
    assert esp.base_id("esp3", answer, request) == "FF-B7-44-80"
    assert esp.base_id("esp3", answer, None) is None  # an ESP3 answer names no command
    assert esp.base_id("esp3", esp3(b"\x02", packet_type=2), request) is None  # not RET_OK
    assert esp.is_base_id_request("esp2", BASE_ID_READ)


def test_validation() -> None:
    def gateway(**values: Any) -> Connection:
        return Connection.from_dict(
            {"name": "FAM", "port": 9100, "kind": "enocean", "link": "serial", **values}
        )

    fam = gateway(device="/dev/ttyUSB0", baud=9600)
    assert fam.uses_device and fam.upstream == "/dev/ttyUSB0 9600n81"
    mgw = Connection.from_dict(
        {"name": "MGW", "port": 9101, "kind": "enocean", "link": "tcp", "host": "mgw.local"}
    )
    assert mgw.remote and mgw.upstream == "mgw.local:502"
    with pytest.raises(ValidationError) as err:
        gateway(device="/dev/ttyUSB0", esp_protocol="esp4", send_gap_ms=-1, link="rtu")
    assert set(err.value.errors) == {"esp_protocol", "send_gap_ms", "link"}
    with pytest.raises(ValidationError) as err:
        gateway()
    assert "device" in err.value.errors


# the proxy


class FakeGateway:
    def __init__(self) -> None:
        self.received = bytearray()
        self.writers: list[asyncio.StreamWriter] = []
        self.server: asyncio.Server | None = None
        self.port = 0

    async def start(self, port: int = 0) -> "FakeGateway":
        self.server = await asyncio.start_server(self._client, "127.0.0.1", port)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.writers.append(writer)
        while data := await reader.read(1024):
            self.received += data

    def send(self, frame: bytes) -> None:
        for writer in self.writers:
            writer.write(frame)

    async def stop(self) -> None:
        for writer in self.writers:
            writer.close()
        assert self.server is not None
        self.server.close()
        await self.server.wait_closed()
        self.writers.clear()


async def _until(predicate: Callable[[], bool], timeout: float = 3.0) -> None:
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.01)


class Setup:
    def __init__(self, gateway: FakeGateway, proxy: EnOceanProxy) -> None:
        self.gateway, self.proxy = gateway, proxy
        self.events: list[tuple[str, dict[str, object]]] = []


@pytest.fixture
async def setup() -> AsyncIterator[Setup]:
    gateway = await FakeGateway().start()
    c = Connection(
        "FAM",
        "",
        0,
        kind="enocean",
        link="tcp",
        host="127.0.0.1",
        host_port=gateway.port,
        max_clients=10,
        send_gap_ms=0,
    )
    events: list[tuple[str, dict[str, object]]] = []

    def on_event(level: str, kind: str, **params: object) -> None:
        events.append((kind, params))

    proxy = EnOceanProxy(c, "all", on_event, lambda chunk: None)
    task = asyncio.create_task(proxy.run())
    await _until(lambda: proxy.listening and proxy.link.is_open and bool(gateway.writers))
    result = Setup(gateway, proxy)
    result.events = events
    yield result
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    await gateway.stop()


async def _connect(
    proxy: EnOceanProxy, replay: bool = False
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    reader, writer = await asyncio.open_connection("127.0.0.1", proxy.port)
    if replay:
        writer.write(REPLAY_REQUEST)
    return reader, writer


async def test_frames_reach_every_client_and_commands_stay_whole(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    (r1, w1), (r2, w2) = await _connect(proxy), await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 2)
    gateway.send(FRAME_A)
    assert await r1.readexactly(14) == FRAME_A
    assert await r2.readexactly(14) == FRAME_A

    # two clients send halves of their commands interleaved: the gateway gets whole frames
    w1.write(COMMAND[:6])
    w2.write(FRAME_B[:6])
    await asyncio.sleep(0.05)
    w1.write(COMMAND[6:])
    w2.write(FRAME_B[6:])
    await _until(lambda: len(gateway.received) == 28)
    assert {bytes(gateway.received[:14]), bytes(gateway.received[14:])} == {COMMAND, FRAME_B}
    assert proxy.stats.to_gateway == 2
    with pytest.raises(TimeoutError):  # no echo of one client's frames to the other
        await asyncio.wait_for(r2.readexactly(1), 0.1)
    assert ("client_connected", {"address": next(iter(proxy.clients))}) in setup.events
    w1.close()
    w2.close()


async def test_replay_of_telegrams_missed_while_away(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    gateway.send(FRAME_A)  # nobody listens: kept
    gateway.send(FRAME_B)
    await _until(lambda: proxy.stats.from_gateway == 2)

    plain, plain_writer = await _connect(proxy)  # a plain client does not get the replay
    reader, writer = await _connect(proxy, replay=True)
    assert await reader.readexactly(28) == FRAME_A + FRAME_B
    assert proxy.stats.replayed == 2
    gateway.send(FRAME_A)  # live, also to the plain client
    assert await reader.readexactly(14) == FRAME_A
    assert await plain.readexactly(14) == FRAME_A

    writer.close()  # e.g. Home Assistant restarts
    await _until(lambda: len(proxy.clients) == 1)
    gateway.send(FRAME_B)
    await _until(lambda: proxy.stats.from_gateway == 4)
    reader, writer = await _connect(proxy, replay=True)
    assert await reader.readexactly(14) == FRAME_B
    writer.close()
    plain_writer.close()


async def test_replay_with_reception_times(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    gateway.send(FRAME_A)
    await _until(lambda: proxy.stats.from_gateway == 1)
    reader, writer = await asyncio.open_connection("127.0.0.1", proxy.port)
    writer.write(REPLAY_REQUEST_TS[:6])  # the request may come in pieces
    await asyncio.sleep(0.05)
    writer.write(REPLAY_REQUEST_TS[6:])
    assert await reader.readline() == b"EOPX TS 1\n"
    stamp, frame = (await reader.readline()).decode().split()
    assert bytes.fromhex(frame) == FRAME_A and abs(float(stamp) - time.time()) < 5
    assert await reader.readline() == b"EOPX END\n"
    gateway.send(FRAME_B)  # then the live binary stream
    assert await reader.readexactly(14) == FRAME_B
    writer.close()


async def test_replay_keeps_radio_only_and_drops_old(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    now = [1000.0]
    proxy._clock = lambda: now[0]
    proxy.c = replace(proxy.c, replay_max_age_s=60)
    gateway.send(FRAME_A)  # will be too old
    await _until(lambda: proxy.stats.from_gateway == 1)
    now[0] += 120
    gateway.send(BUS_POLL_ANSWER)  # FAM14 polling: never kept
    gateway.send(FRAME_B)
    await _until(lambda: proxy.stats.from_gateway == 3)
    assert proxy.state()["replay"]["kept"] == 2
    reader, writer = await _connect(proxy, replay=True)
    assert await reader.readexactly(14) == FRAME_B
    assert proxy.stats.replayed == 1
    writer.close()


async def test_reconnects_to_the_gateway(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    port = gateway.port
    await gateway.stop()
    await _until(lambda: proxy.reachable is False)
    assert setup.events[-1][0] == "enocean_down"
    _reader, writer = await _connect(proxy)
    writer.write(COMMAND)  # gateway away: dropped, not queued forever
    await _until(lambda: proxy.stats.dropped == 1)
    restarted = await FakeGateway().start(port)
    setup.gateway = restarted
    await _until(lambda: proxy.reachable is True, timeout=10)
    assert ("enocean_back", {"target": f"127.0.0.1:{port}"}) in setup.events
    writer.write(COMMAND)
    await _until(lambda: bytes(restarted.received) == COMMAND)
    writer.close()


async def test_answers_go_to_the_asking_client(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    (r1, w1), (r2, w2) = await _connect(proxy), await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 2)
    w1.write(BASE_ID_READ)
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ)
    gateway.send(BASE_ID_ANSWER)
    gateway.send(FRAME_A)
    assert await r1.readexactly(28) == BASE_ID_ANSWER + FRAME_A
    assert await r2.readexactly(14) == FRAME_A  # the other client only sees the telegram
    assert proxy.base_id == "FF-B7-44-80"
    gateway.send(BASE_ID_ANSWER)  # nobody asked: everyone gets it
    assert await r2.readexactly(14) == BASE_ID_ANSWER
    w1.close()
    w2.close()


async def test_allowed_clients_and_slow_clients(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    proxy.c = replace(proxy.c, remaddr="192.168.1.0/24")
    reader, writer = await _connect(proxy)
    assert await reader.read() == b""  # 127.0.0.1 is refused
    assert proxy.stats.refused == 1
    writer.close()

    proxy.c = replace(proxy.c, remaddr="127.0.0.1")
    monkeypatch.setattr(enocean, "CLIENT_BUFFER_LIMIT", -1)  # every write counts as too much
    _reader, writer = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    gateway.send(FRAME_A)
    await _until(lambda: not proxy.clients)
    assert proxy.stats.slow_clients == 1
    assert setup.events[-1][0] in ("client_dropped", "client_disconnected")
    writer.close()


async def test_places_and_the_lock_of_a_capture(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    proxy.c = replace(proxy.c, max_clients=1)
    _r1, w1 = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    r2, w2 = await _connect(proxy)
    assert await r2.read() == b""  # all places taken
    assert setup.events[-1][0] == "client_refused"
    proxy.exclusive_peer = "192.0.2.1"  # another program has the gateway alone
    w1.write(COMMAND)
    await _until(lambda: proxy.stats.locked == 1)
    proxy.exclusive_peer = "127.0.0.1"
    w1.write(COMMAND)
    await _until(lambda: bytes(gateway.received) == COMMAND)
    w1.close()
    w2.close()


async def test_duty_cycle_and_the_gateway_test(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    _reader, writer = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    for _ in range(3):
        writer.write(COMMAND)  # TRT radio telegrams over the air
    writer.write(BASE_ID_READ)  # a gateway command: no air time
    await _until(lambda: proxy.stats.to_gateway == 4)
    duty = proxy.duty_cycle()
    assert duty["telegrams"] == 3
    assert 0 < duty["ms"] < 20 and duty["of_limit"] < 1
    writer.close()

    async def answer_base_id() -> None:
        while True:
            await asyncio.sleep(0.01)
            while BASE_ID_READ in gateway.received:
                index = gateway.received.index(BASE_ID_READ)
                del gateway.received[index : index + 14]
                gateway.send(BASE_ID_ANSWER)

    task = asyncio.create_task(answer_base_id())
    result = await proxy.gateway_test(3)
    assert (result["sent"], result["answered"], result["lost"]) == (3, 3, 0)
    assert await proxy.request(BASE_ID_READ) == BASE_ID_ANSWER
    with pytest.raises(ValueError):
        await proxy.request(BASE_ID_READ[:5])
    task.cancel()


async def test_state_and_mqtt_values(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    reader, writer = await _connect(proxy, replay=True)
    await _until(lambda: len(proxy.clients) == 1)
    gateway.send(FRAME_A)
    await reader.readexactly(14)
    state = proxy.state()
    assert state["connected"] and state["reachable"] and state["protocol"] == "esp2"
    assert state["frames"]["from_gateway"] == 1
    assert enocean.mqtt_state(state) == {"reachable": True, "telegrams": 1, "duty_cycle": 0.0}
    (client,) = proxy.clients.values()
    row = enocean.client_row(client)
    assert row["replay"] and row["bytes_to_client"] == 14 and row["bytes_from_client"] == 12
    writer.close()
