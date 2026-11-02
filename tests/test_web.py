import asyncio
import json
from pathlib import Path

import pytest

from device_proxy.controller import Controller
from device_proxy.db import Database
from device_proxy.events import EventLog
from device_proxy.store import Store
from device_proxy.trace import TraceHub
from device_proxy.web import WebServer


async def request(port: int, method: str, path: str, body: object = None) -> tuple[int, object]:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    data = b"" if body is None else json.dumps(body).encode()
    writer.write(
        f"{method} /{path} HTTP/1.1\r\nHost: x\r\nContent-Length: {len(data)}\r\n\r\n".encode()
        + data
    )
    await writer.drain()
    head = await reader.readuntil(b"\r\n\r\n")
    status = int(head.split(b" ")[1])
    length = int(
        next(
            line for line in head.split(b"\r\n") if line.lower().startswith(b"content-length")
        ).split(b":")[1]
    )
    payload = await reader.readexactly(length)
    writer.close()
    return status, json.loads(payload) if payload.startswith((b"{", b"[")) else payload


async def test_api_creates_checks_and_lists(tmp_path: Path) -> None:
    db = Database(tmp_path / "history.db")
    controller = Controller(
        Store(db, tmp_path / "config.json"),
        EventLog(db),
        tmp_path / "ser2net.yaml",
        custom_file=tmp_path / "own.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )
    web = WebServer(controller, port=0, hosts=("127.0.0.1",), peers=None)
    await web.start()
    assert web._server is not None
    port = web._server.sockets[0].getsockname()[1]

    status, created = await request(
        port,
        "POST",
        "api/connections",
        {"connection": {"name": "eHZ", "device": "/dev/null", "port": 3335}},
    )
    assert status == 200 and isinstance(created, dict) and created["rebuilt"] == ["eHZ"]
    status, refused = await request(
        port,
        "POST",
        "api/connections",
        {"connection": {"name": "x", "device": "/dev/null", "port": 0}},
    )
    assert status == 400 and isinstance(refused, dict) and set(refused["errors"]) == {"port"}
    status, state = await request(port, "GET", "api/state")
    assert status == 200 and isinstance(state, dict)
    assert [c["name"] for c in state["connections"]] == ["eHZ"]
    status, page = await request(port, "GET", "")
    assert status == 200 and b"<device-proxy>" in page  # type: ignore[operator]
    assert (await request(port, "GET", "api/nothing"))[0] == 404
    status, running = await request(port, "GET", "api/runtime")
    assert status == 200 and isinstance(running, dict) and running["connections"] == 1
    assert "tcp," in running["text"] and "admin:" in running["text"]
    other = await asyncio.start_server(lambda r, w: None, "0.0.0.0", 0)  # another program
    taken = other.sockets[0].getsockname()[1]
    status, preview = await request(
        port,
        "POST",
        "api/preview",
        {
            "connection": {
                "name": "x",
                "kind": "modbus",
                "device": "",
                "host": "1.2.3.4",
                "port": taken,
            }
        },
    )
    assert isinstance(preview, dict) and preview["warnings"] == {
        "port": "in use by another program"
    }
    other.close()
    await web.stop()


async def test_backup_and_restore(tmp_path: Path) -> None:
    db = Database(tmp_path / "history.db")
    controller = Controller(
        Store(db, tmp_path / "config.json"),
        EventLog(db),
        tmp_path / "ser2net.yaml",
        custom_file=tmp_path / "own.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )
    web = WebServer(controller, port=0, hosts=("127.0.0.1",), peers=None)
    await web.start()
    assert web._server is not None
    port = web._server.sockets[0].getsockname()[1]
    await request(
        port,
        "POST",
        "api/connections",
        {"connection": {"name": "eHZ", "device": "/dev/null", "port": 3335}},
    )
    status, backup = await request(port, "GET", "api/backup")
    assert status == 200 and isinstance(backup, dict)
    text = json.dumps(backup)
    await request(port, "DELETE", f"api/connections/{backup['config']['connections'][0]['id']}")
    status, preview = await request(port, "POST", "api/restore/preview", {"text": text})
    assert status == 200 and isinstance(preview, dict)
    assert preview["total"] == 1 and preview["kinds"]["serial"] == 1 and preview["current"] == 0
    assert (await request(port, "POST", "api/restore/preview", {"text": "{}"}))[0] == 400
    assert (await request(port, "POST", "api/restore/preview", {"text": "nonsense"}))[0] == 400
    assert (await request(port, "POST", "api/restore", {"text": text}))[0] == 200
    status, state = await request(port, "GET", "api/state")
    assert isinstance(state, dict) and [c["name"] for c in state["connections"]] == ["eHZ"]
    await web.stop()


async def test_the_mqtt_password_stays_on_the_server(tmp_path: Path) -> None:
    db = Database(tmp_path / "history.db")
    controller = Controller(
        Store(db, tmp_path / "config.json"),
        EventLog(db),
        tmp_path / "ser2net.yaml",
        custom_file=tmp_path / "own.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )
    web = WebServer(controller, port=0, hosts=("127.0.0.1",), peers=None)
    await web.start()
    assert web._server is not None
    port = web._server.sockets[0].getsockname()[1]
    secret = {"mqtt_host": "emqx", "mqtt_user": "anna", "mqtt_password": "geheim"}
    assert (await request(port, "PUT", "api/settings", {"settings": secret}))[0] == 200
    status, state = await request(port, "GET", "api/state")
    assert isinstance(state, dict) and "geheim" not in json.dumps(state)
    kept = state["settings"]["mqtt_password"]
    assert kept and state["settings"]["mqtt_user"] == "anna"
    # the form sends back what it got, with another change: the password stays
    status, _ = await request(
        port, "PUT", "api/settings", {"settings": {**state["settings"], "mqtt_port": 1884}}
    )
    assert status == 200
    assert controller.config.settings.mqtt_password == "geheim"
    assert controller.config.settings.mqtt_port == 1884
    status, versions = await request(port, "GET", "api/versions")
    assert isinstance(versions, list)
    for v in versions:
        _, config = await request(port, "GET", f"api/versions/{v['id']}")
        assert "geheim" not in json.dumps(config)
    await web.stop()


async def test_bodies_of_the_wrong_shape_and_trace_links(tmp_path: Path) -> None:
    db = Database(tmp_path / "history.db")
    controller = Controller(
        Store(db, tmp_path / "config.json"),
        EventLog(db),
        tmp_path / "ser2net.yaml",
        custom_file=tmp_path / "own.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )
    web = WebServer(controller, port=0, hosts=("127.0.0.1",), peers=None)
    await web.start()
    assert web._server is not None
    port = web._server.sockets[0].getsockname()[1]
    assert (await request(port, "PUT", "api/settings", [1, 2]))[0] == 400
    assert (await request(port, "POST", "api/import", {"text": "", "take": 5}))[0] == 400
    assert (await request(port, "POST", "api/import", {"text": "", "on_conflict": [1]}))[0] == 400
    backup = json.dumps({"app": "device_proxy_backup", "config": "x"})
    assert (await request(port, "POST", "api/restore/preview", {"text": backup}))[0] == 400
    backup = json.dumps({"app": "device_proxy_backup", "config": {"connections": [5]}})
    assert (await request(port, "POST", "api/restore/preview", {"text": backup}))[0] == 400
    (tmp_path / "trace").mkdir()
    (tmp_path / "secret").write_text("token")
    (tmp_path / "trace" / "x.log").symlink_to(tmp_path / "secret")
    assert (await request(port, "GET", "api/trace/x.log"))[0] == 404
    assert (await request(port, "GET", "api/trace/a%22b.log"))[0] == 400
    big = bytes(range(256)) * 1000  # several blocks and a short last one
    (tmp_path / "trace" / "big.log").write_bytes(big)
    assert await request(port, "GET", "api/trace/big.log") == (200, big)
    await web.stop()


async def test_a_request_that_does_not_come_closes_the_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from device_proxy import web as web_module

    monkeypatch.setattr(web_module, "IDLE_SECONDS", 0.2)
    monkeypatch.setattr(web_module, "BODY_SECONDS", 0.2)
    db = Database(tmp_path / "history.db")
    controller = Controller(
        Store(db, tmp_path / "config.json"),
        EventLog(db),
        tmp_path / "ser2net.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )
    web = WebServer(controller, port=0, hosts=("127.0.0.1",), peers=None)
    await web.start()
    assert web._server is not None
    port = web._server.sockets[0].getsockname()[1]
    for sent in (
        b"",
        b"GET /api/sta",
        b"POST /api/settings HTTP/1.1\r\nContent-Length: 9\r\n\r\n{",
    ):
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(sent)
        assert await asyncio.wait_for(reader.read(), 2) == b""  # closed, nothing answered
        writer.close()
    assert (await request(port, "GET", "api/state"))[0] == 200  # the others are served
    await web.stop()


async def test_effects_before_settings_imports_and_restores(tmp_path: Path) -> None:
    db = Database(tmp_path / "history.db")
    controller = Controller(
        Store(db, tmp_path / "config.json"),
        EventLog(db),
        tmp_path / "ser2net.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )
    web = WebServer(controller, port=0, hosts=("127.0.0.1",), peers=None)
    await web.start()
    assert web._server is not None
    port = web._server.sockets[0].getsockname()[1]
    connection = {"name": "eHZ", "device": "/dev/null", "port": 3335}
    assert (await request(port, "POST", "api/connections", {"connection": connection}))[0] == 200
    controller.write_config()  # as running: eHZ is set up
    status, answer = await request(
        port, "POST", "api/settings/effects", {"settings": {"listen": "all"}}
    )
    assert status == 200 and answer == {
        "effects": [{"name": "eHZ", "effect": "restart", "clients": 0}]
    }
    status, answer = await request(
        port, "POST", "api/settings/effects", {"settings": {"listen": "x"}}
    )
    assert status == 400
    text = (
        "connections:\n  meter:\n    accepter: tcp,3336\n"
        "    connector: serialdev,/dev/zero,9600n81\n"
    )
    status, answer = await request(
        port, "POST", "api/import/effects", {"text": text, "replace_all": True}
    )
    assert status == 200 and answer == {
        "effects": [{"name": "eHZ", "effect": "stop", "clients": 0}]
    }
    status, answer = await request(port, "POST", "api/import/effects", {"text": text})
    assert status == 200 and answer == {"effects": []}  # added next to it: nothing restarts
    status, versions = await request(port, "GET", "api/versions")
    assert isinstance(versions, list) and versions
    status, answer = await request(port, "GET", f"api/versions/{versions[0]['id']}/effects")
    assert status == 200 and answer == {"effects": []}  # the version that runs
    assert (await request(port, "GET", "api/versions/999/effects"))[0] == 404
    await web.stop()


async def test_a_full_disk_saves_nothing_and_says_so(tmp_path: Path) -> None:
    import errno
    import os
    import sqlite3

    db = Database(tmp_path / "history.db")
    store = Store(db, tmp_path / "config.json")
    controller = Controller(
        store,
        EventLog(db),
        tmp_path / "ser2net.yaml",
        trace=TraceHub(tmp_path / "trace", tmp_path / "shm"),
    )
    web = WebServer(controller, port=0, hosts=("127.0.0.1",), peers=None)
    await web.start()
    assert web._server is not None
    port = web._server.sockets[0].getsockname()[1]
    first = {"name": "eHZ", "device": "/dev/null", "port": 3335}
    assert (await request(port, "POST", "api/connections", {"connection": first}))[0] == 200
    saved = (tmp_path / "config.json").read_text()

    def full(fd: int) -> None:
        raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))

    real_fsync = os.fsync
    os.fsync = full  # type: ignore[assignment]
    try:
        second = {"name": "Z-Wave", "device": "/dev/zero", "port": 3333}
        status, answer = await request(port, "POST", "api/connections", {"connection": second})
    finally:
        os.fsync = real_fsync
    assert status == 507 and isinstance(answer, dict) and "not saved" in answer["error"]
    assert [c.name for c in controller.config.connections] == ["eHZ"]  # nothing changed
    assert (tmp_path / "config.json").read_text() == saved and not (
        tmp_path / "config.tmp"
    ).exists()

    # the file is written, the history is full: the change counts all the same
    real_execute = db.execute

    def history_full(sql: str, params: tuple[object, ...] = ()) -> sqlite3.Cursor:
        if sql.startswith(("INSERT INTO config_versions", "DELETE FROM config_versions")):
            raise sqlite3.OperationalError("database or disk is full")
        return real_execute(sql, params)

    db.execute = history_full  # type: ignore[method-assign]
    status, _ = await request(port, "POST", "api/connections", {"connection": second})
    db.execute = real_execute  # type: ignore[method-assign]
    assert status == 200 and len(controller.config.connections) == 2
    assert "Z-Wave" in (tmp_path / "config.json").read_text()
    await web.stop()
