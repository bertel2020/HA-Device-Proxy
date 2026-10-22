"""A second EnOcean gateway with the same base ID that takes over when the first one fails."""

from dataclasses import replace
from typing import Any

import pytest

from device_proxy.enocean import restart_key
from device_proxy.enocean_ha import gateways
from device_proxy.importer import ImportItem, ImportResult, merge
from device_proxy.model import AppConfig, Connection, ValidationError


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
