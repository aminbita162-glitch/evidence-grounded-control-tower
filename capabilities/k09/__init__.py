"""Tenant-scoped document fingerprints and symmetric duplicate findings."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from typing import Literal

from kernel.hashing import domain_hash
from kernel.intake import IntakeDocument
from kernel.lib.text import comparison_form

type RelationKind = Literal["SUPERSEDES", "AMENDS", "SPLIT_OF", "SAME_CONSIGNMENT"]
type Outcome = Literal["ALLOW", "ABSTAIN", "HOLD", "ESCALATE"]
_OUTCOMES: tuple[Outcome, ...] = ("ALLOW", "ABSTAIN", "HOLD", "ESCALATE")
MAX_CANDIDATES = 1000
VERSION = "1.0.0"
_BAND_WIDTH = 4
_MAX_TOKENS = 32_768
_SEEDS = tuple(i.to_bytes(2, "big") for i in range(128))
_CONFUSABLES = str.maketrans("аеорсхукіјвмнт", "aeopcyxkijbmht")
_IDENTITY = {
    "COMMERCIAL_INVOICE": ("seller_name", "invoice_number"),
    "TRANSPORT_DOCUMENT": ("issuer", "transport_document_number"),
    "PACKING_LIST": ("issuer", "packing_list_number"),
    "ORIGIN_CERTIFICATE": ("issuer", "certificate_number"),
    "DELIVERY_ORDER": ("issuer", "delivery_order_number"),
    "INSURANCE_CERTIFICATE": ("issuer", "certificate_number"),
    "DECLARATION_DRAFT": ("issuer", "declaration_number"),
}


@dataclass(frozen=True)
class IdentityFact:
    field: str
    value: str
    status: str


@dataclass(frozen=True)
class Fingerprint:
    tenant_id: str
    case_id: str
    document_id: str
    document_type: str
    content_hash: str
    text_hash: str | None
    signature: tuple[int, ...]
    shingles: frozenset[str]
    identity_hash: str | None
    identity_complete: bool
    facts: tuple[tuple[str, str], ...]
    producer: str | None
    signals: tuple[str, ...]
    duplicate: bool = False
    text_index_complete: bool = True


def _timestamp(text: str | None) -> datetime | None:
    if text:
        try:
            value = datetime.fromisoformat(text)
            return value if value.tzinfo else None
        except ValueError:
            pass
    return None


def fingerprint(
    document: IntakeDocument,
    facts: Sequence[IdentityFact],
    *,
    max_revisions: int = 1,
) -> Fingerprint:
    text = comparison_form(" ".join(s.text for s in document.reading.segments))
    tokens = text.split(maxsplit=_MAX_TOKENS)
    complete_text = len(tokens) <= _MAX_TOKENS
    if not complete_text:
        tokens = []
    shingles = frozenset(" ".join(tokens[i : i + 5]) for i in range(len(tokens) - 4))
    # Hash each shingle to a fixed-length commitment before it can reach persistence.
    hashed = frozenset(hashlib.sha256(s.encode()).hexdigest() for s in shingles)
    key_fields = _IDENTITY.get(document.document_type, ())
    groups: dict[str, set[str]] = defaultdict(set)
    for fact in facts:
        if fact.status == "VERIFIED" and fact.value:
            groups[fact.field].add(fact.value)
    values = {field: next(iter(group)) for field, group in groups.items() if len(group) == 1}
    complete = all(field in values for field in key_fields)
    identity = (
        [comparison_form(values[k]).translate(_CONFUSABLES) for k in key_fields]
        if key_fields and complete
        else None
    )
    signature = (
        tuple(
            min(
                int.from_bytes(
                    hashlib.blake2b(bytes.fromhex(shingle), key=seed, digest_size=8).digest()
                )
                for shingle in hashed
            )
            for seed in _SEEDS
        )
        if hashed
        else ()
    )
    metadata = document.reading.metadata
    modified, issue = _timestamp(metadata.modified_at), _timestamp(values.get("issue_date"))
    signals = []
    if modified and issue and modified > issue:
        signals.append("MODIFIED_AFTER_ISSUE")
    if metadata.revisions is not None and metadata.revisions > max_revisions:
        signals.append("REVISION_COUNT")
    return Fingerprint(
        document.record.tenant_id,
        document.case_id,
        document.record.document_id,
        document.document_type,
        document.record.sha256,
        hashlib.sha256(text.encode()).hexdigest() if text else None,
        signature,
        hashed,
        domain_hash("ctc/payload/v1", [document.document_type, identity]) if identity else None,
        complete,
        tuple(sorted(values.items())),
        metadata.producer,
        tuple(signals),
        document.duplicate,
        complete_text,
    )


@dataclass(frozen=True)
class Relation:
    left_document: str
    right_document: str
    kind: RelationKind
    approval_id: str

    @property
    def pair(self) -> frozenset[str]:
        return frozenset((self.left_document, self.right_document))


@dataclass(frozen=True)
class Finding:
    reason_code: str
    outcome: Outcome
    document_id: str
    other_document_id: str | None = None
    other_case_id: str | None = None
    differences: tuple[tuple[str, str | None, str | None], ...] = ()
    similarity: str | None = None


@dataclass(frozen=True)
class Coverage:
    document_id: str
    checks: tuple[str, ...]
    skipped: tuple[str, ...] = ()


@dataclass(frozen=True)
class DocumentShieldReport:
    case_id: str
    findings: tuple[Finding, ...]
    observations: tuple[tuple[str, str], ...]
    coverage: tuple[Coverage, ...]
    outcome: Outcome
    reason_codes: tuple[str, ...]
    index_version: str = VERSION

    @property
    def output_hash(self) -> str:
        return domain_hash("ctc/payload/v1", asdict(self))

    def view(self, readable_cases: frozenset[str], *, reviewer: bool) -> DocumentShieldReport:
        safe = []
        for finding in self.findings:
            changed = finding
            if finding.other_case_id is not None and finding.other_case_id not in readable_cases:
                changed = replace(
                    changed,
                    other_document_id=None,
                    other_case_id="another case of this tenant",
                    differences=tuple(
                        (field, left, None) for field, left, _ in changed.differences
                    ),
                )
            if not reviewer:
                changed = replace(changed, similarity=None)
            safe.append(changed)
        return replace(self, findings=tuple(safe))


def _keys(fact: Fingerprint) -> Sequence[tuple[str, object]]:
    keys: list[tuple[str, object]] = [("content", fact.content_hash)]
    if fact.text_hash:
        keys.append(("text", fact.text_hash))
    if fact.identity_hash:
        keys.append(("identity", fact.identity_hash))
    for index in range(0, len(fact.signature), _BAND_WIDTH):
        keys.append(("band", (index, fact.signature[index : index + _BAND_WIDTH])))
    # A deterministic prefix index supplements probabilistic bands. Any sets with
    # Jaccard >= 0.8 share a token in these prefixes under a common global order.
    if fact.shingles:
        prefix = len(fact.shingles) - (4 * len(fact.shingles) + 4) // 5 + 1
        keys.extend(("prefix", item) for item in sorted(fact.shingles)[:prefix])
    issuer = dict(fact.facts).get("seller_name") or dict(fact.facts).get("issuer")
    if issuer and fact.producer:
        keys.append(("producer", comparison_form(issuer)))
    return keys


class FingerprintIndex:
    """Tenant-partitioned in-memory implementation with no global index state."""

    def __init__(self) -> None:
        self._documents: dict[str, dict[str, Fingerprint]] = defaultdict(dict)
        self._buckets: dict[str, dict[tuple[str, object], set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self._relations: dict[str, dict[frozenset[str], set[RelationKind]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self._reports: dict[tuple[str, str], DocumentShieldReport] = {}
        self._stale: set[tuple[str, str]] = set()
        self._closed: set[tuple[str, str]] = set()
        self.available = True

    def upsert(self, value: Fingerprint) -> None:
        old = self._documents[value.tenant_id].get(value.document_id)
        if old is not None:
            self._remove_buckets(old)
        self._documents[value.tenant_id][value.document_id] = value
        for key in _keys(value):
            self._buckets[value.tenant_id][key].add(value.document_id)
        self._stale.add((value.tenant_id, value.case_id))

    def _remove_buckets(self, value: Fingerprint) -> None:
        buckets = self._buckets[value.tenant_id]
        for key in _keys(value):
            bucket = buckets[key]
            bucket.remove(value.document_id)
            if not bucket:
                del buckets[key]

    def result(self, tenant_id: str, case_id: str) -> DocumentShieldReport | None:
        key = (tenant_id, case_id)
        return None if key in self._stale else self._reports.get(key)

    def erase(self, tenant_id: str, document_id: str) -> None:
        old = self._documents[tenant_id].pop(document_id, None)
        if old is None:
            return
        self._remove_buckets(old)
        for pair in tuple(self._relations[tenant_id]):
            if document_id in pair:
                del self._relations[tenant_id][pair]
        for key, report in self._reports.items():
            if key[0] != tenant_id:
                continue
            if key[1] == old.case_id or any(
                f.other_document_id == document_id for f in report.findings
            ):
                self._stale.add(key)
        for key in self._stale:
            if key[0] == tenant_id:
                self._reports.pop(key, None)

    def declare(self, tenant_id: str, relation: Relation) -> None:
        if (
            len(relation.pair) != 2
            or not relation.approval_id
            or not relation.pair <= self._documents[tenant_id].keys()
        ):
            raise ValueError("VERIFIED_RELATION_REQUIRED")
        self._relations[tenant_id][relation.pair].add(relation.kind)
        for document in relation.pair:
            self._stale.add((tenant_id, self._documents[tenant_id][document].case_id))

    def mark_closed(self, tenant_id: str, case_id: str) -> None:
        self._closed.add((tenant_id, case_id))

    def is_stale(self, tenant_id: str, case_id: str) -> bool:
        return (tenant_id, case_id) in self._stale

    def recompute_stale(self, tenant_id: str) -> None:
        for tenant, case in sorted(self._stale - self._closed):
            if tenant == tenant_id:
                self.evaluate(tenant, case, recompute=False)

    def _candidates(self, source: Fingerprint) -> list[Fingerprint] | None:
        matches: set[str] = set()
        for key in _keys(source):
            if key[0] == "producer":
                continue
            for document_id in self._buckets[source.tenant_id].get(key, ()):
                if document_id != source.document_id:
                    matches.add(document_id)
                    if len(matches) > MAX_CANDIDATES:
                        return None
        return [self._documents[source.tenant_id][key] for key in sorted(matches)]

    def _signals(self, source: Fingerprint) -> tuple[str, ...]:
        for key in _keys(source):
            if key[0] == "producer" and any(
                self._documents[source.tenant_id][other].producer != source.producer
                for other in self._buckets[source.tenant_id][key]
            ):
                return (*source.signals, "PRODUCER_CHANGED")
        return source.signals

    def evaluate(
        self, tenant_id: str, case_id: str, *, pack_available: bool = True, recompute: bool = True
    ) -> DocumentShieldReport:
        key = (tenant_id, case_id)
        documents = sorted(
            (s for s in self._documents[tenant_id].values() if s.case_id == case_id),
            key=lambda item: item.document_id,
        )
        findings: list[Finding] = []
        obs: set[tuple[str, str]] = set()
        coverage: list[Coverage] = []
        linked: set[str] = set()
        if not pack_available:
            findings.append(Finding("K09.ABSTAIN.PACK_UNAVAILABLE", "ABSTAIN", ""))
        elif not self.available:
            findings.append(Finding("K09.ABSTAIN.INDEX_UNAVAILABLE", "ABSTAIN", ""))
        else:
            for src in documents:
                self._check_document(src, findings, obs, coverage, linked)
        reasons = tuple(sorted({f.reason_code for f in findings} | {code for _, code in obs}))
        if not findings:
            reasons = tuple(sorted((*reasons, "K09.OK.NO_FINDING")))
        outcome: Outcome = max(
            (finding.outcome for finding in findings), key=_OUTCOMES.index, default=_OUTCOMES[0]
        )
        report = DocumentShieldReport(
            case_id, tuple(findings), tuple(sorted(obs)), tuple(coverage), outcome, reasons
        )
        old = self._reports.get(key)
        self._reports[key] = report
        self._stale.discard(key)
        if recompute and old != report:
            for other_case in sorted(linked):
                other = (tenant_id, other_case)
                if other not in self._closed:
                    self._stale.add(other)
                    self.evaluate(tenant_id, other_case, recompute=False)
        return report

    def _check_document(
        self,
        src: Fingerprint,
        findings: list[Finding],
        observations: set[tuple[str, str]],
        coverage: list[Coverage],
        linked: set[str],
    ) -> None:
        did = src.document_id
        signals = self._signals(src)
        if src.duplicate:
            observations.add((did, "K09.OBS.SAME_CASE_DUPLICATE"))
        if signals:
            observations.add((did, "K09.OBS.METADATA_SIGNAL"))
        if not src.text_hash:
            observations.add((did, "K09.OBS.TEXT_UNAVAILABLE"))
        if not src.text_index_complete:
            findings.append(Finding("K09.ABSTAIN.INDEX_UNAVAILABLE", "ABSTAIN", did))
        if not src.identity_complete:
            findings.append(Finding("K09.ABSTAIN.IDENTITY_FACT_NOT_VERIFIED", "ABSTAIN", did))
        candidates = self._candidates(src)
        if candidates is None:
            findings.append(Finding("K09.ABSTAIN.CANDIDATE_CAP", "ABSTAIN", did))
            coverage.append(Coverage(did, (), ("CANDIDATE_CAP",)))
            return
        checks = (
            ("CONTENT_HASH", "NORMALIZED_TEXT_HASH", "MINHASH_JACCARD")
            if src.text_hash
            else ("CONTENT_HASH",)
        )
        coverage.append(
            Coverage(
                did,
                checks + (("IDENTITY",) if src.identity_hash else ()),
                () if src.text_hash else ("TEXT_UNAVAILABLE",),
            )
        )
        for other in candidates:
            pair = frozenset((did, other.document_id))
            relations = self._relations[src.tenant_id].get(pair, set())
            same = other.case_id == src.case_id
            exact = src.content_hash == other.content_hash or (
                src.text_hash is not None and src.text_hash == other.text_hash
            )
            related = relations.intersection({"SPLIT_OF", "SAME_CONSIGNMENT"})
            amended = relations.intersection({"SUPERSEDES", "AMENDS"})
            result = []
            if exact and not same:
                if related:
                    observations.add((did, "K09.OBS.RELATION_APPLIED"))
                else:
                    result.append(Finding("K09.REUSE.EXACT_DOCUMENT", "HOLD", did))
            if (
                src.identity_hash
                and src.identity_hash == other.identity_hash
                and (src.content_hash != other.content_hash)
            ):
                if amended:
                    observations.add((did, "K09.OBS.RELATION_APPLIED"))
                else:
                    first, second = dict(src.facts), dict(other.facts)
                    differences = tuple(
                        (name, first.get(name), second.get(name))
                        for name in sorted(first.keys() | second.keys())
                        if first.get(name) != second.get(name)
                    )
                    result.append(
                        Finding(
                            "K09.CONFLICT.IDENTITY_KEY", "ESCALATE", did, differences=differences
                        )
                    )
            if not same and not exact and src.shingles and other.shingles:
                common = len(src.shingles & other.shingles)
                union = len(src.shingles | other.shingles)
                upper = common * 10 >= union * 9
                if upper or common * 5 >= union * 4 and (signals or self._signals(other)):
                    suffix = "NEAR_DUPLICATE" if upper else "CORROBORATED"
                    result.append(
                        Finding(
                            f"K09.SIMILAR.{suffix}", "ESCALATE", did, similarity=f"{common}/{union}"
                        )
                    )
            findings.extend(
                replace(item, other_document_id=other.document_id, other_case_id=other.case_id)
                for item in result
            )
            if result and not same:
                linked.add(other.case_id)


def evidence(
    report: DocumentShieldReport,
    fingerprints: Sequence[Fingerprint],
    configuration_hash: str,
) -> Mapping[str, object]:
    return {
        "document_hashes": sorted(
            f.content_hash for f in fingerprints if f.case_id == report.case_id
        ),
        "configuration_hash": configuration_hash,
        "pack_version": VERSION,
        "index_version": report.index_version,
        "output_hash": report.output_hash,
    }
