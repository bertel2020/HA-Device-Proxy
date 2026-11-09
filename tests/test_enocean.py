"""The EnOcean proxy against a fake gateway reached over TCP (like ser2net or an MGW)."""

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from device_proxy import enocean, esp
from device_proxy.enocean import REPLAY_REQUEST, REPLAY_REQUEST_TS, EnOceanProxy
from device_proxy.esp import Splitter, crc8
from device_proxy.model import Connection, ValidationError

FRAME_A = bytes.fromhex("A55A0B0570000000002163433077")
FRAME_B = bytes.fromhex("A55A0B0550000000002163433057")
COMMAND = bytes.fromhex("A55A6B0501000000FFABCD813099")  # TRT RPS: sent over the air
BASE_ID_READ = bytes.fromhex("A55AAB5800000000000000000003")  # TCT, ORG 0x58
BASE_ID_ANSWER = bytes.fromhex("A55A8B98FFABCD8000000000001A")  # RMT, ORG 0x98
BUS_POLL_ANSWER = bytes.fromhex("A55A8BF800000000000000000083")  # RMT, ORG 0xF8: FAM14 bus


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


def test_esp3_does_not_wait_on_a_false_header() -> None:
    radio = esp3(bytes.fromhex("F6500021634330"))
    for length in (0x0100, 0xF000):  # within and above the limit
        header = length.to_bytes(2, "big") + b"\x00\x01"
        junk = b"\x55" + header + bytes([crc8(header)])  # passes the header CRC
        assert Splitter("esp3").feed(junk + radio * 50) == [radio] * 50
    now = [0.0]
    splitter = Splitter("esp3", clock=lambda: now[0])
    header = (0x20).to_bytes(2, "big") + b"\x00\x01"
    assert splitter.feed(b"\x55" + header + bytes([crc8(header)])) == []  # waits for 32 bytes
    now[0] = 1.0  # the rest never came
    assert splitter.feed(radio) == [radio]


def test_checksums_of_whole_frames() -> None:
    radio = esp3(bytes.fromhex("F6500021634330"))
    assert esp.checksum_error("esp3", radio) is None
    assert esp.checksum_error("esp3", radio[:-1] + bytes([radio[-1] ^ 1])) == (
        f"data CRC should be {radio[-1]:02X}"
    )
    assert esp.checksum_error("esp2", BASE_ID_READ) is None
    assert esp.checksum_error("esp2", BASE_ID_READ[:-1] + b"\x07") == "checksum should be 03"


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

    bus_actor = bytes.fromhex("A55A8B0570000000000000013031")  # RMT ORG 05: actor answer
    poll = bytes.fromhex("A55AABFC000000000000000100A8")  # TCT ORG FC: FAM14 poll
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
    assert esp.base_id("esp2", BASE_ID_ANSWER) == "FF-AB-CD-80"
    assert esp.base_id("esp2", FRAME_A) is None
    request = esp.base_id_request("esp3")
    answer = esp3(bytes.fromhex("00FFABCD80"), b"\x0a", packet_type=2)
    assert esp.base_id("esp3", answer, request) == "FF-AB-CD-80"
    assert esp.base_id("esp3", answer, None) is None  # an ESP3 answer names no command
    assert esp.base_id("esp3", esp3(b"\x02", packet_type=2), request) is None  # not RET_OK
    assert esp.is_base_id_request("esp2", BASE_ID_READ)


def test_base_id_changes() -> None:
    request = esp.base_id_request("esp3")
    answer = esp3(bytes.fromhex("00FFABCD80"), b"\x0a", packet_type=2)
    assert esp.base_id_writes_left("esp3", answer, request) == 10
    assert (
        esp.base_id_writes_left("esp3", esp3(bytes.fromhex("00FFABCD80"), packet_type=2), request)
        is None
    )
    assert esp.base_id_writes_left("esp2", BASE_ID_ANSWER, None) is None  # ESP2 does not tell
    raw = esp.parse_base_id("ff-ab-cd-80")
    assert raw == bytes.fromhex("FFABCD80")
    for bad in ("FF-AB-CD-81", "FF-7F-FF-80", "FF-AB-CD", "zz-00-00-00", "00-00-00-00"):
        with pytest.raises(ValueError):
            esp.parse_base_id(bad)
    write = esp.base_id_write_request("esp3", raw)
    assert write == esp3(bytes.fromhex("07FFABCD80"), packet_type=5)
    write2 = esp.base_id_write_request("esp2", raw)
    assert Splitter("esp2").feed(write2) == [write2] and write2[2:8].hex() == "ab18ffabcd80"
    assert esp.base_id_write_result("esp3", esp3(b"\x00", packet_type=2)) == "ok"
    assert esp.base_id_write_result("esp3", esp3(b"\x91", packet_type=2)) == "no_writes_left"
    assert esp.base_id_write_result("esp3", None) == "no_answer"
    ok2 = bytes.fromhex("A55A8B58000000000000000000")
    assert esp.base_id_write_result("esp2", ok2 + bytes([sum(ok2[2:]) & 0xFF])) == "ok"


async def test_the_base_id_is_set_and_read_back() -> None:
    class Esp3Gateway(FakeGateway):
        base = bytes.fromhex("FFABCD80")
        left = 3

        async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            self.writers.append(writer)
            splitter = Splitter("esp3")
            while data := await reader.read(1024):
                for frame in splitter.feed(data):
                    if frame[6] == 0x07 and self.left:
                        self.base, self.left = frame[7:11], self.left - 1
                        writer.write(esp3(b"\x00", packet_type=2))
                    elif frame[6] == 0x07:
                        writer.write(esp3(b"\x91", packet_type=2))
                    elif frame[6] == 0x08:
                        writer.write(esp3(b"\x00" + self.base, bytes([self.left]), 2))

    gateway = await Esp3Gateway().start()
    c = Connection(
        "USB",
        "",
        0,
        kind="enocean",
        link="tcp",
        host="127.0.0.1",
        host_port=gateway.port,
        esp_protocol="esp3",
    )
    proxy = EnOceanProxy(c, "all", lambda *a, **k: None, lambda chunk: None)
    task = asyncio.create_task(proxy.run())
    try:
        await _until(lambda: proxy.base_id_writes_left == 3)
        assert await proxy.set_base_id(bytes.fromhex("FF801000")) == "ok"
        assert (proxy.base_id, proxy.base_id_writes_left) == ("FF-80-10-00", 2)
        assert proxy.state()["base_id_writes_left"] == 2
        gateway.left = 0
        assert await proxy.set_base_id(bytes.fromhex("FF802000")) == "no_writes_left"
        assert (proxy.base_id, proxy.base_id_writes_left) == ("FF-80-10-00", 0)
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await gateway.stop()


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


def test_gateway_model() -> None:
    def gateway(**values: Any) -> Connection:
        return Connection.from_dict(
            {"name": "FAM", "port": 9100, "kind": "enocean", "link": "tcp", "host": "gw", **values}
        )

    assert gateway(model="").model == ""
    assert gateway(model="fam14").model == "fam14"
    assert gateway(model="mgw_eth", esp_protocol="esp3").model == "mgw_eth"
    with pytest.raises(ValidationError) as err:
        gateway(model="usb300", esp_protocol="esp3")
    assert set(err.value.errors) == {"model"}
    with pytest.raises(ValidationError) as err:
        gateway(model="mgw_eth")  # ESP3, the gateway ESP2
    assert err.value.errors["model"] == "mgw_eth speaks ESP3, not this protocol"
    # saved before there was the field: the model of the template, when the protocol fits
    assert gateway(template="fgw14_usb").model == "fgw14_usb"
    assert gateway(template="usb300", esp_protocol="esp3").model == "esp3"
    assert gateway(template="mgw_eth", esp_protocol="esp2").model == ""
    assert gateway(template="enocean").model == ""
    assert gateway(template="fam_usb", model="").model == ""  # saved without one on purpose


def test_discovery_gateways_carry_the_model() -> None:
    from device_proxy.enocean_ha import discovery_config

    fam = Connection("FAM", "/dev/ttyUSB0", 9100, kind="enocean", model="fam_usb")
    mgw = Connection("PioTek MGW-ETH", "", 9101, kind="enocean", esp_protocol="esp3")
    assert discovery_config("h", 9199, [fam, mgw])["gateways"] == [
        {"name": "FAM", "port": 9100, "protocol": "esp2", "model": "fam_usb"},
        {"name": "PioTek MGW-ETH", "port": 9101, "protocol": "esp3"},
    ]


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
    proxy.ask_base_id = False  # the gateway counts every byte it gets
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
    assert proxy.base_id == "FF-AB-CD-80"
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
    assert setup.events[-1][0] == "client_refused_network"
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


async def test_blocked_host_is_refused_and_dropped(setup: Setup) -> None:
    proxy = setup.proxy
    _reader, connected = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    assert proxy.disconnect_host("192.0.2.7") == 0  # another host stays
    assert proxy.disconnect_host("127.0.0.1") == 1
    await _until(lambda: not proxy.clients)
    connected.close()

    proxy.refuse = lambda host, _name: host == "127.0.0.1"
    reader, writer = await _connect(proxy)
    assert await reader.read() == b""
    assert not proxy.clients
    assert setup.events[-1][0] == "client_refused_blocked"
    writer.close()

    proxy.refuse = lambda _host, _name: False
    proxy.only = "192.0.2.7"  # maintenance: only this host
    reader, writer = await _connect(proxy)
    assert await reader.read() == b""
    assert setup.events[-1][0] == "client_refused_exclusive"
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


# what the EnOcean Eltako integration gets (enocean_ha.py)


async def test_replay_buffer_kept_over_a_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(enocean, "REPLAY_DIR", tmp_path)
    c = Connection("FAM", "/dev/null", 9100, id="0000000d", kind="enocean", link="serial")
    first = EnOceanProxy(replace(c, replay_persist=True), "all", lambda *a, **k: None, print)
    first._replay.append((first._clock(), time.time() - 30, FRAME_A))
    first._replay.append((first._clock(), time.time() - 5000, FRAME_B))  # too old by then
    first._save_replay()
    second = EnOceanProxy(replace(c, replay_persist=True), "all", lambda *a, **k: None, print)
    assert [frame for _r, _w, frame in second._replay] == [FRAME_A]
    assert not (tmp_path / "0000000d.json").exists()  # read once
    second._save_replay()
    plain = EnOceanProxy(c, "all", lambda *a, **k: None, print)  # off: nothing read, file goes
    assert not plain._replay
    plain._save_replay()
    assert not (tmp_path / "0000000d.json").exists()


async def test_status_and_discovery_for_the_integration(
    setup: Setup,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from device_proxy import enocean_ha
    from device_proxy.controller import Controller
    from device_proxy.db import Database
    from device_proxy.events import EventLog
    from device_proxy.model import AppConfig
    from device_proxy.store import Store
    from device_proxy.trace import TraceHub

    gateway, proxy = setup.gateway, setup.proxy
    db = Database(tmp_path / "h.db")
    controller = Controller(
        Store(db, tmp_path / "c.json"),
        EventLog(db),
        tmp_path / "s.yaml",
        trace=TraceHub(tmp_path / "t", tmp_path / "shm"),
    )
    c = replace(proxy.c, id="0000000e", port=proxy.port)
    controller.config = AppConfig(
        replace(AppConfig().settings, enocean_status_port=0), (c,)
    )  # 0: a free port, for the test
    controller.proxies[c.id] = proxy
    calls: list[tuple[str, Any, str]] = []

    def supervisor(path: str, payload: Any = None, method: str = "") -> Any:
        calls.append((path, payload, method))
        if path == "/addons/self/info":
            return {"data": {"hostname": "abc-device-proxy"}}
        return {"data": {"uuid": "u1"}}

    monkeypatch.setattr(enocean_ha, "_supervisor", supervisor)
    monkeypatch.setenv("SUPERVISOR_TOKEN", "t")
    monkeypatch.setenv("APP_VERSION", "0.2.0")
    ha = controller.enocean_ha
    await ha.update()
    assert calls[-1] == (
        "/discovery",
        {
            "service": "enocean_eltako",
            "config": {
                "app": "device_proxy",
                "host": "abc-device-proxy",
                "status_port": 0,
                "replay": True,
                "gateways": [{"name": "FAM", "port": proxy.port, "protocol": "esp2"}],
            },
        },
        "",
    )
    await ha.update()  # nothing changed: not sent again
    assert len(calls) == 2

    reader, writer = await _connect(proxy, replay=True)
    await _until(lambda: len(proxy.clients) == 1)
    gateway.send(FRAME_A)
    await reader.readexactly(14)
    assert ha.port
    r, w = await asyncio.open_connection("127.0.0.1", ha.port)
    w.write(b"GET /api/status HTTP/1.1\r\nHost: x\r\n\r\n")
    head, _, body = (await r.read()).partition(b"\r\n\r\n")
    assert head.startswith(b"HTTP/1.1 200")
    status = json.loads(body)
    assert (status["app"], status["api"], status["version"]) == ("device_proxy", 1, "0.2.0")
    (gw,) = status["gateways"]
    # what the integration's proxy_status.summarize() reads
    assert gw["port"] == proxy.port and gw["name"] == "FAM" and gw["connected"] is True
    assert gw["clients"] == [{"peer": "127.0.0.1", "replay": True}]
    assert gw["duty_cycle"]["of_limit"] == 0.0 and gw["duty_cycle"]["telegrams"] == 0
    assert gw["stats"]["replayed"] == 0 and gw["exclusive_peer"] is None
    r, w = await asyncio.open_connection("127.0.0.1", ha.port)
    w.write(b"POST /api/send HTTP/1.1\r\n\r\n")
    assert (await r.read()).startswith(b"HTTP/1.1 404")  # read only
    writer.close()

    monkeypatch.setattr(enocean_ha, "STATUS_PEERS", "192.0.2.0/24")
    r, w = await asyncio.open_connection("127.0.0.1", ha.port)
    monkeypatch.setattr(enocean_ha, "peer_allowed", lambda *args: False)  # not this host either
    w.write(b"GET /api/status HTTP/1.1\r\nHost: 194d6409-device-proxy:9199\r\n\r\n")
    with caplog.at_level(logging.WARNING, logger="device_proxy.enocean_ha"):
        # not Home Assistant or an app: refused with a reason, not reset, and logged
        head, _, body = (await r.read()).partition(b"\r\n\r\n")
    assert head.startswith(b"HTTP/1.1 403")
    assert body.startswith(b"forbidden: 127.0.0.1 is not in 192.0.2.0/24")
    assert "127.0.0.1" in caplog.text and "refused" in caplog.text
    assert "Host 194d6409-device-proxy:9199" in caplog.text and "GET /api/status" in caplog.text

    controller.config = AppConfig(controller.config.settings, (replace(c, enabled=False),))
    await ha.update()  # no gateway left: discovery withdrawn, status closed
    assert calls[-1] == ("/discovery/u1", None, "DELETE") and ha.port is None
    controller.proxies.clear()


def test_status_port_and_the_health_check(tmp_path: Path) -> None:
    from device_proxy import health
    from device_proxy.model import AppConfig

    gateway = Connection("FAM", "/dev/ttyUSB0", 9199, kind="enocean", link="serial")
    with pytest.raises(ValidationError) as err:
        AppConfig(connections=(gateway,)).validate()
    assert "status for the EnOcean integration" in err.value.errors["connections.0.port"]
    AppConfig(connections=(replace(gateway, kind="serial"),)).validate()  # only with EnOcean

    state = tmp_path / "health.json"
    assert health.proxies_ok(state)  # not written yet: just started
    health.write([], state)
    assert health.proxies_ok(state)
    health.write(["FAM"], state)  # a gateway does not listen
    assert not health.proxies_ok(state)
    state.write_text(json.dumps({"time": time.time() - 600, "not_listening": []}))
    assert not health.proxies_ok(state)  # the app no longer writes it: it hangs


# tools: send, test, capture (enocean_tools.py, web routes)


async def test_tools_over_the_web_interface(setup: Setup, tmp_path: Path) -> None:
    from device_proxy.controller import Controller
    from device_proxy.db import Database
    from device_proxy.events import EventLog
    from device_proxy.model import AppConfig
    from device_proxy.store import Store
    from device_proxy.trace import TraceHub
    from device_proxy.web import WebServer
    from tests.test_web import request

    gateway, proxy = setup.gateway, setup.proxy
    db = Database(tmp_path / "h.db")
    controller = Controller(
        Store(db, tmp_path / "c.json"),
        EventLog(db),
        tmp_path / "s.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )
    c = replace(proxy.c, id="00000011", port=proxy.port)
    controller.config = AppConfig(connections=(c,))
    controller.proxies[c.id] = proxy
    web = WebServer(controller, port=0, hosts=("127.0.0.1",), peers=None)
    await web.start()
    assert web._server is not None
    port = web._server.sockets[0].getsockname()[1]

    async def answer_base_id() -> None:
        while True:
            await asyncio.sleep(0.01)
            while BASE_ID_READ in gateway.received:
                index = gateway.received.index(BASE_ID_READ)
                del gateway.received[index : index + 14]
                gateway.send(BASE_ID_ANSWER)

    task = asyncio.create_task(answer_base_id())
    base = f"api/tools/{c.id}/enocean"
    status, sent = await request(port, "POST", f"{base}/send", {"hex": BASE_ID_READ.hex(":")})
    assert status == 200 and sent == {
        "sent": BASE_ID_READ.hex(" ").upper(),
        "answer": BASE_ID_ANSWER.hex(" ").upper(),
    }
    status, error = await request(port, "POST", f"{base}/send", {"hex": "A5 5A 00"})
    assert status == 409 and "ESP2" in error["error"]  # type: ignore[index]
    bad_sum = BASE_ID_READ[:-1] + b"\x00"
    status, error = await request(port, "POST", f"{base}/send", {"hex": bad_sum.hex()})
    assert status == 409 and "checksum should be 03" in error["error"]  # type: ignore[index]
    status, error = await request(port, "POST", f"{base}/send", {"hex": "xyz"})
    assert status == 409 and "hex" in error["error"]  # type: ignore[index]
    status, result = await request(port, "POST", f"{base}/test", {"count": 2})
    assert status == 200 and result["answered"] == 2  # type: ignore[index]
    status, _ = await request(port, "POST", f"{base}/test", {"count": 500})
    assert status == 409

    # a capture reserved for one program; the app's tools wait meanwhile
    status, capture = await request(
        port, "POST", f"{base}/capture", {"exclusive_peer": "192.0.2.9"}
    )
    assert status == 200 and capture["exclusive_peer"] == "192.0.2.9"  # type: ignore[index]
    assert proxy.exclusive_peer == "192.0.2.9"
    status, error = await request(port, "POST", f"{base}/send", {"hex": BASE_ID_READ.hex()})
    assert status == 409 and "reserved" in error["error"]  # type: ignore[index]
    status, other = await request(port, "POST", f"{base}/capture", {})
    assert status == 409  # one at a time
    assert controller.problems() == {}
    gateway.send(FRAME_A)
    await _until(
        lambda: controller.captures.current is not None and controller.captures.current.frames >= 1
    )
    assert controller.snapshot()["capture"]["file"] == capture["file"]  # type: ignore[index]
    status, _ = await request(port, "DELETE", f"api/trace/{capture['file']}")  # type: ignore[index]
    assert status == 409  # it is being written: not lost while it runs
    status, stopped = await request(port, "POST", "api/capture/stop", {})
    assert stopped["frames"] >= 1 and proxy.exclusive_peer is None  # type: ignore[index]
    lines = (tmp_path / "trace" / capture["file"]).read_text().splitlines()  # type: ignore[index]
    first = json.loads(lines[0])
    assert (first["gateway"], first["dir"], first["kind"], first["hex"]) == (
        "FAM",
        "rx",
        "radio",
        FRAME_A.hex(),
    )
    names = [f["name"] for f in controller.trace.files()]
    listed = {f["name"]: f["connection"] for f in controller.snapshot()["trace_files"]}  # type: ignore[union-attr]
    assert listed[capture["file"]] == c.id  # type: ignore[index]  # its connection
    assert capture["file"] in names  # type: ignore[index]
    status, body = await request(port, "GET", f"api/trace/{capture['file']}")  # type: ignore[index]
    assert status == 200
    status, _ = await request(port, "DELETE", f"api/trace/{capture['file']}")  # type: ignore[index]
    assert status == 200 and not controller.trace.files()
    kinds = [e.kind for e in controller.events.live]
    assert "capture_locked" in kinds and "capture_stopped" in kinds

    task.cancel()
    await web.stop()
    controller.proxies.clear()


def test_air_time_notification(tmp_path: Path) -> None:
    from device_proxy.controller import Controller
    from device_proxy.db import Database
    from device_proxy.events import EventLog
    from device_proxy.model import AppConfig
    from device_proxy.store import Store
    from device_proxy.trace import TraceHub

    db = Database(tmp_path / "h.db")
    controller = Controller(
        Store(db, tmp_path / "c.json"),
        EventLog(db),
        tmp_path / "s.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )
    c = Connection("FAM", "", 9100, id="00000012", kind="enocean", link="tcp", host="h")
    controller.config = AppConfig(connections=(c,))
    proxy = EnOceanProxy(c, "all", lambda *a, **k: None, lambda chunk: None)
    proxy.listening = True
    proxy.clients["x"] = None  # type: ignore[assignment]  # a client: no "no client" note
    controller.proxies[c.id] = proxy
    proxy._airtime.append((time.time(), 0.85 * 36000))  # 85 % of the 1 % of an hour
    (key,) = controller.problems()
    assert key == "device_proxy_00000012_duty"
    assert esp.describe("esp2", BASE_ID_READ) == "command"


async def test_the_base_id_is_read_once_after_connecting() -> None:
    class Answering(FakeGateway):
        async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            self.writers.append(writer)
            while data := await reader.read(1024):
                self.received += data
                if BASE_ID_READ in data:
                    writer.write(BASE_ID_ANSWER)

    gateway = await Answering().start()
    c = Connection(
        "FAM", "", 0, kind="enocean", link="tcp", host="127.0.0.1", host_port=gateway.port
    )
    proxy = EnOceanProxy(c, "all", lambda *a, **k: None, lambda chunk: None)
    task = asyncio.create_task(proxy.run())
    try:
        await _until(lambda: proxy.base_id is not None)
        assert gateway.received.count(BASE_ID_READ) == 1
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await gateway.stop()


async def test_a_stop_does_not_wait_for_a_client_that_does_not_read() -> None:
    gateway = await FakeGateway().start()
    c = Connection(
        "FAM", "", 0, kind="enocean", link="tcp", host="127.0.0.1", host_port=gateway.port
    )
    proxy = EnOceanProxy(c, "all", lambda *a, **k: None, lambda chunk: None)
    proxy.ask_base_id = False
    task = asyncio.create_task(proxy.run())
    await _until(lambda: proxy.listening and proxy.link.is_open)
    _reader, writer = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    client = next(iter(proxy.clients.values()))
    assert client.writer is not None
    client.writer.transport.pause_reading()
    client.writer.transport.set_write_buffer_limits(high=1 << 30)
    for _ in range(20000):  # more than the socket takes: some stays queued
        proxy._send(client, FRAME_A)
    task.cancel()
    await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), 3)
    writer.close()
    await gateway.stop()


async def test_a_failing_observer_does_not_stop_the_gateway(setup: Setup) -> None:
    gateway, proxy = setup.gateway, setup.proxy

    def full_disk(direction: str, frame: bytes, address: str) -> None:
        raise OSError(28, "No space left on device")

    proxy.observers.append(full_disk)
    reader, writer = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    gateway.send(FRAME_A)
    gateway.send(FRAME_B)
    assert await reader.readexactly(28) == FRAME_A + FRAME_B
    assert proxy.observers == [] and proxy.link.is_open
    writer.close()


async def test_a_taken_status_port_is_tried_again() -> None:
    from types import SimpleNamespace

    from device_proxy.enocean_ha import EnOceanHa

    blocker = await asyncio.start_server(lambda r, w: None, None, 0)
    port = blocker.sockets[0].getsockname()[1]
    events: list[str] = []
    log = SimpleNamespace(emit=lambda level, kind, **p: events.append(kind))
    fake = SimpleNamespace(events=log)
    ha = EnOceanHa(fake)  # type: ignore[arg-type]
    await ha._serve(port)
    assert ha._server is None and events == ["listen_failed"]
    state = ha.state()  # the panel says why the integration gets no status
    assert state["port"] == port and state["listening"] is False and state["error"]
    blocker.close()
    await blocker.wait_closed()
    await ha.retry()  # too early
    assert ha._server is None
    ha._failed_at = float("-inf")  # long ago, also on a machine that has only just started
    await ha.retry()
    assert ha._server is not None and ha.port == port and events == ["listen_failed"]
    assert ha.state() == {"port": port, "listening": True, "error": None}
    await ha.stop()


def test_senders_with_signal_and_repeaters() -> None:
    from device_proxy import esp

    # ESP3 RADIO_ERP1: RPS from FE-E9-12-34, status 0x31 (1 repeater), optional data at -74 dBm
    frame = esp3(bytes.fromhex("F630FEE9123431"), bytes.fromhex("03FFFFFFFF4A00"))
    assert esp.radio_info("esp3", frame) == ("RPS", "FE-E9-12-34")
    assert esp.signal("esp3", frame) == (-74, 1)
    assert esp.signal("esp2", FRAME_A) == (None, 0)

    c = Connection("USB", "", 0, kind="enocean", link="tcp", host="127.0.0.1", esp_protocol="esp3")
    proxy = EnOceanProxy(c, "all", lambda *a, **k: None, lambda chunk: None)
    proxy.started -= 3600  # a sender first heard an hour after the start is new
    proxy._heard_frame(frame, "main")
    proxy._heard_frame(frame, "fallback")
    (row,) = proxy.senders_list()
    assert (row["id"], row["rorg"], row["count"], row["dbm"], row["hops"]) == (
        "FE-E9-12-34",
        "RPS",
        2,
        -74,
        1,
    )
    assert row["heard"] == ["fallback", "main"] and row["new"] and not row["own"]


def test_a_test_case_hides_sender_and_base_ids() -> None:
    from device_proxy import esp, testcase
    from device_proxy.trace import Chunk

    frame = esp3(bytes.fromhex("F630FEE9123431"), bytes.fromhex("03FFFFFFFF4A00"))
    own = esp3(bytes.fromhex("F630FFABCD8130"))  # from the gateway's own range
    (anon, anon_own) = testcase.anonymise("esp3", [frame, own], "FF-AB-CD-80")
    assert esp.radio_info("esp3", anon) == ("RPS", "A0-00-00-01")
    assert esp.radio_info("esp3", anon_own) == ("RPS", "FF-AA-00-01")  # offset kept
    assert anon == esp3(bytes.fromhex("F630A000000131"), bytes.fromhex("03FFFFFFFF4A00"))

    c = Connection("USB", "", 0, kind="enocean", link="tcp", host="127.0.0.1")
    case = testcase.build(
        c,
        [Chunk(10.0, "rx", FRAME_A), Chunk(10.5, "open", text="x")],
        base_id=None,
        anonymised=True,
    )
    ((t, direction, raw),) = testcase.frames_of(case)
    assert (t, direction) == (0.0, "rx") and b"\x00\x21\x63\x43" not in raw
    assert raw[13] == sum(raw[2:13]) & 0xFF  # ESP2 checksum computed again


async def test_garbage_from_clients_reaches_the_gateway_as_whole_frames_only(
    setup: Setup,
) -> None:
    import random

    gateway, proxy = setup.gateway, setup.proxy
    rng = random.Random(9)

    async def garbage() -> None:
        reader, writer = await _connect(proxy, replay=rng.random() < 0.3)
        try:
            for _ in range(rng.randint(1, 8)):
                part = rng.choice(
                    [
                        rng.randbytes(rng.randint(0, 200)),
                        b"EOPX" + rng.randbytes(rng.randint(0, 80)),
                        b"EOPX REPLAY" + rng.choice([b"", b"\n", b" TS\n", b" X\n"]),
                        COMMAND,
                        COMMAND[: rng.randint(1, 13)],
                        b"\xa5\x5a" + rng.randbytes(12),
                    ]
                )
                writer.write(part)
                await writer.drain()
                if rng.random() < 0.3:
                    gateway.send(FRAME_A)
                await asyncio.sleep(rng.random() * 0.005)
        except OSError:
            pass
        finally:
            writer.transport.abort()

    for _ in range(8):
        await asyncio.gather(*(garbage() for _ in range(8)))
    await asyncio.sleep(0.2)  # what is queued reaches the gateway
    splitter = Splitter("esp2")
    frames = splitter.feed(bytes(gateway.received))
    assert frames and b"".join(frames) == bytes(gateway.received)  # nothing torn or mixed
    reader, writer = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    gateway.send(FRAME_B)
    async with asyncio.timeout(2):
        assert await reader.readexactly(len(FRAME_B)) == FRAME_B
    writer.close()


async def test_status_server_logs_a_failure_and_answers(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A status that fails is logged with the peer and answered with 500, not a reset."""
    from device_proxy import enocean_ha

    def broken(controller: Any) -> dict[str, Any]:
        raise KeyError("gateway")

    monkeypatch.setattr(enocean_ha, "status", broken)
    ha = enocean_ha.EnOceanHa.__new__(enocean_ha.EnOceanHa)
    ha.c = None  # type: ignore[assignment]
    server = await asyncio.start_server(ha._handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    with caplog.at_level(logging.WARNING, logger="device_proxy.enocean_ha"):
        r, w = await asyncio.open_connection("127.0.0.1", port)
        w.write(b"GET /api/status HTTP/1.1\r\nHost: 194d6409-device-proxy:9199\r\n\r\n")
        assert (await r.read()).startswith(b"HTTP/1.1 500")
        w.close()
        r, w = await asyncio.open_connection("127.0.0.1", port)
        w.write(b"GET /api/status HTTP/1.1\r\n")  # and away before the request ends
        w.close()
        for _ in range(100):
            if "closed after" in caplog.text:
                break
            await asyncio.sleep(0.01)
    server.close()
    await server.wait_closed()
    assert "the status for 127.0.0.1:" in caplog.text and "KeyError" in caplog.text
    assert "closed after 26 bytes" in caplog.text


async def test_a_second_capture_in_the_same_second_gets_its_own_file(
    setup: Setup, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from device_proxy.enocean_tools import Captures

    monkeypatch.setattr(time, "strftime", lambda fmt, *args: "20261107-120000")
    captures = Captures(tmp_path)
    first = captures.start(setup.proxy, None)
    first.file.write("kept\n")
    captures.stop()
    second = captures.start(setup.proxy, None)
    captures.stop()
    assert first.path != second.path and second.path.name.endswith("-2.jsonl")
    assert first.path.read_text() == "kept\n"


async def test_one_answered_command_at_a_time_and_late_answers_stay_with_their_command(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    monkeypatch.setattr(enocean, "LATE_GRACE", 0.1)
    (r1, w1), (r2, w2) = await _connect(proxy), await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 2)
    w1.write(BASE_ID_READ)
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ)
    w2.write(BASE_ID_READ)
    await asyncio.sleep(0.1)
    assert bytes(gateway.received) == BASE_ID_READ  # the second waits for the first's answer
    gateway.send(BASE_ID_ANSWER)
    assert await r1.readexactly(14) == BASE_ID_ANSWER
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ * 2)  # now its turn
    gateway.send(BASE_ID_ANSWER)
    assert await r2.readexactly(14) == BASE_ID_ANSWER

    # the asker is gone before the answer comes: the answer is its, not the next one's
    gateway.received.clear()
    w1.write(BASE_ID_READ)
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ)
    w1.close()
    await _until(lambda: len(proxy.clients) == 1)
    w2.write(BASE_ID_READ)
    gateway.send(BASE_ID_ANSWER)  # the answer to the first read
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ * 2)
    gateway.send(BASE_ID_ANSWER)
    assert await r2.readexactly(14) == BASE_ID_ANSWER
    await asyncio.sleep(0.1)
    assert not r2._buffer  # type: ignore[attr-defined]  # only its own answer, not both
    w2.close()


async def test_the_apps_request_waits_for_its_answer_from_the_sending_on(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    monkeypatch.setattr(enocean, "LATE_GRACE", 0.0)
    _r, w = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    next(iter(proxy.clients.values())).answer_within = 0.3
    w.write(BASE_ID_READ)  # never answered: holds the gateway for 0.3 s
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ)
    asked = asyncio.create_task(proxy.request(BASE_ID_READ, timeout=0.2))
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ * 2, timeout=1)
    await asyncio.sleep(0.1)  # 0.4 s after asking, 0.1 s after sending
    gateway.send(BASE_ID_ANSWER)
    assert await asked == BASE_ID_ANSWER
    w.close()

    proxy.exclusive_peer = "192.0.2.1"  # reserved: the request comes back at once
    async with asyncio.timeout(0.5):
        assert await proxy.request(BASE_ID_READ) is None
    proxy.exclusive_peer = None


async def test_an_answer_after_its_command_gave_up_goes_to_nobody(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A client that has just sent its own command would take it for its answer."""
    gateway, proxy = setup.gateway, setup.proxy
    monkeypatch.setattr(enocean, "LATE_GRACE", 0.0)
    (r1, w1), (r2, w2) = await _connect(proxy), await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 2)
    for client in proxy.clients.values():
        client.answer_within = 0.1
    w1.write(BASE_ID_READ)
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ)
    await asyncio.sleep(0.2)  # the read gives up
    w2.write(COMMAND)  # radio: no answer expected, goes out at once
    await _until(lambda: COMMAND in gateway.received)
    gateway.send(BASE_ID_ANSWER)  # the late answer to the read
    gateway.send(FRAME_A)  # then a telegram: proves the answer would have come first
    assert await asyncio.wait_for(r1.readexactly(14), 2) == FRAME_A
    assert await asyncio.wait_for(r2.readexactly(14), 2) == FRAME_A
    assert proxy.stats.late == 1

    monkeypatch.setattr(enocean, "LATE_WINDOW", 0.0)  # long after: the gateway's own words
    gateway.send(BASE_ID_ANSWER)
    assert await asyncio.wait_for(r1.readexactly(14), 2) == BASE_ID_ANSWER
    w1.close()
    w2.close()


def test_a_repeated_esp3_telegram_is_the_same_for_the_duplicate_check() -> None:
    direct = esp3(bytes.fromhex("F6500021634330"), bytes.fromhex("01FFFFFFFF4400"))
    repeated = esp3(bytes.fromhex("F6500021634331"), bytes.fromhex("01FFFFFFFF5000"))
    other = esp3(bytes.fromhex("F6700021634330"))
    assert esp.radio_key("esp3", direct) == esp.radio_key("esp3", repeated)
    assert esp.radio_key("esp3", direct) != esp.radio_key("esp3", other)


def test_an_esp2_false_start_does_not_cost_the_next_frame() -> None:
    """After noise, "A5 5A" in the junk is not a frame (its checksum is wrong): the real
    frames behind it all come out, and the junk does not."""
    splitter = Splitter("esp2")
    assert splitter.feed(b"\x00\xa5\x5a\x01\x02" + FRAME_A + FRAME_A) == [FRAME_A, FRAME_A]


async def test_a_request_that_gave_up_waiting_for_its_turn_is_not_sent_later(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E.g. a base ID write that reported "no answer" must not use a flash write after all."""
    gateway, proxy = setup.gateway, setup.proxy
    monkeypatch.setattr(enocean, "LATE_GRACE", 0.0)
    monkeypatch.setattr(enocean, "QUEUE_TIMEOUT", 0.1)
    _r, w = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    next(iter(proxy.clients.values())).answer_within = 0.4
    w.write(BASE_ID_READ)  # never answered: holds the gateway for 0.4 s
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ)
    assert await proxy.request(BASE_ID_READ) is None  # gives up after 0.1 s
    await asyncio.sleep(0.6)
    assert bytes(gateway.received) == BASE_ID_READ  # only the client's
    w.close()


async def test_a_frame_that_could_not_be_written_does_not_hold_the_next(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    gateway, proxy = setup.gateway, setup.proxy
    _r, w = await _connect(proxy)
    await _until(lambda: len(proxy.clients) == 1)
    next(iter(proxy.clients.values())).answer_within = 5.0
    write, failed = proxy.link.write, []

    async def once_broken(frame: bytes) -> None:
        if not failed:
            failed.append(frame)
            raise OSError("write failed")
        await write(frame)

    monkeypatch.setattr(proxy.link, "write", once_broken)
    w.write(BASE_ID_READ + BASE_ID_READ)
    await _until(lambda: bytes(gateway.received) == BASE_ID_READ, timeout=1)  # not after 5 s
    assert failed and proxy.stats.dropped == 1
    w.close()


def test_sender_names_are_checked() -> None:
    from device_proxy.model import Settings, ValidationError, parse_sender_names

    assert parse_sender_names("fe-e9-12-34  Kitchen   switch\n\nFF-00-00-01 B") == {
        "FE-E9-12-34": "Kitchen switch",
        "FF-00-00-01": "B",
    }
    for wrong in ("FE-E9-12 Name", "FE-E9-12-34", f"FE-E9-12-34 {'x' * 41}", "name FE-E9-12-34"):
        with pytest.raises(ValueError):
            parse_sender_names(wrong)
    with pytest.raises(ValidationError) as err:
        Settings.from_dict({"sender_names": "kaputt"})
    assert "sender_names" in err.value.errors


def test_the_senders_as_a_file() -> None:
    import csv
    import io

    from device_proxy.enocean_tools import senders_csv

    row = {
        "id": "FE-E9-12-34",
        "name": "Küche",
        "rorg": "RPS",
        "count": 2,
        "last": 1700000000.0,
        "dbm": None,
        "hops": 1,
        "own": False,
        "new": True,
    }
    data = senders_csv([row, {**row, "name": "=1+1", "dbm": -74}])
    assert data.startswith(b"\xef\xbb\xbf")  # for the umlauts in a spreadsheet
    head, first, second = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    assert head[:3] == ["id", "name", "kind"]
    assert first[:4] == ["FE-E9-12-34", "Küche", "RPS", "2"] and first[5:] == ["", "1", "0", "1"]
    assert second[1] == "'=1+1" and second[5] == "-74"  # a name cannot be a formula


async def test_a_capture_at_its_limit_tells_that_it_ended(
    setup: Setup, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from device_proxy import enocean_tools

    monkeypatch.setattr(enocean_tools, "MAX_BYTES", 1)
    captures = enocean_tools.Captures(tmp_path)
    ended: list[enocean_tools.Capture] = []
    captures.on_full = ended.append
    capture = captures.start(setup.proxy, None)
    captures._write("rx", b"\x55\x00\x01\x00\x05\x70\x08\x38", "")
    assert captures.current is None and ended == [capture]
