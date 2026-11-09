"""The data of each connection, as ser2net traces it, read along by the app.

Every connection of the forms has ser2net's trace-both on, as hex with timestamps, into a
file in /dev/shm (memory). ser2net opens trace files with a seek to the end, so a pipe does
not work; instead the app reads what is new every fraction of a second and frees the part
it has read (punching a hole: the file keeps its size, the memory is given back). Because
the trace is always on, recording, live view and "last data" never change ser2net's
configuration, so switching them never disconnects clients.

Lines look like "2026/10/20 10:44:01 term 1b 1b 1b 1b 01 01 01 01 |........|": "term" is
data from the device (rx), "tcp " data from the clients to the device (tx). ser2net also
writes OPEN (<address>) and CLOSE lines.

The Modbus proxy (modbus.py) is the app itself: it hands its requests and answers straight
to the hub (feed), with a line on each in info.
"""

from __future__ import annotations

import asyncio
import ctypes
import logging
import os
import re
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

SHM_DIR = Path("/dev/shm/ser2net-trace")
RECORD_DIR = Path("/config/trace")
LIVE_LINES = 400  # per connection, for the live view and the tools
READ_MAX = 1 << 20  # bytes per read
FALLBACK_LIMIT = 8 << 20  # without hole punching: start the file over above this size
LINE = re.compile(rb"^(\d{4}/\d\d/\d\d \d\d:\d\d:\d\d) (term|tcp ) ((?:[0-9a-f]{2} )+)\s*\|.*\|$")
MARK = re.compile(rb"^(\d{4}/\d\d/\d\d \d\d:\d\d:\d\d) (OPEN|CLOSE) ?(.*)$")

_FALLOC_KEEP_SIZE_PUNCH_HOLE = 0x01 | 0x02
_fallocate: Any
try:
    _fallocate = ctypes.CDLL(None, use_errno=True).fallocate
    _fallocate.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_longlong]
except (OSError, AttributeError):  # not Linux (tests on a desktop)
    _fallocate = None


def punch_hole(fd: int, length: int) -> bool:
    """Free the first length bytes of the file's storage; False when not possible."""
    if _fallocate is None or length <= 0:
        return False
    return bool(_fallocate(fd, _FALLOC_KEEP_SIZE_PUNCH_HOLE, 0, length) == 0)


def trace_path(alias: str) -> Path:
    return SHM_DIR / f"{alias}.trace"


@dataclass
class Chunk:
    ts: float
    direction: str  # "rx" from the device, "tx" to the device, "open" / "close"
    data: bytes = b""
    text: str = ""  # for open / close: what ser2net wrote
    seq: int = 0  # set by the TraceHub, increases per connection
    info: str = ""  # Modbus: what the request or answer is

    def to_dict(self) -> dict[str, object]:
        return {
            "ts": self.ts,
            "direction": self.direction,
            "hex": self.data.hex(" ").upper(),
            "text": self.text or self.data.decode("latin-1"),
            "seq": self.seq,
            "info": self.info,
        }

    def line(self) -> str:
        stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.ts))
        stamp += f".{int(self.ts * 1000) % 1000:03d}"
        if self.direction in ("open", "close"):
            return f"{stamp} {self.direction.upper()} {self.text}"
        line = f"{stamp} {self.direction.upper()} {self.data.hex(' ').upper()}"
        return f"{line} | {self.info}" if self.info else line


def _seconds(stamp: bytes, now: float) -> float:
    parsed = time.mktime(time.strptime(stamp.decode(), "%Y/%m/%d %H:%M:%S"))
    return now if int(now) == int(parsed) else parsed  # ser2net has whole seconds only


def parse_lines(lines: list[bytes], now: float) -> list[Chunk]:
    chunks: list[Chunk] = []
    for line in lines:
        if m := LINE.match(line):
            direction = "rx" if m.group(2) == b"term" else "tx"
            data = bytes.fromhex(m.group(3).decode())
            ts = _seconds(m.group(1), now)
            last = chunks[-1] if chunks else None
            if last and last.direction == direction and last.ts == ts and len(last.data) < 64:
                last.data += data  # ser2net writes 8 bytes a line; join them back up
            else:
                chunks.append(Chunk(ts, direction, data))
        elif m := MARK.match(line):
            text = m.group(3).decode(errors="replace").strip()
            chunks.append(Chunk(_seconds(m.group(1), now), m.group(2).decode().lower(), b"", text))
    return chunks


class TraceTail:
    """Reads what ser2net appended to one trace file since the last call."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.offset = 0
        self.partial = b""

    def read(self, now: float | None = None) -> list[Chunk]:
        try:
            fd = os.open(self.path, os.O_RDWR)
        except FileNotFoundError:
            return []
        try:
            size = os.fstat(fd).st_size
            if size < self.offset:  # started over
                self.offset, self.partial = 0, b""
            os.lseek(fd, self.offset, os.SEEK_SET)
            data = os.read(fd, READ_MAX)
            self.offset += len(data)
            if not punch_hole(fd, self.offset - self.offset % 4096) and size > FALLBACK_LIMIT:
                os.ftruncate(fd, 0)  # loses what ser2net writes in this very moment
                self.offset = 0
        finally:
            os.close(fd)
        lines = (self.partial + data).split(b"\n")
        self.partial = lines.pop()
        return parse_lines(lines, time.time() if now is None else now)


def recording_stem(name: str) -> str:
    """The connection's part of a file name: "pump-20261109-104012.log" → "pump".

    Also "pump.log.1" of older versions and "pump-capture-20261109-104012.jsonl"."""
    base = re.split(r"\.(?:log|jsonl)", name)[0]
    return re.sub(r"-(?:capture-)?\d{8}-\d{6}(?:-\d+)?$", "", base)


class Recorder:
    """Writes the chunks of one connection to files in the config folder.

    A file is named after the moment it began and keeps that name; when it is full the next one
    begins. The newest is the running one, and files of older versions count as the oldest."""

    def __init__(
        self,
        directory: Path,
        name: str,
        *,
        max_bytes: int,
        keep: int,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.directory = directory
        self.name = name
        self.max_bytes = max_bytes
        self.keep = keep
        self.clock = clock
        self._mine = re.compile(re.escape(name) + r"(?:-\d{8}-\d{6}\.log|\.log(?:\.\d+)?)")

    def files(self) -> list[Path]:
        """This connection's recordings, oldest first."""
        found = [p for p in self.directory.iterdir() if self._mine.fullmatch(p.name)]
        return sorted(found, key=lambda p: (p.stat().st_mtime, p.name))

    def _new_file(self) -> Path:
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(self.clock()))
        return self.directory / f"{self.name}-{stamp}.log"

    def write(self, chunks: list[Chunk], mode: str, *, fresh: bool = False) -> bool:
        """fresh: the recording was just switched on, so it begins a file of its own.
        False when none of the chunks is recorded in this mode."""
        wanted = {"rx": {"rx"}, "tx": {"tx"}, "both": {"rx", "tx"}}.get(mode, set())
        lines = [
            c.line() for c in chunks if c.direction in wanted or c.direction in ("open", "close")
        ]
        if not lines:
            return False
        self.directory.mkdir(parents=True, exist_ok=True)
        files = self.files()
        target = files[-1] if files and files[-1].name.endswith(".log") else None
        if target is not None and target.name == f"{self.name}.log":
            target = None  # of an older version: when it began is not known
        if fresh or target is None or target.stat().st_size >= self.max_bytes:
            target = self._new_file()
        with target.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        for old in self.files()[: -(self.keep + 1)]:
            old.unlink(missing_ok=True)
        return True


@dataclass
class Flow:
    """What went through a connection, as the trace shows it."""

    rx_bytes: int = 0
    tx_bytes: int = 0
    last_rx: float = 0.0
    last_tx: float = 0.0
    seq: int = 0


class TraceHub:
    """All connections' traces: live lines, byte counts and the recordings."""

    def __init__(self, record_dir: Path = RECORD_DIR, shm_dir: Path = SHM_DIR) -> None:
        self.record_dir = record_dir
        self.shm_dir = shm_dir
        self.tails: dict[str, TraceTail] = {}
        self.live: dict[str, deque[Chunk]] = {}
        self.flow: dict[str, Flow] = {}
        self.fed: dict[str, list[Chunk]] = {}  # from the Modbus proxy, until the next poll
        self._not_recorded: set[str] = set()  # recordings that failed (the thread's own)
        self._switched_off: set[str] = set()  # the next recording begins a file (the thread's own)

    def prepare(self) -> None:
        self.shm_dir.mkdir(parents=True, exist_ok=True)

    def feed(self, alias: str, chunk: Chunk) -> None:
        pending = self.fed.setdefault(alias, [])
        if len(pending) < LIVE_LINES * 10:
            pending.append(chunk)

    async def poll(
        self, aliases: dict[str, tuple[str, str]], max_bytes: int, keep: int
    ) -> dict[str, list[Chunk]]:
        """Read all traces. aliases: alias → (file name for recordings, trace mode).

        The files are read and the recordings written in a thread; everything the rest of
        the app reads (live lines, flows) is only touched here in the event loop."""
        jobs: list[tuple[str, str, str, TraceTail | None, list[Chunk]]] = []
        for alias, (file_name, mode) in aliases.items():
            if alias in self.fed:
                jobs.append((alias, file_name, mode, None, self.fed.pop(alias)))
            else:
                tail = self.tails.setdefault(alias, TraceTail(self.shm_dir / f"{alias}.trace"))
                jobs.append((alias, file_name, mode, tail, []))
        read = await asyncio.to_thread(self._read, jobs, max_bytes, keep)
        new: dict[str, list[Chunk]] = {}
        for alias, chunks in read:
            flow = self.flow.setdefault(alias, Flow())
            for c in chunks:
                flow.seq += 1
                c.seq = flow.seq
                if c.direction == "rx":
                    flow.rx_bytes += len(c.data)
                    flow.last_rx = c.ts
                elif c.direction == "tx":
                    flow.tx_bytes += len(c.data)
                    flow.last_tx = c.ts
            self.live.setdefault(alias, deque(maxlen=LIVE_LINES)).extend(chunks)
            new[alias] = chunks
        for alias in {*self.tails, *self.live, *self.fed}:
            if alias not in aliases:
                self.tails.pop(alias, None)
                self.live.pop(alias, None)
                self.fed.pop(alias, None)
        return new

    def _read(
        self,
        jobs: list[tuple[str, str, str, TraceTail | None, list[Chunk]]],
        max_bytes: int,
        keep: int,
    ) -> list[tuple[str, list[Chunk]]]:
        """The thread's part: file reads and recordings, nothing shared with the loop."""
        result: list[tuple[str, list[Chunk]]] = []
        for alias, file_name, mode, tail, chunks in jobs:
            if mode == "off":
                self._switched_off.add(alias)
            if tail is not None:
                try:
                    chunks = tail.read()
                except OSError as err:
                    _LOGGER.debug("Trace of %s not read: %s", alias, err)
                    continue
            if not chunks:
                continue
            if mode != "off":
                recorder = Recorder(self.record_dir, file_name, max_bytes=max_bytes, keep=keep)
                try:
                    if recorder.write(chunks, mode, fresh=alias in self._switched_off):
                        self._switched_off.discard(alias)
                    self._not_recorded.discard(alias)
                except OSError as err:  # e.g. a full disk: the live view goes on
                    if alias not in self._not_recorded:
                        self._not_recorded.add(alias)
                        _LOGGER.warning("Recording of %s not written: %s", file_name, err)
            result.append((alias, chunks))
        return result

    def files(self) -> list[dict[str, object]]:
        if not self.record_dir.is_dir():
            return []
        return [
            {"name": p.name, "size": p.stat().st_size, "modified": p.stat().st_mtime}
            for p in sorted(self.record_dir.iterdir())
            if p.is_file() and (".log" in p.name or p.name.endswith(".jsonl"))
        ]
