import asyncio
import json
from pathlib import Path

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
