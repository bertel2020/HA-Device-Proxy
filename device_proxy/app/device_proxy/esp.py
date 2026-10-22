"""EnOcean gateway frames (ESP2, ESP3): split a byte stream into whole frames, and tell
what a frame is as far as the EnOcean proxy (enocean.py) needs it.

The proxy must never interleave two clients' frames on the serial line, and it keeps whole
frames for the replay buffer, so it cuts streams at frame boundaries. It does not decode
the telegrams' contents.

ESP2: sync 0xA5 0x5A, then 12 bytes (header/length, ORG, 4 data, 4 ID, status, checksum).
ESP3: 0x55, data length (2), optional length (1), packet type (1), CRC8 of those four,
data, optional data, CRC8 of data + optional data.
"""

from __future__ import annotations

import time
from collections.abc import Callable

ESP2_FRAME = 14
ESP3_HEADER = 6  # sync + 4 header bytes + header CRC
ESP3_MAX_DATA = 1024  # data + optional data; a longer header is a false sync in garbage
ESP3_STALE = 0.5  # seconds: an unfinished frame older than this was a false sync (ESP3: 100 ms)


def crc8(data: bytes) -> int:
    """CRC8 of ESP3 (polynomial 0x07, initial value 0)."""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


class Splitter:
    """Feed bytes, get complete frames; garbage before a sync byte is dropped."""

    def __init__(self, protocol: str, clock: Callable[[], float] = time.monotonic) -> None:
        if protocol not in ("esp2", "esp3"):
            raise ValueError(f"unknown protocol {protocol!r}")
        self.protocol = protocol
        self._buffer = bytearray()
        self._clock = clock
        self._last = 0.0

    def feed(self, chunk: bytes) -> list[bytes]:
        now = self._clock()
        if self.protocol == "esp3" and self._buffer and now - self._last > ESP3_STALE:
            del self._buffer[:1]  # the frame never finished: look for the next sync
        self._last = now
        self._buffer += chunk
        frames: list[bytes] = []
        while True:
            frame = self._next_esp2() if self.protocol == "esp2" else self._next_esp3()
            if frame is None:
                return frames
            frames.append(frame)

    def _next_esp2(self) -> bytes | None:
        start = self._buffer.find(b"\xa5\x5a")
        if start < 0:
            del self._buffer[: max(0, len(self._buffer) - 1)]  # keep a trailing 0xA5
            return None
        del self._buffer[:start]
        if len(self._buffer) < ESP2_FRAME:
            return None
        frame = bytes(self._buffer[:ESP2_FRAME])
        del self._buffer[:ESP2_FRAME]
        return frame

    def _next_esp3(self) -> bytes | None:
        while True:
            start = self._buffer.find(b"\x55")
            if start < 0:
                self._buffer.clear()
                return None
            del self._buffer[:start]
            if len(self._buffer) < ESP3_HEADER:
                return None
            header = bytes(self._buffer[1:5])
            if crc8(header) != self._buffer[5]:
                del self._buffer[:1]  # a 0x55 inside data: look for the next one
                continue
            data_len = int.from_bytes(header[0:2], "big") + header[2]
            if data_len > ESP3_MAX_DATA:
                del self._buffer[:1]
                continue
            total = ESP3_HEADER + data_len + 1
            if len(self._buffer) < total:
                return None
            if crc8(bytes(self._buffer[ESP3_HEADER : total - 1])) != self._buffer[total - 1]:
                del self._buffer[:1]  # the header CRC matched by chance
                continue
            frame = bytes(self._buffer[:total])
            del self._buffer[:total]
            return frame


# what a frame is

ESP2_RRT, ESP2_TRT, ESP2_RMT, ESP2_TCT = 0b000, 0b011, 0b100, 0b101
ESP2_RADIO_ORGS = {0x05, 0x06, 0x07, 0xD2}  # RPS, 1BS, 4BS, VLD (Eltako)
ESP2_BUS_CONTROL = 0xF0  # ORG from here on: FAM14 bus polling and memory access
ESP3_RADIO_TYPES = {0x01, 0x03, 0x09}  # RADIO_ERP1, RADIO_SUB_TEL, RADIO_MESSAGE
ESP3_RESPONSE = 0x02


def _esp2(frame: bytes) -> tuple[int, int]:
    return frame[2] >> 5, frame[3]  # header sequence, ORG


def is_radio(protocol: str, frame: bytes) -> bool:
    """A telegram worth replaying: a radio telegram or a bus actor's state answer, not
    FAM14 polling, empty answers or gateway messages."""
    if protocol == "esp3":
        return frame[4] in ESP3_RADIO_TYPES
    hseq, org = _esp2(frame)
    return hseq in (ESP2_RRT, ESP2_TRT, ESP2_RMT) and org in ESP2_RADIO_ORGS


def is_response(protocol: str, frame: bytes) -> bool:
    """The gateway's answer to a command (OK, error, base ID ...)."""
    if protocol == "esp3":
        return frame[4] == ESP3_RESPONSE
    hseq, org = _esp2(frame)
    return hseq == ESP2_RMT and org not in ESP2_RADIO_ORGS and org < ESP2_BUS_CONTROL


def expects_response(protocol: str, frame: bytes) -> bool:
    """ESP3 answers every packet; ESP2 answers gateway commands (not radio, not bus)."""
    if protocol == "esp3":
        return True
    hseq, org = _esp2(frame)
    return hseq == ESP2_TCT and org < ESP2_BUS_CONTROL


ESP2_ORG_RORG = {0x05: "RPS", 0x06: "1BS", 0x07: "4BS", 0xD2: "VLD"}
ESP3_RORG = {0xF6: "RPS", 0xD5: "1BS", 0xA5: "4BS", 0xD2: "VLD"}


def radio_info(protocol: str, frame: bytes) -> tuple[str, str] | None:
    """Telegram type (RPS, 1BS, 4BS, VLD) and sender ID ("FF-AA-80-01") of a radio frame,
    for the status page; None for anything else."""
    if not is_radio(protocol, frame):
        return None
    if protocol == "esp3":
        length = int.from_bytes(frame[1:3], "big")
        if frame[4] != 0x01 or length < 6 or len(frame) < 6 + length:
            return None  # only RADIO_ERP1: RORG, data, 4 ID bytes, status
        data = frame[6 : 6 + length]
        return ESP3_RORG.get(data[0], f"{data[0]:02X}"), data[-5:-1].hex("-").upper()
    if len(frame) < 14:
        return None
    return ESP2_ORG_RORG.get(frame[3], f"{frame[3]:02X}"), frame[8:12].hex("-").upper()


def radio_key(protocol: str, frame: bytes) -> bytes | None:
    """What two gateways that heard the same radio telegram have in common: ESP3 its data
    without the optional data (signal strength, subtelegrams), ESP2 ORG, data and sender
    without the status (repeater count). None for anything else."""
    if not is_radio(protocol, frame):
        return None
    if protocol == "esp3":
        length = int.from_bytes(frame[1:3], "big")
        return bytes(frame[4:5]) + frame[6 : 6 + length]
    return frame[3:12] if len(frame) >= 14 else None


# air time (868 MHz duty cycle)

BIT_RATE = 125_000  # bit/s of EnOcean radio
SUBTELEGRAMS = 3  # gateways send every telegram three times
RADIO_OVERHEAD = 6  # bytes around the payload on air: preamble, sync, length, CRC (approx.)
ESP2_DATA_BYTES = {0x05: 1, 0x06: 1, 0x07: 4, 0xD2: 4}  # RPS, 1BS, 4BS, VLD (max)


def airtime_ms(protocol: str, frame: bytes) -> float:
    """Approximate time on air of a radio telegram the gateway sends (0 for other frames).

    Payload = RORG + data + sender ID + status, coded 8 to 12 bits per byte on air, sent as
    three subtelegrams. Accurate enough to watch the 1 % duty cycle, not to bill it.
    """
    if protocol == "esp3":
        if frame[4] != 0x01:  # RADIO_ERP1 only
            return 0.0
        payload = int.from_bytes(frame[1:3], "big")
    else:
        if (frame[2] >> 5) != ESP2_TRT or frame[3] not in ESP2_DATA_BYTES:
            return 0.0
        payload = 1 + ESP2_DATA_BYTES[frame[3]] + 4 + 1
    bits = (payload + RADIO_OVERHEAD) * 12
    return SUBTELEGRAMS * bits * 1000 / BIT_RATE


def base_id_request(protocol: str) -> bytes:
    """A harmless command every gateway answers: read the base ID (used by the gateway test)."""
    if protocol == "esp3":
        header = bytes([0x00, 0x01, 0x00, 0x05])  # 1 data byte, COMMON_COMMAND
        return b"\x55" + header + bytes([crc8(header), 0x08, crc8(b"\x08")])
    body = bytes([0xAB, 0x58]) + bytes(9)  # TCT, RD_IDBASE, 4 data, 4 ID, status
    return b"\xa5\x5a" + body + bytes([sum(body) & 0xFF])


ESP2_INF_IDBASE = 0x98


def is_base_id_request(protocol: str, frame: bytes) -> bool:
    if protocol == "esp3":
        return len(frame) >= 8 and frame[4] == 0x05 and frame[6] == 0x08  # CO_RD_IDBASE
    return len(frame) >= 4 and frame[2] >> 5 == ESP2_TCT and frame[3] == 0x58


def base_id(protocol: str, frame: bytes, request: bytes | None = None) -> str | None:
    """The base ID ("FF-B7-44-80") in a gateway's answer, or None. ESP3 answers carry no
    command, so the request they answer must be given."""
    if protocol == "esp3":
        if request is None or not is_base_id_request(protocol, request) or frame[4] != 0x02:
            return None
        if int.from_bytes(frame[1:3], "big") < 5 or frame[6] != 0x00:  # RET_OK
            return None
        return frame[7:11].hex("-").upper()
    if len(frame) < 14 or frame[2] >> 5 != ESP2_RMT or frame[3] != ESP2_INF_IDBASE:
        return None
    return frame[4:8].hex("-").upper()


def base_id_writes_left(protocol: str, frame: bytes, request: bytes | None) -> int | None:
    """How often the base ID can still be changed, from an ESP3 answer to CO_RD_IDBASE
    (its optional byte); None for ESP2, which does not tell."""
    if protocol != "esp3" or base_id(protocol, frame, request) is None:
        return None
    length = int.from_bytes(frame[1:3], "big")
    return frame[6 + length] if frame[3] >= 1 else None


BASE_ID_FIRST, BASE_ID_LAST = 0xFF800000, 0xFFFFFF80  # the range a gateway takes, in steps of 0x80


def parse_base_id(text: str) -> bytes:
    """ "FF-B7-44-80" (also with ":", spaces or none) → 4 bytes; ValueError if not settable."""
    cleaned = "".join(ch for ch in text if ch not in " :-\t")
    try:
        raw = bytes.fromhex(cleaned)
    except ValueError:
        raise ValueError("base ID: 4 hex bytes like FF-B7-44-80") from None
    if len(raw) != 4:
        raise ValueError("base ID: 4 hex bytes like FF-B7-44-80")
    value = int.from_bytes(raw, "big")
    if not BASE_ID_FIRST <= value <= BASE_ID_LAST or value & 0x7F:
        raise ValueError("base ID: FF-80-00-00 to FF-FF-FF-80, the last byte 00 or 80")
    return raw


def base_id_write_request(protocol: str, raw: bytes) -> bytes:
    """Change the base ID (CO_WR_IDBASE / SET_IDBASE). The gateway keeps it in flash and
    allows it only a few times (10 for TCM 300 modules)."""
    if protocol == "esp3":
        header = bytes([0x00, 0x05, 0x00, 0x05])  # 5 data bytes, COMMON_COMMAND
        data = b"\x07" + raw
        return b"\x55" + header + bytes([crc8(header)]) + data + bytes([crc8(data)])
    body = bytes([0xAB, 0x18]) + raw + bytes(5)  # TCT, SET_IDBASE, 4 data, 4 ID, status
    return b"\xa5\x5a" + body + bytes([sum(body) & 0xFF])


# ESP3 return codes of CO_WR_IDBASE; ESP2 answers OK (ORG 0x58) or an error ORG
ESP3_WRITE_RESULTS = {
    0x00: "ok",
    0x01: "error",
    0x02: "not_supported",
    0x82: "flash_error",
    0x90: "out_of_range",
    0x91: "no_writes_left",
}
ESP2_WRITE_RESULTS = {0x58: "ok", 0x19: "error", 0x1A: "out_of_range"}


def base_id_write_result(protocol: str, frame: bytes | None) -> str:
    """What the gateway said to a base ID change: "ok", "no_writes_left" ... or "no_answer"."""
    if frame is None:
        return "no_answer"
    if protocol == "esp3":
        if frame[4] != ESP3_RESPONSE or len(frame) < 8:
            return "error"
        return ESP3_WRITE_RESULTS.get(frame[6], "error")
    if not is_response(protocol, frame):
        return "error"
    return ESP2_WRITE_RESULTS.get(frame[3], "error")


def describe(protocol: str, frame: bytes) -> str:
    """For the live view: "RPS FE-E9-12-34", "answer", "bus", "command" or ""."""
    if (info := radio_info(protocol, frame)) is not None:
        return f"{info[0]} {info[1]}"
    if is_response(protocol, frame):
        return "answer"
    if protocol == "esp2" and len(frame) > 3 and frame[3] >= ESP2_BUS_CONTROL:
        return "bus"
    if expects_response(protocol, frame) and not (protocol == "esp3" and frame[4] == 0x01):
        return "command"  # to the gateway itself (base ID, settings ...)
    return ""
