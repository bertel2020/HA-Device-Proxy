"""Tools for EnOcean gateways: capture every frame, send one frame, test the gateway.

A capture writes each frame in both directions as one JSON line (time, gateway, dir, kind,
peer, hex) into the trace folder, next to the trace recordings, so the trace page lists,
downloads and deletes it. One capture at a time, at most MAX_BYTES. While it runs, the
gateway can be reserved for one program (exclusive_peer: PCT14 reading a FAM14): the frames
of the others are dropped (not sent later), and the app's own tools do not send either.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import logging
import time
from collections.abc import Callable
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
        self.on_full: Callable[[Capture], None] | None = None  # the size limit ended a capture
        # writing failed (a full disk): the capture ended, the reservation with it
        self.on_failed: Callable[[Capture, str], None] | None = None

    def start(
        self, proxy: EnOceanProxy, exclusive_peer: str | None, alias: str | None = None
    ) -> Capture:
        """alias: the name of the connection's files (as its recordings), else from its name."""
        if self.current is not None:
            raise ToolError(f"a capture of {self.current.name} is running")
        self.folder.mkdir(parents=True, exist_ok=True)
        path, file = self._new_file(alias or readable_alias(proxy.c.name, set()))
        capture = Capture(
            proxy.c.id,
            proxy.c.name,
            path,
            file,
            time.time(),
            exclusive_peer or None,
        )
        self.current, self._proxy = capture, proxy
        proxy.exclusive_peer = capture.exclusive_peer
        proxy.observers.append(self._write)
        _LOGGER.info("Capture of %s into %s", proxy.c.name, path.name)
        return capture

    def _new_file(self, alias: str) -> tuple[Path, IO[str]]:
        """A file of its own: a second capture in the same second gets "-2", "-3" ...,
        never the first one's file."""
        stem = f"{alias}-capture-{time.strftime('%Y%m%d-%H%M%S')}"
        for number in range(1, 100):
            path = self.folder / f"{stem}{f'-{number}' if number > 1 else ''}{SUFFIX}"
            try:
                return path, path.open("x", encoding="utf-8")
            except FileExistsError:
                continue
        raise ToolError("no free file name for the capture")

    def stop(self) -> Capture | None:
        capture, proxy = self.current, self._proxy
        if capture is None:
            return None
        if proxy is not None:
            proxy.exclusive_peer = None
            if self._write in proxy.observers:
                proxy.observers.remove(self._write)
        try:
            capture.file.close()
        finally:
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
        try:
            capture.file.write(line + "\n")
            capture.file.flush()
        except OSError as err:
            _LOGGER.warning("Capture %s stopped: %s", capture.path.name, err)
            with contextlib.suppress(OSError):
                self.stop()  # closing flushes once more and may fail the same way
            if self.on_failed is not None:
                self.on_failed(capture, str(err))
            return
        capture.bytes += len(line) + 1
        capture.frames += 1
        if capture.bytes >= MAX_BYTES:
            _LOGGER.warning("Capture %s stopped at %d MB", capture.path.name, MAX_BYTES >> 20)
            self.stop()
            if self.on_full is not None:
                self.on_full(capture)


def parse_frame(protocol: str, text: str) -> bytes:
    """Hex digit pairs (spaces, ":" and "-" allowed) → exactly one whole frame."""
    cleaned = "".join(ch for ch in text if ch not in " :-\t\n")
    try:
        frame = bytes.fromhex(cleaned)
    except ValueError:
        raise ToolError("only hex digit pairs") from None
    whole = esp.Splitter(protocol).feed(frame) == [frame]
    looks_whole = protocol == "esp2" and len(frame) == esp.ESP2_FRAME and frame[:2] == b"\xa5\x5a"
    if (whole or looks_whole) and (error := esp.checksum_error(protocol, frame)):
        raise ToolError(f"{protocol.upper()} {error}")  # the splitter skips such an ESP2 frame
    if not whole:
        raise ToolError(f"not exactly one complete {protocol.upper()} frame")
    return frame


def sendable(proxy: EnOceanProxy) -> EnOceanProxy:
    if proxy.exclusive_peer is not None:
        raise ToolError(f"reserved for {proxy.exclusive_peer} during a capture")
    if not proxy.link.is_open:
        raise ToolError("the gateway is not connected")
    return proxy


def senders_csv(rows: list[dict[str, Any]]) -> bytes:
    """The list of senders as a file for a spreadsheet (with a BOM, for its umlauts). A name
    that looks like a formula is quoted, so opening the file cannot run it."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["id", "name", "kind", "telegrams", "last_seen", "dbm", "hops", "own", "new"])
    for row in rows:
        name = str(row.get("name", ""))
        writer.writerow(
            [
                row["id"],
                f"'{name}" if name[:1] in ("=", "+", "-", "@") else name,
                row["rorg"],
                row["count"],
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row["last"])),
                "" if row["dbm"] is None else row["dbm"],
                row["hops"],
                int(row["own"]),
                int(row["new"]),
            ]
        )
    return out.getvalue().encode("utf-8-sig")
