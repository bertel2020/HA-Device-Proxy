"""A second EnOcean gateway with the same base ID that takes over when the first one fails."""

import asyncio
import contextlib
import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from device_proxy import enocean, health
from device_proxy.controller import Controller
from device_proxy.db import Database
from device_proxy.enocean import EnOceanProxy, restart_key
from device_proxy.enocean_ha import gateway_status, gateways
from device_proxy.events import EventLog
from device_proxy.importer import ImportItem, ImportResult, merge
from device_proxy.model import AppConfig, Connection, ValidationError
from device_proxy.store import Store
from device_proxy.trace import TraceHub


def gateway(name: str, port: int, cid: str, **values: Any) -> Connection:
    return Connection(
        name, "", port, id=cid, kind="enocean", link="tcp", host=f"{name.lower()}.local", **values
    )


A = gateway("A", 9100, "0000000a", fallback="0000000b")
B = gateway("B", 9101, "0000000b")
C = gateway("C", 9102, "0000000c")


def errors(*connections: Connection) -> dict[str, str]:
    with pytest.raises(ValidationError) as err:
        AppConfig(connections=connections).validate()
    return err.value.errors


def test_a_fallback_is_another_enocean_gateway_with_the_same_protocol() -> None:
    config = AppConfig(connections=(A, B, C))
    config.validate()
    assert config.fallback_of(B.id) == A and config.fallback_of(A.id) is None
    serial = Connection("S", "/dev/ttyUSB0", 3333, id="0000000d")
    assert "connections.0.fallback" in errors(replace(A, fallback=serial.id), B, serial)
    esp3 = replace(B, esp_protocol="esp3")
    assert "ESP3" in errors(A, esp3)["connections.0.fallback"]
    with pytest.raises(ValidationError) as err:
        replace(A, fallback=A.id).validate()
    assert err.value.errors == {"fallback": "not the connection itself"}
    with pytest.raises(ValidationError) as err:
        replace(A, fallback="x", fallback_trigger="never", fallback_return="later").validate()
    assert set(err.value.errors) == {"fallback", "fallback_trigger", "fallback_return"}


def test_no_chains_no_rings_and_one_gateway_per_fallback() -> None:
    chain = errors(A, replace(B, fallback=C.id), C)
    assert "has a fallback of its own" in chain["connections.0.fallback"]
    assert "itself the fallback" in chain["connections.1.fallback"]
    ring = errors(A, replace(B, fallback=A.id))
    assert set(ring) == {"connections.0.fallback", "connections.1.fallback"}
    twice = errors(A, B, replace(C, fallback=B.id))
    assert twice == {"connections.2.fallback": "B is the fallback of A already"}


def test_a_deleted_or_missing_fallback_leaves_the_gateway_without() -> None:
    config = AppConfig(connections=(A, B, C))
    assert config.without_connection(B.id).connection(A.id).fallback == ""  # type: ignore[union-attr]
    loaded = AppConfig.from_dict({"connections": [A.to_dict(), C.to_dict()]})
    assert loaded.connection(A.id).fallback == ""  # type: ignore[union-attr]
    kept = AppConfig.from_dict(config.to_dict())
    assert kept.connection(A.id).fallback == B.id  # type: ignore[union-attr]
    # an import that replaces B keeps its id: A keeps its fallback
    item = ImportItem("b", replace(B, id="0000000f", name="B new"))
    result = ImportResult(1, [item])
    imported = merge(config, result, replace_all=False, take={"b"}, on_conflict={"b": "replace"})
    assert imported.connection(A.id).fallback == B.id  # type: ignore[union-attr]
    assert imported.connection(B.id).name == "B new"  # type: ignore[union-attr]


def test_the_fallback_is_not_offered_to_the_integration() -> None:
    config = AppConfig(connections=(A, B, C))
    assert [c.name for c in gateways(config)] == ["A", "C"]
    deselected = config.with_connection(replace(A, fallback=""))
    assert [c.name for c in gateways(deselected)] == ["A", "B", "C"]


def test_changing_the_fallback_does_not_restart_the_gateway() -> None:
    other = replace(A, fallback=C.id, fallback_return="manual", fallback_listen=True)
    assert restart_key(A, "all") == restart_key(other, "all")


# the proxies: A goes on through B


BASE_A = bytes.fromhex("A55A8B98FFB7448000000000000A")  # ESP2 base ID answer FF-B7-44-80
BASE_OTHER = bytes.fromhex("A55A8B98FFA1220000000000000A")  # FF-A1-22-00
BASE_ID_READ = bytes.fromhex("A55AAB5800000000000000000003")
FRAME = bytes.fromhex("A55A0B0570000000002163433000")  # RPS from 00-21-63-43
FRAME_REPEATED = bytes.fromhex("A55A0B0570000000002163433100")  # the same, status: repeated
OWN = bytes.fromhex("A55A0B0570000000FFB744813000")  # RPS from FF-B7-44-81: A's own range
COMMAND = bytes.fromhex("A55A6B0501000000FFB744813000")  # TRT RPS: sent over the air


class Gateway:
    """A fake ESP2 gateway over TCP that answers base ID reads (unless silent)."""

    def __init__(self, answer: bytes = BASE_A) -> None:
        self.answer = answer
        self.silent = False
        self.received = bytearray()
        self.writers: list[asyncio.StreamWriter] = []
        self.server: asyncio.Server | None = None
        self.port = 0

    async def start(self, port: int = 0) -> "Gateway":
        self.server = await asyncio.start_server(self._client, "127.0.0.1", port)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.writers.append(writer)
        with contextlib.suppress(ConnectionError):
            while data := await reader.read(1024):
                self.received += data
                if BASE_ID_READ in data and not self.silent:
                    writer.write(self.answer)

    def send(self, frame: bytes) -> None:
        for writer in self.writers:
            writer.write(frame)

    async def stop(self) -> None:
        assert self.server is not None
        self.server.close()
        for writer in self.writers:
            writer.close()
        await self.server.wait_closed()
        self.writers.clear()


async def _until(predicate: Callable[[], bool], timeout: float = 5.0) -> None:
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.01)


@dataclass
class Pair:
    gateway_a: Gateway
    gateway_b: Gateway
    a: EnOceanProxy
    b: EnOceanProxy
    events: list[tuple[str, dict[str, object]]]
    tasks: list[asyncio.Task[None]]

    async def client(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        result = await asyncio.open_connection("127.0.0.1", self.a.port)
        await _until(lambda: bool(self.a.clients))
        return result

    def kinds(self) -> list[str]:
        return [kind for kind, _ in self.events]


async def _pair(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, answer_b: bytes = BASE_A, **values: Any
) -> Pair:
    monkeypatch.setattr(enocean, "BASE_ID_FILE", tmp_path / "base_ids.json")
    monkeypatch.setattr(enocean, "SUPERVISE", 0.02)
    monkeypatch.setattr(enocean, "MAIN_PROBE", 0.05)
    monkeypatch.setattr(enocean, "FALLBACK_PROBE", 0.05)
    monkeypatch.setattr(enocean, "FALLBACK_STABLE", 0.3)
    monkeypatch.setattr(enocean, "PROBE_TIMEOUT", 0.1)
    gateway_a, gateway_b = await Gateway().start(), await Gateway(answer_b).start()
    events: list[tuple[str, dict[str, object]]] = []

    def on_event(level: str, kind: str, **params: object) -> None:
        events.append((kind, params))

    def proxy(gateway: Gateway, name: str, cid: str, **more: Any) -> EnOceanProxy:
        c = Connection(
            name, "", 0, id=cid, kind="enocean", link="tcp", host="127.0.0.1",
            host_port=gateway.port, max_clients=5, send_gap_ms=0, **more,
        )  # fmt: skip
        return EnOceanProxy(c, "all", on_event, lambda chunk: None)

    a = proxy(gateway_a, "A", "0000000a", fallback="0000000b", **values)
    b = proxy(gateway_b, "B", "0000000b")
    b.serves = "A"
    a.attach_fallback(b)
    tasks = [asyncio.create_task(a.run()), asyncio.create_task(b.run())]
    pair = Pair(gateway_a, gateway_b, a, b, events, tasks)
    await _until(lambda: a.listening and a.base_id is not None and b.base_id is not None)
    return pair


async def _end(pair: Pair) -> None:
    for task in pair.tasks:
        task.cancel()
    await asyncio.gather(*pair.tasks, return_exceptions=True)
    for gateway in (pair.gateway_a, pair.gateway_b):
        if gateway.server is not None and gateway.server.is_serving():
            await gateway.stop()


async def test_b_stands_in_when_a_is_gone_and_a_takes_over_again(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pair = await _pair(monkeypatch, tmp_path)
    try:
        assert not pair.b.listening and pair.b.serves == "A"  # no port of its own
        await _until(lambda: pair.a.fallback_ready)
        reader, writer = await pair.client()
        port = pair.gateway_a.port
        await pair.gateway_a.stop()  # A breaks
        await _until(lambda: pair.a.active == "fallback")
        assert (
            "enocean_failover",
            {"fallback": "B", "reason": "disconnected", "unanswered": 0},
        ) in [
            (k, {x: p[x] for x in ("fallback", "reason", "unanswered")})
            for k, p in pair.events
            if k == "enocean_failover"
        ]
        writer.write(COMMAND)  # A's client sends: it goes out through B
        await _until(lambda: COMMAND in pair.gateway_b.received)
        pair.gateway_b.send(FRAME)  # B hears a switch: A's client gets it
        assert await asyncio.wait_for(reader.readexactly(14), 2) == FRAME
        assert pair.a.stats.relayed == 1 and pair.a.stats.from_fallback >= 1
        assert pair.a.state()["fallback"]["active"] == "fallback"

        await pair.gateway_a.start(port)  # A is back: after steady running A takes over
        await _until(lambda: pair.a.active == "main")
        assert "enocean_failback" in pair.kinds()
        pair.gateway_a.received.clear()
        writer.write(COMMAND)
        await _until(lambda: COMMAND in pair.gateway_a.received)
        writer.close()
    finally:
        await _end(pair)


async def test_a_gateway_that_stops_answering_counts_as_failed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pair = await _pair(monkeypatch, tmp_path)
    try:
        await _until(lambda: pair.a.fallback_ready)
        pair.gateway_a.silent = True  # connected, but no answers
        await _until(lambda: pair.a.active == "fallback")
        assert pair.a.switch_reason == "no_answer"
    finally:
        await _end(pair)


async def test_only_a_lost_connection_counts_with_the_trigger_disconnect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pair = await _pair(monkeypatch, tmp_path, fallback_trigger="disconnect")
    try:
        await _until(lambda: pair.a.fallback_ready)
        pair.gateway_a.silent = True
        await asyncio.sleep(0.5)
        assert pair.a.active == "main"
    finally:
        await _end(pair)


async def test_a_fallback_with_another_base_id_does_not_stand_in(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pair = await _pair(monkeypatch, tmp_path, answer_b=BASE_OTHER)
    try:
        await _until(lambda: "enocean_fallback_unready" in pair.kinds())
        assert pair.a.fallback_state() == (False, "base_id_differs")
        await pair.gateway_a.stop()
        await asyncio.sleep(0.3)
        assert pair.a.active == "main"
        with pytest.raises(ValueError):
            pair.a.switch("fallback")
        # the base ID of A is kept: the check works while A is away, also after a restart
        assert json.loads((tmp_path / "base_ids.json").read_text())["0000000a"] == "FF-B7-44-80"
    finally:
        await _end(pair)


async def test_by_hand_and_back_only_by_hand(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pair = await _pair(monkeypatch, tmp_path)
    try:
        await _until(lambda: pair.a.fallback_ready)
        pair.a.switch("fallback")
        await asyncio.sleep(0.5)  # longer than FALLBACK_STABLE: no automatic return
        assert pair.a.active == "fallback" and pair.a.manual
        pair.a.switch("main")
        assert pair.a.active == "main" and not pair.a.manual
        with pytest.raises(ValueError):
            pair.a.switch("elsewhere")
    finally:
        await _end(pair)


async def test_listening_to_both_drops_duplicates_and_the_own_sending(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pair = await _pair(monkeypatch, tmp_path, fallback_listen=True)
    try:
        reader, writer = await pair.client()
        pair.gateway_a.send(FRAME)
        await _until(lambda: pair.a.heard["main"] == 1)
        pair.gateway_b.send(FRAME_REPEATED)  # the same telegram via B: a duplicate
        pair.gateway_b.send(OWN)  # B hears A's own sending: dropped
        await _until(lambda: pair.a.heard["own"] == 1 and pair.a.heard["duplicates"] == 1)
        other = bytes.fromhex("A55A0B0550000000002163433000")
        pair.gateway_b.send(other)  # only B heard this one
        assert await asyncio.wait_for(reader.readexactly(28), 2) == FRAME + other
        assert pair.a.heard == {"main": 1, "fallback": 1, "duplicates": 1, "own": 1}
        writer.close()
    finally:
        await _end(pair)


async def test_without_listening_the_resting_fallback_is_not_heard(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pair = await _pair(monkeypatch, tmp_path)
    try:
        reader, writer = await pair.client()
        pair.gateway_b.send(FRAME)
        pair.gateway_a.send(OWN)
        assert await asyncio.wait_for(reader.readexactly(14), 2) == OWN
        assert pair.b.state()["replay"]["kept"] == 0  # a fallback keeps no replay of its own
        writer.close()
    finally:
        await _end(pair)


def test_mqtt_entities_and_values_of_a_gateway_with_fallback() -> None:
    def entity(key: str, **config: Any) -> dict[str, Any]:
        return {"key": key, **config}

    topics = enocean.mqtt_entities("ha", A, entity)
    assert any(t.endswith("/fallback_active/config") for t in topics)
    assert not any("fallback" in t for t in enocean.mqtt_entities("ha", C, entity))
    state = {
        "reachable": False,
        "frames": {"from_gateway": 3},
        "duty_cycle": {"of_limit": 1.0},
        "fallback": {"active": "fallback", "name": "B", "main": "A", "ready": True},
    }
    values = enocean.mqtt_state(state)
    assert values["fallback_active"] and values["active_gateway"] == "B"


# in the controller


async def test_the_controller_wires_the_fallback_and_swaps_the_hardware(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(enocean, "BASE_ID_FILE", tmp_path / "base_ids.json")
    monkeypatch.setattr(enocean, "SUPERVISE", 0.02)
    monkeypatch.setattr(health, "HEALTH_FILE", tmp_path / "health.json")
    gateway_a, gateway_b = await Gateway().start(), await Gateway().start()
    a = replace(A, host="127.0.0.1", host_port=gateway_a.port, port=15031)
    b = replace(B, host="127.0.0.1", host_port=gateway_b.port, port=15032)
    db = Database(tmp_path / "h.db")
    store = Store(db, tmp_path / "c.json")
    config = AppConfig(connections=(a, b))
    store.save(AppConfig(), config, "test")
    controller = Controller(
        store, EventLog(db), tmp_path / "s.yaml", trace=TraceHub(tmp_path / "t", tmp_path / "shm")
    )
    controller.health_file = tmp_path / "health.json"
    controller.config = config
    try:
        await controller._reconcile_proxies()
        proxy_a, proxy_b = controller.proxies[a.id], controller.proxies[b.id]
        assert isinstance(proxy_a, EnOceanProxy) and isinstance(proxy_b, EnOceanProxy)
        assert proxy_b.serves == "A" and proxy_a.fallback is proxy_b
        await _until(lambda: proxy_a.fallback_ready)
        rows = {row["name"]: row for row in controller.snapshot()["connections"]}  # type: ignore[attr-defined]
        assert rows["B"]["running"] and rows["B"]["enocean"]["serves"] == "A"
        assert rows["A"]["enocean"]["fallback"]["name"] == "B"
        status = gateway_status(a, proxy_a)
        assert status["active"] == "main" and status["fallback"]["ready"]
        await controller._proxy_tick()
        assert json.loads((tmp_path / "health.json").read_text())["not_listening"] == []
        topics = controller.mqtt.configs()
        assert any(t.endswith(f"device_proxy_{a.id}/active_gateway/config") for t in topics)

        proxy_a.switch("fallback")
        problems = controller.problems()
        assert "läuft über Ersatz" in problems[f"device_proxy_{a.id}_fallback"][0]
        assert f"device_proxy_{a.id}_unreachable" not in problems

        # B's hardware becomes A's: A keeps its port, the old hardware is switched off
        await controller.enocean_promote(a.id, "off")
        new_a, new_b = controller.config.connection(a.id), controller.config.connection(b.id)
        assert new_a is not None and new_b is not None
        assert (new_a.host_port, new_a.port, new_a.fallback) == (gateway_b.port, 15031, b.id)
        assert (new_b.host_port, new_b.enabled) == (gateway_a.port, False)
        assert b.id not in controller.proxies
        assert "enocean_fallback_promoted" in [e.kind for e in controller.events.history()]
        with pytest.raises(ValueError):
            await controller.enocean_promote(a.id, "later")
        await controller.enocean_promote(a.id, "delete")
        assert controller.config.connection(b.id) is None
        assert controller.config.connection(a.id).fallback == ""  # type: ignore[union-attr]
        with pytest.raises(ValueError):
            await controller.enocean_promote(a.id, "off")
    finally:
        controller.config = AppConfig()
        await controller._reconcile_proxies()
        await gateway_a.stop()
        await gateway_b.stop()
