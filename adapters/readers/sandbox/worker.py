"""Quarantined worker for text-bearing document formats."""

from __future__ import annotations

import csv
import ctypes
import errno
import io
import json
import resource
import sys
import zipfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import IO

from lxml import etree  # type: ignore[import-untyped]

from adapters.readers.sandbox import MAX_INPUT, MAX_OUTPUT
from kernel.intake import ReaderMetadata, TextSegment

_MAX_ENTRIES = 2048
_MAX_EXPANDED = 48 * 1024 * 1024
_MAX_SEGMENTS = 8192
_MAX_XML_DEPTH = 64
_MAX_CELLS = 150_000


def _restrict(cpu: int, memory: int) -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT, MAX_OUTPUT))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    if sys.platform == "darwin":
        resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))
        return  # The parent starts the worker inside a network-denying seatbelt profile.
    if not sys.platform.startswith("linux"):
        raise ValueError("SANDBOX_UNAVAILABLE")
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    seccomp = ctypes.CDLL("libseccomp.so.2")
    seccomp.seccomp_init.argtypes = [ctypes.c_uint32]
    seccomp.seccomp_init.restype = ctypes.c_void_p
    seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    seccomp.seccomp_rule_add.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
    seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
    policy = seccomp.seccomp_init(0x7FFF0000)
    if not policy:
        raise ValueError("SANDBOX_UNAVAILABLE")
    try:
        blocked = 0x00050000 | errno.EPERM
        for name in (
            b"socket",
            b"socketpair",
            b"socketcall",
            b"connect",
            b"bind",
            b"io_uring_setup",
        ):
            syscall = seccomp.seccomp_syscall_resolve_name(name)
            if syscall >= 0 and seccomp.seccomp_rule_add(policy, blocked, syscall, 0) != 0:
                raise ValueError("SANDBOX_UNAVAILABLE")
        if seccomp.seccomp_load(policy) != 0:
            raise ValueError("SANDBOX_UNAVAILABLE")
    finally:
        seccomp.seccomp_release(policy)


def _xml(file: IO[bytes]) -> None:
    raw = file.read()
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower() or b"\0" in raw:
        raise ValueError("XML_DECLARATION_REFUSED")
    depth = 0
    events = etree.iterparse(
        io.BytesIO(raw),
        events=("start", "end"),
        no_network=True,
        resolve_entities=False,
        load_dtd=False,
        huge_tree=False,
    )
    for event, element in events:
        if event == "start":
            depth += 1
            if depth > _MAX_XML_DEPTH:
                raise ValueError("XML_DEPTH_LIMIT")
            if element.attrib.get("TargetMode", "").casefold() == "external":
                raise ValueError("EXTERNAL_RELATIONSHIP")
        else:
            depth -= 1
            element.clear()


def _check_container(payload: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = archive.infolist()
        if len(members) > _MAX_ENTRIES or sum(e.file_size for e in members) > _MAX_EXPANDED:
            raise ValueError("ZIP_EXPANSION_LIMIT")
        paths: set[str] = set()
        for entry in members:
            name = entry.filename.casefold()
            if (
                not name
                or name in paths
                or PurePosixPath(name).is_absolute()
                or ".." in PurePosixPath(name).parts
                or "\\" in name
                or ":" in name
                or (entry.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise ValueError("ZIP_PATH_REFUSED")
            paths.add(name)
            if entry.file_size > 1024 * 1024 and entry.file_size > 200 * entry.compress_size:
                raise ValueError("ZIP_EXPANSION_LIMIT")
            if any(marker in name for marker in ("vbaproject", "/activex/", "/embeddings/")):
                raise ValueError("ACTIVE_CONTENT")
            if name.endswith((".xml", ".rels")):
                with archive.open(entry) as member:
                    _xml(member)


def _date(value: object) -> str | None:
    return str(value) if value else None


def _pdf(payload: bytes) -> tuple[list[TextSegment], ReaderMetadata]:
    from pypdf import PdfReader

    document = PdfReader(io.BytesIO(payload), strict=True)
    if document.is_encrypted or len(document.pages) > _MAX_SEGMENTS:
        raise ValueError("PDF_REFUSED")
    root = document.root_object
    if any(key in root for key in ("/OpenAction", "/AA", "/AcroForm", "/Names")):
        raise ValueError("ACTIVE_CONTENT")
    metadata = document.metadata
    properties = ReaderMetadata(
        producer=metadata.producer if metadata else None,
        created_at=_date(metadata.creation_date) if metadata else None,
        modified_at=_date(metadata.modification_date) if metadata else None,
    )
    pages = []
    for index, page in enumerate(document.pages):
        if "/AA" in page or "/Annots" in page:
            raise ValueError("ACTIVE_CONTENT")
        text = page.extract_text()
        if text.strip():
            pages.append(TextSegment(index, text))
    return pages, properties


def _office(payload: bytes, media: str) -> tuple[list[TextSegment], ReaderMetadata]:
    _check_container(payload)
    if media.endswith("wordprocessingml.document"):
        from docx import Document

        document = Document(io.BytesIO(payload))
        core = document.core_properties
        paragraphs = [p.text for p in document.paragraphs]
        paragraphs.extend(
            "\t".join(cell.text for cell in row.cells)
            for table in document.tables
            for row in table.rows
        )
        return [TextSegment(0, "\n".join(paragraphs))], ReaderMetadata(
            core.last_modified_by or None,
            _date(core.created),
            _date(core.modified),
            core.revision,
        )
    from openpyxl import load_workbook  # type: ignore[import-untyped]

    workbook = load_workbook(io.BytesIO(payload), read_only=True, data_only=True, keep_links=False)
    try:
        pages = []
        remaining = _MAX_CELLS
        for index, sheet in enumerate(workbook.worksheets):
            rows = []
            for row in sheet.iter_rows(values_only=True):
                remaining -= len(row)
                if remaining < 0:
                    raise ValueError("SPREADSHEET_SIZE_LIMIT")
                rows.append("\t".join("" if cell is None else str(cell) for cell in row))
            pages.append(TextSegment(index, "\n".join(rows)))
        core = workbook.properties
        return pages, ReaderMetadata(
            core.lastModifiedBy,
            _date(core.created),
            _date(core.modified),
            int(core.revision) if core.revision and core.revision.isdecimal() else None,
        )
    finally:
        workbook.close()


def _read(payload: bytes, media: str) -> tuple[list[TextSegment], ReaderMetadata]:
    if media == "application/pdf":
        return _pdf(payload)
    if media.startswith("application/vnd.openxmlformats-officedocument."):
        return _office(payload, media)
    if media not in {"text/plain", "text/csv"}:
        raise ValueError("UNSUPPORTED_MEDIA")
    text = payload.decode("utf-8-sig", errors="strict")
    if "\0" in text:
        raise ValueError("INVALID_TEXT")
    if media == "text/csv":
        text = "\n".join("\t".join(row) for row in csv.reader(io.StringIO(text), strict=True))
    return [TextSegment(0, text)], ReaderMetadata()


def main() -> None:
    from dataclasses import asdict

    try:
        _restrict(int(sys.argv[1]), int(sys.argv[2]))
        payload = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(payload) > MAX_INPUT:
            raise ValueError("READER_SIZE_LIMIT")
        result: Mapping[str, object]
        if sys.argv[3] == "OCR":
            from adapters.readers.scan.worker import extract

            result = extract(payload, Path(sys.argv[4]), sys.argv[5])
        else:
            segments, metadata = _read(payload, sys.argv[3])
            pages = [asdict(item) for item in segments if item.text.strip()]
            if len(pages) > _MAX_SEGMENTS:
                raise ValueError("READER_OUTPUT_LIMIT")
            result = {
                "segments": pages,
                "metadata": asdict(metadata),
                "reason": None if pages else "TEXT_UNAVAILABLE",
            }
        encoded = json.dumps(result, ensure_ascii=False).encode()
        if len(encoded) > MAX_OUTPUT:
            raise ValueError("READER_OUTPUT_LIMIT")
        sys.stdout.buffer.write(encoded)
    except Exception:
        # The worker may encounter parser messages containing document data.
        # Report only a stable refusal at the trusted boundary.
        sys.stdout.write('{"reason":"READER_REFUSED"}')


if __name__ == "__main__":
    main()
