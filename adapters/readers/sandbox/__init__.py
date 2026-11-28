"""Resource-bounded subprocess transport for untrusted documents."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess  # nosec B404
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from kernel.intake import DocumentReader, ReaderMetadata, ReadResult, TextSegment

MAX_INPUT = 16 * 1024 * 1024
MAX_OUTPUT = 4 * 1024 * 1024
_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ReaderLimits:
    seconds: int = 8
    cpu_seconds: int = 4
    memory_bytes: int = 512 * 1024 * 1024


def run_worker(payload: bytes, arguments: tuple[str, ...], limits: ReaderLimits) -> bytes:
    """Run the fixed reader worker with separated stdin and bounded output."""
    command = [
        sys.executable,
        "-m",
        "adapters.readers.sandbox.worker",
        str(limits.cpu_seconds),
        str(limits.memory_bytes),
        *arguments,
    ]
    if sys.platform == "darwin":
        command[:0] = ["/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)"]
    with (
        tempfile.TemporaryDirectory(prefix="intake-") as work,
        tempfile.TemporaryFile(dir=work) as output,
    ):
        env = {"HOME": work, "TMPDIR": work, "PATH": os.defpath, "LANG": "C.UTF-8"}
        with subprocess.Popen(  # nosec B603  # noqa: S603
            command,
            cwd=_ROOT,
            env=env,
            stdin=subprocess.PIPE,
            stdout=output,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        ) as process:
            try:
                process.communicate(payload, timeout=limits.seconds)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise ValueError("READER_TIMEOUT") from None
            if process.returncode:
                raise ValueError("READER_FAILED")
        output.seek(0)
        result = output.read(MAX_OUTPUT + 1)
    if len(result) > MAX_OUTPUT:
        raise ValueError("READER_OUTPUT_LIMIT")
    return result


class SandboxedReader:
    def __init__(self, limits: ReaderLimits | None = None, scan: DocumentReader | None = None):
        self._limits = limits or ReaderLimits()
        self._scan = scan

    async def read(self, payload: bytes, media_type: str) -> ReadResult:
        if len(payload) > MAX_INPUT:
            return ReadResult(media_type, reason="READER_SIZE_LIMIT")
        if media_type == "image/scan":
            if self._scan is not None:
                return await self._scan.read(payload, media_type)
            return ReadResult(media_type, reason="TEXT_UNAVAILABLE")
        try:
            raw = await asyncio.to_thread(run_worker, payload, (media_type,), self._limits)
            data = json.loads(raw)
            metadata = ReaderMetadata(**data.get("metadata", {}))
            segments = tuple(TextSegment(**segment) for segment in data.get("segments", []))
            reason = cast("str | None", data.get("reason"))
        except OSError, ValueError, TypeError:
            return ReadResult(media_type, reason="READER_REFUSED")
        return ReadResult(media_type, segments, metadata, reason)
