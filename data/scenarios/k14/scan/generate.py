"""Make a reproducible English and digit OCR fixture using the standard library."""

from __future__ import annotations

import random
import struct
import zlib
from pathlib import Path

_REFERENCE = "TOTAL 1250"
_GLYPHS = {
    "T": (31, 4, 4, 4, 4, 4, 4),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "A": (14, 17, 17, 31, 17, 17, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31),
    "5": (31, 16, 16, 30, 1, 17, 14),
    "0": (14, 17, 19, 21, 25, 17, 14),
    " ": (0,) * 7,
}


def _chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def synthetic_png(seed: int = 14) -> bytes:
    zoom, left, top = 4, 14, 16
    width = 6 * zoom * len(_REFERENCE) + 2 * left
    height = 70
    randomizer = random.Random(seed)  # nosec B311  # noqa: S311
    data = bytearray([255]) * (width * height)
    for index, letter in enumerate(_REFERENCE):
        for row, bits in enumerate(_GLYPHS[letter]):
            for bit in range(5):
                if not bits & (1 << (4 - bit)):
                    continue
                column = left + zoom * (6 * index + bit)
                start = top + zoom * row + column // 35
                for y in range(start, start + zoom):
                    offset = y * width + column
                    data[offset : offset + zoom] = b"\0" * zoom
    for _ in range(width * height // 180):
        data[randomizer.randrange(len(data))] = randomizer.choice((30, 130, 210, 255))
    scanlines = b"".join(b"\0" + data[n : n + width] for n in range(0, len(data), width))
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(scanlines, level=9))
        + _chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    Path(__file__).with_name("english.png").write_bytes(synthetic_png())
