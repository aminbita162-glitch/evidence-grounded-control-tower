"""Document persistence, parser containment and optional OCR."""

from __future__ import annotations

import asyncio
import hashlib
import io
import os
import sys
import zipfile
from pathlib import Path
from typing import TypedDict

import pytest

from adapters.postgres.tenant_context import TenantContext
from adapters.readers import SandboxedReader
from adapters.readers.sandbox import MAX_INPUT, ReaderLimits
from adapters.readers.scan import PinnedFile, ScanConfiguration, ScanReader
from kernel.intake import IntakeStage, ReaderMetadata, ReadResult, TextSegment
from kernel.ledger.chain import InMemoryCaseChain
from kernel.ledger.records import Actor
from kernel.persistence.repositories.in_memory import InMemoryRepository

pytestmark = pytest.mark.fast
_ACTOR = Actor("ROLE", "operator")


class _DocumentArgs(TypedDict):
    payload: bytes
    filename: str
    document_type: str
    created_at: str


class FixtureReader:
    async def read(self, payload: bytes, media_type: str) -> ReadResult:
        return ReadResult(
            media_type,
            (TextSegment(0, payload.decode()),),
            ReaderMetadata("synthetic producer", revisions=2),
        )


# id: T-INT-0001
# title: Document roundtrip and tenant isolation
# purpose: Verify document roundtrip and tenant isolation.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0001_document_roundtrip_and_tenant_isolation() -> None:
    async def run() -> None:
        stage = IntakeStage(FixtureReader(), InMemoryRepository(), InMemoryRepository())
        tenant = TenantContext("SYN-ONE", "operator")
        other = TenantContext("SYN-TWO", "operator")
        chain = InMemoryCaseChain(tenant.tenant_id, "SYN-CASE")
        payload = "وزن ١٢٥٠ كغ".encode()
        kwargs: _DocumentArgs = {
            "payload": payload,
            "filename": "manifest.txt",
            "document_type": "PACKING_LIST",
            "created_at": "2026-11",
        }
        document = await stage.ingest(tenant, chain, _ACTOR, **kwargs)
        duplicate = await stage.ingest(tenant, chain, _ACTOR, **kwargs)
        digest = hashlib.sha256(payload).hexdigest()
        assert await stage.original(tenant, digest) == payload
        assert await stage.original(other, digest) is None
        assert len(await stage.documents(tenant, chain.case_id)) == 1
        assert await stage.documents(other, chain.case_id) == ()
        assert duplicate.duplicate
        assert document.reading.segments[0].text == payload.decode()
        assert document.comparison_segments == ("وزن 1250 كغ",)
        assert document.reading.metadata.revisions == 2
        assert chain.length == 2
        with pytest.raises(ValueError, match="INTAKE_TENANT_MISMATCH"):
            await stage.ingest(other, chain, _ACTOR, **kwargs)

    asyncio.run(run())


# id: T-INT-0021
# title: Reader refuses unusable payload
# purpose: Verify reader refuses unusable payload.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
@pytest.mark.parametrize(
    ("payload", "mime", "reason"),
    [
        (b"\x89PNG\r\n\x1a\n", "image/scan", "TEXT_UNAVAILABLE"),
        (b"0" * (MAX_INPUT + 1), "text/plain", "READER_SIZE_LIMIT"),
        (b"not a valid PDF", "application/pdf", "READER_REFUSED"),
        (b"invalid \xff text", "text/plain", "READER_REFUSED"),
        (b"\x00\x00", "text/plain", "READER_REFUSED"),
        (b'"unterminated', "text/csv", "READER_REFUSED"),
    ],
)
def test_T_INT_0021_reader_refuses_unusable_payload(
    payload: bytes,
    mime: str,
    reason: str,
) -> None:
    result = asyncio.run(SandboxedReader().read(payload, mime))
    assert result.reason == reason
    assert result.segments == ()


# id: T-INT-0022
# title: Rejects unsafe archive
# purpose: Verify rejects unsafe archive.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
@pytest.mark.parametrize(
    ("name", "data"),
    [
        ("../outside.txt", b"synthetic"),
        ("/absolute.xml", b"<synthetic/>"),
        ("word/vbaProject.bin", b"synthetic"),
        ("word/document.xml", b"<a>" * 65 + b"</a>" * 65),
        ("word/_rels/document.xml.rels", b'<Relationship TargetMode="External"/>'),
        ("word/document.xml", b"<a/>" + b" " * (2 * 1024 * 1024)),
        ("word/document.xml", b"<synthetic>"),
    ],
)
def test_T_INT_0022_rejects_unsafe_archive(
    name: str,
    data: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from adapters.readers.sandbox.worker import _check_container

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, data)
    with pytest.raises((ValueError, SyntaxError)):
        _check_container(buffer.getvalue())


# id: T-INT-0023
# title: Reader crash is contained
# purpose: Verify reader crash is contained.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0023_reader_crash_is_contained() -> None:
    reader = SandboxedReader(ReaderLimits(seconds=0, cpu_seconds=1))
    assert asyncio.run(reader.read(b"Invoice", "text/plain")).reason == "READER_REFUSED"


# id: T-INT-0024
# title: Network denied in worker
# purpose: Verify network denied in worker.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0024_network_denied_in_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    if sys.platform != "linux":
        # Exercise the worker's platform-specific production policy in its Linux job.
        return
    from subprocess import run

    probe = """import socket
from adapters.readers.sandbox.worker import _restrict
_restrict(3, 512 * 1024 * 1024)
try:
    socket.socket()
except PermissionError:
    raise SystemExit(0)
raise SystemExit(1)
"""
    result = run([sys.executable, "-c", probe], capture_output=True, check=False, timeout=5)
    assert result.returncode == 0, result.stderr.decode()


# id: T-INT-0061
# title: Disabled and tampered ocr
# purpose: Verify disabled and tampered ocr.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0061_disabled_and_tampered_ocr(tmp_path: Path) -> None:
    payload = b"\x89PNG\r\n\x1a\n"
    assert asyncio.run(ScanReader().read(payload, "image/scan")).reason == "TEXT_UNAVAILABLE"
    artifact = tmp_path / "fixture"
    artifact.write_bytes(b"synthetic")
    valid = PinnedFile(artifact, hashlib.sha256(b"synthetic").hexdigest())
    wrong = PinnedFile(artifact, hashlib.sha256(b"tampered").hexdigest())
    for config in (
        ScanConfiguration(wrong, valid, valid, "fixture"),
        ScanConfiguration(valid, wrong, valid, "fixture"),
        ScanConfiguration(valid, valid, wrong, "fixture"),
    ):
        assert asyncio.run(ScanReader(config).read(payload, "image/scan")).reason == (
            "TEXT_UNAVAILABLE"
        )
    assert os.stat(artifact).st_mode & 0o111 == 0


# id: T-INT-0062
# title: Oversized scan is refused before ocr
# purpose: Verify oversized scan is refused before ocr.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0062_oversized_scan_is_refused_before_ocr(tmp_path: Path) -> None:
    pin = PinnedFile(tmp_path / "unavailable", "0" * 64)
    reader = ScanReader(ScanConfiguration(pin, pin, pin, "fixture"))
    payload = b"\x89PNG\r\n\x1a\n" + b"\0" * 8 + (100_000).to_bytes(4, "big") * 2
    result = asyncio.run(reader.read(payload, "image/scan"))
    assert result.reason == "READER_SIZE_LIMIT"


# id: T-INT-0010
# title: Parse supported formats
# purpose: Verify parse supported formats.
# level: fast
# requirement: PR-02 PR-11
# input: Synthetic document fixture.
# expected: The bounded reader and stable metadata match the format contract.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
@pytest.mark.parametrize("kind", ("txt", "csv", "docx", "xlsx", "pdf"))
def test_T_INT_0010_parse_supported_formats(kind: str) -> None:
    if sys.platform != "linux":
        return
    from docx import Document as WordDocument
    from openpyxl import Workbook  # type: ignore[import-untyped]
    from pypdf import PdfWriter

    buffer = io.BytesIO()
    expected = "Invoice"
    if kind == "docx":
        word = WordDocument()
        word.core_properties.last_modified_by = "SYNTHETIC"
        word.add_paragraph(expected)
        word.save(buffer)
    elif kind == "xlsx":
        spreadsheet = Workbook()
        sheet = spreadsheet.active
        assert sheet is not None
        sheet.append([expected, "1250"])
        spreadsheet.save(buffer)
    elif kind == "pdf":
        pdf = PdfWriter()
        pdf.add_blank_page(width=200, height=200)
        pdf.add_metadata({"/Producer": "SYNTHETIC"})
        pdf.write(buffer)
    else:
        buffer.write(b"Invoice,1250")
    from kernel.intake import detect_media_type

    raw = buffer.getvalue()
    result = asyncio.run(SandboxedReader().read(raw, detect_media_type(raw, f"fixture.{kind}")))
    if kind == "pdf":
        assert result.reason == "TEXT_UNAVAILABLE"
        assert result.metadata.producer == "SYNTHETIC"
    else:
        assert result.reason is None
        assert result.segments[0].text.startswith(expected)


# id: T-INT-0063
# title: Scan fixture has stable bytes
# purpose: Verify scan fixture has stable bytes.
# level: fast
# requirement: PR-02 PR-11
# input: Synthetic document fixture.
# expected: The bounded reader and stable metadata match the format contract.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0063_scan_fixture_has_stable_bytes() -> None:
    import importlib
    import json

    from kernel.intake import detect_media_type

    source = importlib.import_module("data.scenarios.k14.scan.generate")
    assert source.__file__ is not None
    directory = Path(source.__file__).parent
    fixture = directory / "english.png"
    reference = json.loads((directory / "reference.json").read_text())
    raw = fixture.read_bytes()
    assert detect_media_type(raw, fixture.name) == "image/scan"
    assert raw == source.synthetic_png(reference["seed"])
    assert reference["label"] == "SYNTHETIC"
