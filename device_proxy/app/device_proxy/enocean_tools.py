"""Tools for EnOcean gateways: capture every frame, send one frame, test the gateway.

A capture writes each frame in both directions as one JSON line (time, gateway, dir, kind,
peer, hex) into the trace folder, next to the trace recordings, so the trace page lists,
downloads and deletes it. One capture at a time, at most MAX_BYTES. While it runs, the
gateway can be reserved for one program (exclusive_peer: PCT14 reading a FAM14): the frames
of the others are held back, and the app's own tools do not send either.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

from . import esp
from .config import readable_alias
from .enocean import EnOceanProxy

_LOGGER = logging.getLogger(__name__)

MAX_BYTES = 50 * 1024 * 1024
SUFFIX = ".jsonl"


class ToolError(ValueError):
    """Shown to the user as it is."""


@dataclass
class Capture:
    connection: str  # id
    name: str  # the connection's name
    path: Path
    file: IO[str]
    started: float
    exclusive_peer: str | None
    bytes: int = 0
    frames: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "connection": self.connection,
            "name": self.name,
            "file": self.path.name,
            "started": self.started,
            "exclusive_peer": self.exclusive_peer,
            "bytes": self.bytes,
            "frames": self.frames,
        }


class Captures:
    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.current: Capture | None = None
        self._proxy: EnOceanProxy | None = None

    def start(self, proxy: EnOceanProxy, exclusive_peer: str | None) -> Capture:
        if self.current is not None:
            raise ToolError(f"a capture of {self.current.name} is running")
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.folder / f"{readable_alias(proxy.c.name, set())}-capture-{stamp}{SUFFIX}"
        capture = Capture(
            proxy.c.id,
            proxy.c.name,
            path,
            path.open("a", encoding="utf-8"),
            time.time(),
            exclusive_peer or None,
        )
        self.current, self._proxy = capture, proxy
        proxy.exclusive_peer = capture.exclusive_peer
        proxy.observers.append(self._write)
        _LOGGER.info("Capture of %s into %s", proxy.c.name, path.name)
        return capture

    def stop(self) -> Capture | None:
        capture, proxy = self.current, self._proxy
        if capture is None:
            return None
        if proxy is not None:
            proxy.exclusive_peer = None
            if self._write in proxy.observers:
                proxy.observers.remove(self._write)
        capture.file.close()
        self.current, self._proxy = None, None
        return capture

    def _write(self, direction: str, frame: bytes, peer: str) -> None:
        capture, proxy = self.current, self._proxy
        if capture is None or proxy is None:
            return
        protocol = proxy.protocol
        kind = (
            "radio"
            if esp.is_radio(protocol, frame)
            else "answer"
            if esp.is_response(protocol, frame)
            else "other"
        )
        line = json.dumps(
            {
                "time": round(time.time(), 3),
                "gateway": capture.name,
                "dir": direction,
                "kind": kind,
                "peer": peer or None,
                "hex": frame.hex(),
            }
        )
        capture.file.write(line + "\n")
        capture.file.flush()
        capture.bytes += len(line) + 1
        capture.frames += 1
        if capture.bytes >= MAX_BYTES:
            _LOGGER.warning("Capture %s stopped at %d MB", capture.path.name, MAX_BYTES >> 20)
            self.stop()


def parse_frame(protocol: str, text: str) -> bytes:
    """Hex digit pairs (spaces, ":" and "-" allowed) → exactly one whole frame."""
    cleaned = "".join(ch for ch in text if ch not in " :-\t\n")
    try:
        frame = bytes.fromhex(cleaned)
    except ValueError:
        raise ToolError("only hex digit pairs") from None
    if esp.Splitter(protocol).feed(frame) != [frame]:
        raise ToolError(f"not exactly one complete {protocol.upper()} frame")
    return frame


def sendable(proxy: EnOceanProxy) -> EnOceanProxy:
    if proxy.exclusive_peer is not None:
        raise ToolError(f"reserved for {proxy.exclusive_peer} during a capture")
    if not proxy.link.is_open:
        raise ToolError("the gateway is not connected")
    return proxy
