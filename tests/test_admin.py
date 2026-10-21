import asyncio
import tempfile
from pathlib import Path

from device_proxy.admin import AdminClient

# what ser2net 4.6 writes in yaml mode (controller.c / portinfo.c)
SHOWPORT = (
    "\r\n%YAML 1.1\r\n---\r\nresponse: \r\n  name: !!str 'showport'\r\n"
    "  port: \r\n    name: !!str 'c_0000000a'\r\n    accepter: !!str 'tcp,3335'\r\n"
    "    enable state: !!str 'on'\r\n    timeout: !!int 0\r\n"
    "    connected: \r\n      name: !!str 'ipv4,192.168.1.20,50114'\r\n"
    "      timeout left: !!int 0\r\n      bytes read from TCP: !!int 0\r\n"
    "      bytes written to TCP: !!int 96200\r\n"
    "    device: !!str '/dev/ttyUSB1'\r\n    bytes read from device: !!int 96200\r\n"
    "    bytes written to device: !!int 0\r\n    close state: !!str 'retained'\r\n"
    "  port: \r\n    name: !!str 'c_0000000b'\r\n    enable state: !!str 'off'\r\n"
    "    device: !!str '/dev/ttyACM0'\r\n    close state: !!str 'retained'\r\n...\r\n"
)
EVENT = (
    "\r\n%YAML 1.1\r\n---\r\nnew connection: \r\n  name: !!str 'c_0000000a'\r\n"
    "  remaddr: !!str 'ipv4,192.168.1.21,38610'\r\n...\r\n"
)


async def test_showport_and_pushed_events() -> None:
    events: list[tuple[str, str, str]] = []

    async def fake_ser2net(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        writer.write(b"-> ")
        assert await reader.readline() == b"yaml\r\n"
        writer.write(b"yaml\r\n" + EVENT.encode())
        assert await reader.readline() == b"showport\r\n"
        writer.write(SHOWPORT.encode())
        await writer.drain()
        await reader.read()

    path = str(Path(tempfile.mkdtemp(dir="/tmp")) / "admin.sock")  # short: sun_path limit
    server = await asyncio.start_unix_server(fake_ser2net, path)
    client = AdminClient(lambda *e: events.append(e), path=path)
    stop = asyncio.Event()
    task = asyncio.create_task(client.run(stop))
    await asyncio.wait_for(client.connected.wait(), 5)
    ports = await client.showport()
    stop.set()
    server.close()
    await task

    assert events == [("new connection", "c_0000000a", "192.168.1.21:38610")]
    assert [p.alias for p in ports] == ["c_0000000a", "c_0000000b"]
    assert ports[0].clients[0].address == "192.168.1.20:50114"
    assert ports[0].clients[0].bytes_to_client == 96200
    assert ports[1].enabled is False and ports[1].clients == []
