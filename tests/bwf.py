"""Splice a bext chunk (EBU Tech 3285 v2) into a WAV written by soundfile, for metadata tests."""

from __future__ import annotations

import struct
from pathlib import Path


def bext_chunk(loudness_value: int = 0x7FFF, loudness_range: int = 0x7FFF, max_true_peak: int = 0x7FFF, description: str = "cumple test", originator: str = "cumple") -> bytes:
    def fixed(s: str, n: int) -> bytes:
        return s.encode("ascii")[:n].ljust(n, b"\x00")

    body = (
        fixed(description, 256) + fixed(originator, 32) + fixed("cumple-test", 32) + fixed("2026-09-04", 10) + fixed("12:00:00", 8)
        + struct.pack("<II", 0, 0) + struct.pack("<H", 2) + b"\x00" * 64
        + struct.pack("<hhhhh", loudness_value, loudness_range, max_true_peak, 0x7FFF, 0x7FFF)
        + b"\x00" * 180
        + b"A=PCM,F=48000,W=24,M=stereo,T=cumple\r\n"
    )
    if len(body) % 2:
        body += b"\x00"
    return b"bext" + struct.pack("<I", len(body)) + body


def add_bext(path: Path, **kwargs) -> Path:
    """Insert a bext chunk after the fmt chunk and fix the RIFF size. Modifies the file in place."""
    data = bytearray(path.read_bytes())
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE"
    pos = 12
    insert_at = None
    while pos + 8 <= len(data):
        cid = bytes(data[pos : pos + 4])
        size = struct.unpack("<I", data[pos + 4 : pos + 8])[0]
        nxt = pos + 8 + size + (size % 2)
        if cid == b"fmt ":
            insert_at = nxt
            break
        pos = nxt
    assert insert_at is not None
    chunk = bext_chunk(**kwargs)
    data[insert_at:insert_at] = chunk
    struct.pack_into("<I", data, 4, len(data) - 8)
    path.write_bytes(bytes(data))
    return path
