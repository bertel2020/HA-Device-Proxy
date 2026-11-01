"""A connection's last frames as a test case: a file to attach to an issue, which
tools/dev_server.py plays back as a fake device.

The frames come from the live trace (the last few hundred). Client addresses are never in
it. EnOcean sender IDs and the base ID are replaced by made-up ones unless the user keeps
them, with each frame's checksum computed again; the gateway's own range keeps its offsets,
so "own" telegrams stay recognisable. Modbus registers and smart meter data stay as they are
(a meter's telegrams contain its number: the web interface says so).
"""

from __future__ import annotations

import time
from typing import Any

from . import esp
from .model import Connection
from .trace import Chunk

FORMAT = "device-proxy-testcase"
VERSION = 1
FAKE_BASE = 0xFFAA0000  # the base ID in an anonymised test case
FAKE_SENDER = 0xA0000001  # the first made-up sender ID


def _esp_checksums(protocol: str, frame: bytearray) -> None:
    if protocol == "esp2" and len(frame) == 14:
        frame[13] = sum(frame[2:13]) & 0xFF
    elif protocol == "esp3" and len(frame) >= 7:
        length, optional = int.from_bytes(frame[1:3], "big"), frame[3]
        end = 6 + length + optional
        if len(frame) > end:
            frame[end] = esp.crc8(bytes(frame[6:end]))


def anonymise(protocol: str, frames: list[bytes], base_id: str | None) -> list[bytes]:
    """The frames with every sender ID and the base ID replaced, consistently."""
    ids: dict[bytes, bytes] = {}
    base = int(base_id.replace("-", ""), 16) if base_id else None
    if base is not None:
        ids[base.to_bytes(4, "big")] = FAKE_BASE.to_bytes(4, "big")
    fake = FAKE_SENDER
    for frame in frames:
        info = esp.radio_info(protocol, frame)
        if info is None:
            continue
        raw = bytes.fromhex(info[1].replace("-", ""))
        number = int.from_bytes(raw, "big")
        if raw in ids:
            continue
        if base is not None and base <= number <= base + 0x7F:
            ids[raw] = (FAKE_BASE + number - base).to_bytes(4, "big")
        else:
            ids[raw] = fake.to_bytes(4, "big")
            fake += 1
    result = []
    for frame in frames:
        changed = bytearray(frame)
        for old, new in ids.items():
            start = changed.find(old, 2)
            while start >= 0:
                changed[start : start + 4] = new
                start = changed.find(old, start + 4)
        if changed != frame:
            _esp_checksums(protocol, changed)
        result.append(bytes(changed))
    return result


def build(
    c: Connection, chunks: list[Chunk], *, base_id: str | None, anonymised: bool
) -> dict[str, Any]:
    frames = [ch for ch in chunks if ch.direction in ("rx", "tx") and ch.data]
    data = [ch.data for ch in frames]
    if anonymised and c.kind == "enocean":
        data = anonymise(c.esp_protocol, data, base_id)
    start = frames[0].ts if frames else time.time()
    connection: dict[str, Any] = {"kind": c.kind}
    if c.kind == "enocean":
        connection |= {"esp_protocol": c.esp_protocol, "model": c.model}
    elif c.kind == "modbus":
        connection |= {"link": c.link}
    if c.uses_device:
        connection |= {"baud": c.baud, "format": c.serial_format}
    return {
        "format": FORMAT,
        "version": VERSION,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "anonymised": anonymised and c.kind == "enocean",
        "connection": connection,
        "frames": [
            {
                "t": round(ch.ts - start, 3),
                "dir": ch.direction,
                "hex": raw.hex(),
                "info": ch.info.rsplit(" · ", 1)[0] if c.kind == "modbus" else "",  # no client
            }
            for ch, raw in zip(frames, data, strict=True)
        ],
    }


def frames_of(case: dict[str, Any]) -> list[tuple[float, str, bytes]]:
    """(seconds from the start, "rx" or "tx", bytes) of a test case; raises ValueError."""
    if case.get("format") != FORMAT:
        raise ValueError("not a Device Proxy test case")
    return [(float(f["t"]), str(f["dir"]), bytes.fromhex(f["hex"])) for f in case["frames"]]
