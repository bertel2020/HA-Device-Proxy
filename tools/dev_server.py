"""Runs the app's web interface on a desktop, without ser2net and Home Assistant.

    .venv/bin/python tools/dev_server.py [port]    then open http://127.0.0.1:8399/

Three serial example connections, a simulated smart meter in the trace (the first one), a
Modbus TCP device simulated on 127.0.0.1 with a client polling it through the proxy, a
Modbus device that is not reachable, and some events. Nothing is shared on the network;
ser2net shows as not running. Data lives in a temporary folder that is removed at the end.
"""

from __future__ import annotations

import asyncio
import json
import logging
import struct
import sys
import tempfile
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "device_proxy" / "app"))

from device_proxy import controller as controller_module  # noqa: E402
from device_proxy import enocean, esp, process, testcase  # noqa: E402
from device_proxy.clients import KnownClients  # noqa: E402
from device_proxy.controller import Controller  # noqa: E402
from device_proxy.db import Database  # noqa: E402
from device_proxy.devices import Device, fingerprint  # noqa: E402
from device_proxy.events import EventLog  # noqa: E402
from device_proxy.meter import crc_x25  # noqa: E402
from device_proxy.model import AppConfig, Connection, Settings  # noqa: E402
from device_proxy.store import Store  # noqa: E402
from device_proxy.trace import TraceHub  # noqa: E402
from device_proxy.web import WebServer  # noqa: E402


def _sml() -> bytes:
    """One SML telegram with a meter reading (1.8.0 = 18 450 282.7 Wh) and a right CRC."""
    body = bytes.fromhex("7707 0100010800ff 6500 1c0104 01 621e 52ff 69000000000aff4a2b 01")
    data = bytes.fromhex("1b1b1b1b01010101") + body + bytes.fromhex("1b1b1b1b1a00")
    crc = crc_x25(data)
    return data + bytes([crc & 0xFF, crc >> 8])


SML = _sml()


async def meter(trace: TraceHub, alias: str, stop: asyncio.Event) -> None:
    path = trace.shm_dir / f"{alias}.trace"
    while not stop.is_set():
        stamp = time.strftime("%Y/%m/%d %H:%M:%S").encode()
        lines = []
        for i in range(0, len(SML), 8):
            part = SML[i : i + 8]
            text = "".join(chr(b) if 32 <= b < 127 else "." for b in part)
            lines.append(stamp + b" term " + part.hex(" ").encode() + b" |" + text.encode() + b"|")
        with path.open("ab") as f:
            f.write(b"\n".join(lines) + b"\n")
        await asyncio.sleep(1)


SUNSPEC = (
    b"SunS"
    + struct.pack(">HH", 1, 65)
    + b"".join(
        text.ljust(size * 2, b"\x00")
        for text, size in ((b"SolarEdge", 16), (b"SE10K", 16), (b"", 8), (b"0004.0019", 8))
    )
)


async def modbus_device(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Units 1 and 2; holding register n holds n * 10 (an inverter's power, say)."""
    try:
        while True:
            tid, _, length, unit = struct.unpack(">HHHB", await reader.readexactly(7))
            pdu = await reader.readexactly(length - 1)
            if unit not in (1, 2):
                continue  # nobody there
            if pdu[:2] == b"\x2b\x0e" and unit == 1:  # device identification
                objects = ((0, b"SolarEdge"), (1, b"SE10K"), (2, b"0004.0019"))
                body = bytes([0x2B, 0x0E, 1, 1, 0, 0, len(objects)])
                body += b"".join(bytes([i, len(v)]) + v for i, v in objects)
                writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
                continue
            if pdu[0] != 3:
                body = bytes([pdu[0] | 0x80, 1])  # illegal function
                writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
                continue
            address, count = struct.unpack(">HH", pdu[1:5])
            if unit == 1 and 40000 <= address < 40070:  # SunSpec marker and common model
                regs = SUNSPEC[(address - 40000) * 2 :].ljust(count * 2, b"\x00")[: count * 2]
                body = bytes([3, count * 2]) + regs
                writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
                continue

            body = bytes([3, count * 2]) + b"".join(
                struct.pack(">H", (address + i) * 10 % 65536) for i in range(count)
            )
            await asyncio.sleep(0.015)
            writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
    except (asyncio.IncompleteReadError, ConnectionError):
        writer.close()


async def modbus_client(port: int, stop: asyncio.Event) -> None:
    await asyncio.sleep(1)
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    tid = 0
    while not stop.is_set():
        tid += 1
        writer.write(struct.pack(">HHHBBHH", tid, 0, 6, 1, 3, 40000 + tid % 50, 4))
        head = await reader.readexactly(7)
        await reader.readexactly(struct.unpack(">HHHB", head)[2] - 1)
        await asyncio.sleep(2)


def _esp2(hseq_org: str, data: str, sender: str, status: str = "30") -> bytes:
    body = bytes.fromhex(hseq_org + data + sender + status)
    return b"\xa5\x5a" + body + bytes([sum(body) & 0xFF])


ESP2_RADIO = [  # rocker presses, a window contact, a meter (4BS)
    _esp2("0B05", "70000000", "FEE91234"),
    _esp2("0B05", "00000000", "FEE91234", "20"),
    _esp2("0B06", "09000000", "0181A2B3"),
    _esp2("0B07", "FF6C0418", "01908C14", "00"),
    _esp2("0B05", "50000000", "00216343"),
]


async def esp2_gateway(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """A FAM-USB: radio telegrams every few seconds, the base ID on request (and to change)."""
    base = "FFABCD80"

    async def talk() -> None:
        n = 0
        while True:
            await asyncio.sleep(2.5)
            writer.write(ESP2_RADIO[n % len(ESP2_RADIO)])
            n += 1

    task = asyncio.create_task(talk())
    try:
        buffer = b""
        while chunk := await reader.read(1024):
            buffer += chunk
            while len(buffer) >= 14:
                start = buffer.find(b"\xa5\x5a")
                if start < 0:
                    buffer = b""
                    break
                frame, buffer = buffer[start : start + 14], buffer[start + 14 :]
                if len(frame) == 14 and frame[3] == 0x58:
                    await asyncio.sleep(0.01)
                    writer.write(_esp2("8B98", base, "00000000", "00"))
                elif len(frame) == 14 and frame[3] == 0x18:  # SET_IDBASE
                    base = frame[4:8].hex().upper()
                    await asyncio.sleep(0.3)  # the flash
                    writer.write(_esp2("8B58", "00000000", "00000000", "00"))
    except ConnectionError:
        pass
    finally:
        task.cancel()
        writer.close()


async def enocean_client(port: int, stop: asyncio.Event) -> None:
    """Home Assistant: replay with times, reads the base ID, sends a rocker telegram at times."""
    await asyncio.sleep(1)
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(b"EOPX REPLAY TS\n" + _esp2("AB58", "00000000", "00000000", "00"))
    n = 0
    while not stop.is_set():
        await asyncio.sleep(7)
        n += 1
        writer.write(_esp2("6B05", "30000000" if n % 2 else "00000000", "FFABCD81"))
        await reader.read(4096)


# playing back a test case (the button "As a test case" on a connection's live data)


def _replay_answers(frames: list[tuple[float, str, bytes]], key: Callable[[bytes], Any]) -> dict:
    """Each recorded request (by key) → the answer that came after it."""
    answers = {}
    for i, (_, direction, raw) in enumerate(frames):
        if direction == "tx":
            following = next((r for _, d, r in frames[i + 1 :] if d == "rx"), None)
            if following is not None:
                answers.setdefault(key(raw), following)
    return answers


def replay_server(case: dict[str, Any]) -> Callable[..., Awaitable[None]]:
    """A fake device that plays a test case back: EnOcean sends the radio telegrams in a
    loop and answers known commands, Modbus answers the recorded requests."""
    frames = testcase.frames_of(case)
    kind, link = case["connection"]["kind"], case["connection"].get("link", "tcp")
    protocol = case["connection"].get("esp_protocol", "esp2")

    async def enocean(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        answers = _replay_answers(frames, bytes)
        radio = [(t, raw) for t, d, raw in frames if d == "rx" and esp.is_radio(protocol, raw)]

        async def play() -> None:
            while radio:
                last = 0.0
                for t, raw in radio:
                    await asyncio.sleep(max(0.05, t - last))
                    last = t
                    writer.write(raw)
                await asyncio.sleep(2)

        task = asyncio.create_task(play())
        buffer = b""
        try:
            while data := await reader.read(4096):
                buffer = (buffer + data)[-512:]
                for request, answer in answers.items():
                    if request in buffer:
                        writer.write(answer)
                        buffer = buffer.replace(request, b"")
        finally:
            task.cancel()
            writer.close()

    def pdu(raw: bytes) -> tuple[int, bytes]:
        return (raw[6], raw[7:]) if link == "tcp" else (raw[0], raw[1:-2])

    async def modbus(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        answers = _replay_answers(frames, pdu)
        try:
            while True:
                tid, _, length, unit = struct.unpack(">HHHB", await reader.readexactly(7))
                request = await reader.readexactly(length - 1)
                recorded = answers.get((unit, request))
                body = pdu(recorded)[1] if recorded else bytes([request[0] | 0x80, 2])
                writer.write(struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body)
        except (asyncio.IncompleteReadError, ConnectionError):
            writer.close()

    return enocean if kind == "enocean" else modbus


async def replay_serial(
    case: dict[str, Any], trace: TraceHub, alias: str, stop: asyncio.Event
) -> None:
    """A serial test case: what the device sent, again and again, into the live trace."""
    rx = [(t, raw) for t, d, raw in testcase.frames_of(case) if d == "rx"]
    path = trace.shm_dir / f"{alias}.trace"
    while rx and not stop.is_set():
        last = 0.0
        for t, raw in rx:
            await asyncio.sleep(max(0.05, t - last))
            last = t
            stamp = time.strftime("%Y/%m/%d %H:%M:%S").encode()
            lines = [
                stamp + b" term " + raw[i : i + 8].hex(" ").encode() + b" |........|"
                for i in range(0, len(raw), 8)
            ]
            with path.open("ab") as f:
                f.write(b"\n".join(lines) + b"\n")
        await asyncio.sleep(2)


async def main(port: int, offset: int = 0, replay: Path | None = None) -> None:
    """offset moves the example connections' ports, so two dev servers can run at once."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    process.RESTART_DELAYS = (3600,)  # no ser2net here: do not retry
    controller_module.STATUS_POLL = 3600
    # the BWT's adapter, now on another port: "Device Proxy" offers to take it over
    adapter = Device(
        "/dev/ttyUSB7",
        by_path=["/dev/serial/by-path/platform-xhci-hcd.0-usb-0:1.4:1.0-port0"],
        vendor_id="1a86",
        product_id="7523",
        product="USB Serial",
    )
    # sticks that name themselves: the form picks them by template, the plain adapter for a meter
    enocean_stick = Device(
        "/dev/ttyUSB0",
        by_id=["/dev/serial/by-id/usb-EnOcean_GmbH_EnOcean_Programmer_V3.2_FTWH6OMP-if00-port0"],
        vendor_id="0403",
        product_id="6001",
        manufacturer="EnOcean GmbH",
        product="EnOcean Programmer V3.2",
        serial="FTWH6OMP",
        driver="ftdi_sio",
    )
    zwave_stick = Device(
        "/dev/ttyACM0",
        by_id=["/dev/serial/by-id/usb-0658_0200-if00"],
        vendor_id="0658",
        product_id="0200",
        driver="cdc_acm",
    )
    controller_module.scan = lambda: [enocean_stick, zwave_stick, adapter]
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        device = await asyncio.start_server(modbus_device, "127.0.0.1", 0)
        device_port = device.sockets[0].getsockname()[1]
        gateway = await asyncio.start_server(esp2_gateway, "127.0.0.1", 0)
        gateway_port = gateway.sockets[0].getsockname()[1]
        spare = await asyncio.start_server(esp2_gateway, "127.0.0.1", 0)  # same base ID
        spare_port = spare.sockets[0].getsockname()[1]
        enocean.BASE_ID_FILE = data / "enocean_base_ids.json"
        db = Database(data / "history.db")
        events = EventLog(db)
        store = Store(db, data / "config.json")
        config = AppConfig(
            settings=Settings(
                enocean_status_port=19199 + offset, client_names="127.0.0.1 Home Assistant"
            ),
            connections=(
                Connection(
                    "eHZ SML",
                    "/dev/null",
                    3335 + offset,
                    template="ehz_sml",
                    max_clients=5,
                    trace="rx",
                ),
                Connection(
                    "Z-Wave-Gateway",
                    "/dev/zero",
                    3333 + offset,
                    baud=115200,
                    max_clients=2,
                    nodelay=True,
                    template="zwave",
                ),
                Connection(
                    "BWT AQA perla",
                    "/dev/ttyMISSING0",
                    3334 + offset,
                    baud=19200,
                    max_clients=2,
                    id="0000b001",
                ),
                Connection(
                    "SolarEdge SE10K",
                    "",
                    15020 + offset,
                    kind="modbus",
                    template="modbus",
                    host="127.0.0.1",
                    host_port=device_port,
                    max_clients=10,
                    bind="127.0.0.1",
                    trace="both",
                ),
                Connection(
                    "FAM-USB",
                    "",
                    19100 + offset,
                    id="0000fa01",
                    kind="enocean",
                    template="fam_usb",
                    model="fam_usb",
                    link="tcp",
                    host="127.0.0.1",
                    host_port=gateway_port,
                    max_clients=4,
                    remaddr="127.0.0.1, 172.30.32.0/23",
                    bind="127.0.0.1",
                    trace="both",
                    fallback="0000fa02",
                ),
                Connection(
                    "FAM-USB 2",
                    "",
                    19102 + offset,
                    id="0000fa02",
                    kind="enocean",
                    template="fam_usb",
                    model="fam_usb",
                    link="tcp",
                    host="127.0.0.1",
                    host_port=spare_port,
                    max_clients=4,
                    remaddr="127.0.0.1, 172.30.32.0/23",
                    bind="127.0.0.1",
                ),
                Connection(
                    "MGW-ETH",
                    "",
                    19101 + offset,
                    kind="enocean",
                    template="mgw_eth",
                    model="mgw_eth",
                    esp_protocol="esp3",
                    link="tcp",
                    host="127.0.0.1",
                    host_port=2,
                    max_clients=4,
                    remaddr="127.0.0.1, 172.30.32.0/23",
                    bind="127.0.0.1",
                ),
                Connection(
                    "NIBE S1155",
                    "",
                    15021 + offset,
                    kind="modbus",
                    template="modbus",
                    host="127.0.0.1",
                    host_port=1,
                    max_clients=10,
                    bind="127.0.0.1",
                ),
            ),
        )
        case = json.loads(replay.read_text()) if replay else None
        replayed = None
        if case is not None:
            kind = case["connection"]["kind"]
            if kind == "serial":
                replayed = Connection("Testfall", "/dev/null", 3399 + offset, max_clients=3)
            else:
                fake = await asyncio.start_server(replay_server(case), "127.0.0.1", 0)
                replayed = Connection(
                    "Testfall",
                    "",
                    19199 + offset if kind == "enocean" else 15099 + offset,
                    kind=kind,
                    template="modbus" if kind == "modbus" else "fam_usb",
                    esp_protocol=case["connection"].get("esp_protocol", "esp2"),
                    host="127.0.0.1",
                    host_port=fake.sockets[0].getsockname()[1],
                    max_clients=4,
                    bind="127.0.0.1",
                )
            config = config.with_connection(replayed)
        store.save(AppConfig(), config, "test")
        trace = TraceHub(record_dir=data / "trace", shm_dir=data / "shm")
        (data / "device_prints.json").write_text(json.dumps({"0000b001": fingerprint(adapter)}))
        # a computer seen for the first time, for the card Clients in the settings
        (data / "known_clients.json").write_text(
            json.dumps(
                {
                    "known": {},
                    "new": {
                        "192.168.1.77": {
                            "first": time.time() - 3600,
                            "connection": "SolarEdge SE10K",
                            "address": "192.168.1.77:51234",
                        }
                    },
                }
            )
        )
        controller = Controller(
            store,
            events,
            data / "ser2net.yaml",
            custom_file=data / "own.yaml",
            import_dir=data / "import",
            trace=trace,
            known_clients=KnownClients(data / "known_clients.json"),
            prints_file=data / "device_prints.json",
        )
        web = WebServer(controller, port=port, hosts=("127.0.0.1",), peers=None, version="dev")
        await web.start()
        stop = asyncio.Event()
        task = asyncio.create_task(controller.start(stop))
        await asyncio.sleep(0.5)
        alias = controller.config.connections[0].alias
        feeder = asyncio.create_task(meter(trace, alias, stop))
        poller = asyncio.create_task(modbus_client(15020 + offset, stop))
        home_assistant = asyncio.create_task(enocean_client(19100 + offset, stop))
        if case is not None and replayed is not None and replayed.kind == "serial":
            asyncio.create_task(replay_serial(case, trace, replayed.alias, stop))
        print(f"Open http://127.0.0.1:{port}/  (Ctrl+C ends)")
        try:
            await asyncio.Event().wait()
        finally:
            stop.set()
            feeder.cancel()
            poller.cancel()
            home_assistant.cancel()
            gateway.close()
            spare.close()
            device.close()
            await task
            await web.stop()


if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        replay = None
        if "--replay" in args:  # tools/dev_server.py 8399 --replay testcase-enocean-….json
            index = args.index("--replay")
            replay = Path(args[index + 1])
            del args[index : index + 2]
        port = int(args[0]) if args else 8399
        asyncio.run(main(port, int(args[1]) if len(args) > 1 else 0, replay))
    except KeyboardInterrupt:
        pass
