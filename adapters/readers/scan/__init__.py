"""Optional, digest-pinned OCR integration."""

from __future__ import annotations

import asyncio
import hashlib
import json
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

from adapters.readers.sandbox import MAX_INPUT, ReaderLimits, run_worker
from kernel.intake import ReadResult, TextSegment


@dataclass(frozen=True)
class PinnedFile:
    path: Path
    sha256: str

    def verified_bytes(self, limit: int) -> bytes:
        with self.path.open("rb") as stream:
            value = stream.read(limit + 1)
        if len(value) > limit or hashlib.sha256(value).hexdigest() != self.sha256:
            raise ValueError("OCR_FILE_UNVERIFIED")
        return value


@dataclass(frozen=True)
class ScanConfiguration:
    executable: PinnedFile
    english: PinnedFile
    arabic: PinnedFile
    version: str


class _OCRLine(TypedDict):
    page: int
    text: str
    confidence: float
    box: tuple[int, int, int, int]


class ScanReader:
    def __init__(self, config: ScanConfiguration | None = None):
        self._config = config

    async def read(self, payload: bytes, media_type: str) -> ReadResult:
        if self._config is None:
            return ReadResult(media_type, reason="TEXT_UNAVAILABLE")
        if len(payload) > MAX_INPUT:
            return ReadResult(media_type, reason="READER_SIZE_LIMIT")
        if payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 24:
            width, height = struct.unpack(">II", payload[16:24])
            if not width or not height or width * height > 25_000_000:
                return ReadResult(media_type, reason="READER_SIZE_LIMIT")
        try:
            data = await asyncio.to_thread(_read, self._config, payload)
            if data.get("reason"):
                return ReadResult(media_type, reason=str(data["reason"]))
            segments = tuple(
                TextSegment(
                    page=row["page"],
                    text=row["text"],
                    origin="OCR",
                    confidence=row["confidence"],
                    box=(row["box"][0], row["box"][1], row["box"][2], row["box"][3]),
                )
                for row in cast("list[_OCRLine]", data["segments"])
            )
            return ReadResult(media_type, segments, reason=None if segments else "TEXT_UNAVAILABLE")
        except OSError, ValueError, TypeError, KeyError:
            return ReadResult(media_type, reason="TEXT_UNAVAILABLE")


def _read(config: ScanConfiguration, payload: bytes) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="intake-ocr-") as directory:
        root = Path(directory)
        program = root / "ocr"
        program.write_bytes(config.executable.verified_bytes(64 * 1024 * 1024))
        program.chmod(0o500)
        for language, pin in (("eng", config.english), ("ara", config.arabic)):
            (root / f"{language}.traineddata").write_bytes(pin.verified_bytes(64 * 1024 * 1024))
        raw = run_worker(
            payload, ("OCR", str(program), config.version), ReaderLimits(seconds=12, cpu_seconds=8)
        )
        result: dict[str, object] = json.loads(raw)
        return result
