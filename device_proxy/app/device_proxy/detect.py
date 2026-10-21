"""Finds a meter's baud rate and format by listening at each one in turn.

Only while ser2net has let go of the device (the connection is switched off in ser2net for
the test, its clients are disconnected). The device is opened read-only in effect: nothing is
sent, so it works for meters that push their data (SML, D0 in push mode).
"""

from __future__ import annotations

import os
import select
import termios
import time
from collections.abc import Callable
from dataclasses import dataclass

from .meter import analyze, score

BAUDS = (9600, 19200, 2400, 4800, 1200, 300, 38400, 57600, 115200)
FORMATS = ((8, "n", 1), (7, "e", 1), (8, "e", 1))
LISTEN_SECONDS = 2.5


@dataclass
class Candidate:
    baud: int
    data_bits: int
    parity: str
    stop_bits: int
    score: float
    protocol: str
    bytes: int

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def configure(fd: int, baud: int, data_bits: int, parity: str, stop_bits: int) -> None:
    attrs = termios.tcgetattr(fd)
    speed = getattr(termios, f"B{baud}")
    attrs[0] = termios.IGNBRK  # iflag: raw, no flow control
    attrs[1] = 0  # oflag
    cflag = (
        termios.CREAD
        | termios.CLOCAL
        | {5: termios.CS5, 6: termios.CS6, 7: termios.CS7}.get(data_bits, termios.CS8)
    )
    if parity in ("e", "o"):
        cflag |= termios.PARENB | (termios.PARODD if parity == "o" else 0)
    if stop_bits == 2:
        cflag |= termios.CSTOPB
    attrs[2] = cflag
    attrs[3] = 0  # lflag
    attrs[4] = attrs[5] = speed
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIFLUSH)


def listen(fd: int, seconds: float) -> bytes:
    data = b""
    end = time.monotonic() + seconds
    while (left := end - time.monotonic()) > 0:
        ready, _, _ = select.select([fd], [], [], left)
        if ready:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            data += chunk
    return data


def detect(
    device: str, progress: Callable[[int, int, Candidate], None] | None = None
) -> list[Candidate]:
    """Every speed and format, best first. Raises OSError when the device cannot be opened."""
    fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    found: list[Candidate] = []
    try:
        steps = [(b, f) for b in BAUDS for f in FORMATS]
        for index, (baud, (data_bits, parity, stop_bits)) in enumerate(steps):
            configure(fd, baud, data_bits, parity, stop_bits)
            data = listen(fd, LISTEN_SECONDS)
            candidate = Candidate(
                baud,
                data_bits,
                parity,
                stop_bits,
                round(score(data), 3),
                analyze(data).protocol,
                len(data),
            )
            found.append(candidate)
            if progress is not None:
                progress(index + 1, len(steps), candidate)
            if candidate.score >= 0.95:  # clean telegrams: no need to go on
                break
    finally:
        os.close(fd)
    return sorted(found, key=lambda c: c.score, reverse=True)
