"""Tenant-scoped document intake and the boundary for document readers."""

from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass, replace
from typing import Protocol, cast

from adapters.postgres.tenant_context import TenantContext
from kernel.contracts._generated.document import Document
from kernel.ledger.chain import CaseChain
from kernel.ledger.records import Actor
from kernel.persistence.repositories import ConflictError, Repository


@dataclass(frozen=True)
class ReaderMetadata:
    producer: str | None = None
    created_at: str | None = None
    modified_at: str | None = None
    revisions: int | None = None


@dataclass(frozen=True)
class TextSegment:
    page: int
    text: str
    origin: str = "TEXT"
    confidence: float | None = None
    box: tuple[int, int, int, int] | None = None


@dataclass(frozen=True)
class ReadResult:
    media_type: str
    segments: tuple[TextSegment, ...] = ()
    metadata: ReaderMetadata = ReaderMetadata()
    reason: str | None = None


class DocumentReader(Protocol):
    """Read bytes as untrusted data, returning a bounded result or refusal."""

    async def read(self, payload: bytes, media_type: str) -> ReadResult: ...


@dataclass(frozen=True)
class ScriptProfile:
    arabic: int
    latin: int
    other: int

    @property
    def supported(self) -> bool:
        total = self.arabic + self.latin + self.other
        return bool(total and 5 * (self.arabic + self.latin) >= 3 * total)

    @property
    def dominant_language(self) -> str:
        if not self.supported:
            return "und"
        return "ar" if self.arabic > self.latin else "en"

    @property
    def direction(self) -> str:
        return "rtl" if self.arabic > self.latin else "ltr"


def profile(text: str) -> ScriptProfile:
    counts = dict.fromkeys(("ARABIC", "LATIN", "OTHER"), 0)
    for char in text:
        if char.isalpha():
            script = unicodedata.name(char, "").split(" ", 1)[0]
            counts[script if script in counts else "OTHER"] += 1
    return ScriptProfile(counts["ARABIC"], counts["LATIN"], counts["OTHER"])


def detect_media_type(payload: bytes, filename: str) -> str:
    if payload.startswith(b"%PDF-"):
        return "application/pdf"
    if payload.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"II*\x00", b"MM\x00*")):
        return "image/scan"
    extension = filename.rpartition(".")[2].lower()
    return {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "txt": "text/plain",
    }.get(extension, "application/octet-stream")


@dataclass(frozen=True)
class IntakeDocument:
    record: Document
    case_id: str
    document_type: str
    size: int
    reading: ReadResult
    scripts: ScriptProfile
    comparison_segments: tuple[str, ...]
    duplicate: bool = False


class IntakeStage:
    """Read input through injected ports and keep raw payloads out of the ledger."""

    def __init__(
        self, reader: DocumentReader, documents: Repository, originals: Repository
    ) -> None:
        self._reader = reader
        self._documents = documents
        self._originals = originals

    async def ingest(
        self,
        context: TenantContext,
        chain: CaseChain,
        actor: Actor,
        *,
        payload: bytes,
        filename: str,
        document_type: str,
        created_at: str,
    ) -> IntakeDocument:
        from kernel.lib.text import comparison_form

        if chain.tenant_id != context.tenant_id:
            raise ValueError("INTAKE_TENANT_MISMATCH")
        digest = hashlib.sha256(payload).hexdigest()
        document_id = hashlib.sha256(
            "\0".join((context.tenant_id, chain.case_id, digest)).encode()
        ).hexdigest()
        existing = await self._documents.get(context, document_id)
        if existing is not None:
            await chain.append(
                "Intake",
                actor,
                "document_observation",
                {
                    "document_id": document_id,
                    "reason": "SAME_CASE_DUPLICATE",
                },
            )
            return replace(cast("IntakeDocument", existing["document"]), duplicate=True)

        media_type = detect_media_type(payload, filename)
        reading = await self._reader.read(payload, media_type)
        segments = tuple(
            replace(s, text=unicodedata.normalize("NFC", s.text)) for s in reading.segments
        )
        reading = replace(reading, segments=segments)
        scripts = profile("\n".join(s.text for s in segments))
        record = Document(
            document_id=document_id,
            tenant_id=context.tenant_id,
            sha256=digest,
            content_type=media_type,
            created_at=created_at,
            language="ar" if scripts.dominant_language == "ar" else "en",
            schema_version=1,
        )
        document = IntakeDocument(
            record,
            chain.case_id,
            document_type,
            len(payload),
            reading,
            scripts,
            tuple(comparison_form(s.text) for s in segments),
        )
        with suppress(ConflictError):
            await self._originals.insert(context, {"id": digest, "payload": payload})
        try:
            await self._documents.insert(context, {"id": document_id, "document": document})
        except ConflictError:
            return await self.ingest(
                context,
                chain,
                actor,
                payload=payload,
                filename=filename,
                document_type=document_type,
                created_at=created_at,
            )
        await chain.append(
            "Intake",
            actor,
            "document",
            {
                "document_id": document_id,
                "sha256": digest,
                "content_type": media_type,
                "size": len(payload),
                "reason": reading.reason or "TEXT_AVAILABLE",
            },
        )
        return document

    async def original(self, context: TenantContext, digest: str) -> bytes | None:
        entry = await self._originals.get(context, digest)
        return cast("bytes", entry["payload"]) if entry else None

    async def documents(self, context: TenantContext, case_id: str) -> Sequence[IntakeDocument]:
        return tuple(
            doc
            for row in await self._documents.list(context)
            if (doc := cast("IntakeDocument", row["document"])).case_id == case_id
        )

    async def erase(self, context: TenantContext, case_id: str, document_id: str) -> str | None:
        """Erase a case document and an unreferenced original within its tenant."""
        entry = await self._documents.get(context, document_id)
        if entry is None:
            return None
        document = cast("IntakeDocument", entry["document"])
        if document.case_id != case_id:
            return None
        if not await self._documents.delete(context, document_id):
            return None
        digest = document.record.sha256
        others = await self._documents.list(context)
        if not any(
            cast("IntakeDocument", row["document"]).record.sha256 == digest for row in others
        ):
            await self._originals.delete(context, digest)
        return digest
