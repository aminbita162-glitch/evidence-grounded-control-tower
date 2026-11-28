"""Evaluate verified document facts and request canonical shipment facts."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Literal, Protocol

import yaml

from kernel.hashing import domain_hash
from kernel.lib.text import comparison_form

type Outcome = Literal["ALLOW", "ABSTAIN", "HOLD", "ESCALATE"]
_OUTCOMES: tuple[Outcome, ...] = ("ALLOW", "ABSTAIN", "HOLD", "ESCALATE")
_LABELS = {"OFFICIAL", "DERIVED"}
_SUFFIXES = ("limited", "ltd", "llc", "inc", "gmbh", "ذ م م")
_SOURCE_ID = "SRC-ISO-6346-CHECK-DIGIT"
_MASS = {"g": Decimal("0.001"), "kg": Decimal(1), "t": Decimal(1000)}


@dataclass(frozen=True)
class Fact:
    fact_id: str
    document_id: str
    document_type: str
    field: str
    value: str
    original: str
    locator: str
    status: str = "VERIFIED"
    label: str = "SYNTHETIC"
    unit: str | None = None
    scale: int | None = None
    currency: str | None = None


@dataclass(frozen=True)
class Interval:
    low: Decimal
    high: Decimal

    def overlaps(self, other: Interval) -> bool:
        return max(self.low, other.low) <= min(self.high, other.high)

    def as_value(self) -> tuple[str, str]:
        return format(self.low, "f"), format(self.high, "f")


@dataclass(frozen=True)
class Agreement:
    field: str
    comparator: str
    mismatch: str
    minimum_documents: int = 2


_AGREEMENTS = (
    Agreement("seller_name", "NAME", "PARTY"),
    Agreement("buyer_name", "NAME", "PARTY"),
    Agreement("consignee_name", "NAME", "PARTY"),
    Agreement("goods_description", "TOKENS", "DESCRIPTION"),
    Agreement("total_quantity", "QUANTITY", "QUANTITY"),
    Agreement("package_count", "COUNT", "QUANTITY"),
    Agreement("gross_weight", "QUANTITY", "WEIGHT"),
    Agreement("net_weight", "QUANTITY", "WEIGHT"),
    Agreement("invoice_total", "MONEY", "VALUE"),
    Agreement("currency", "EXACT", "CURRENCY"),
    Agreement("incoterm", "EXACT", "TERMS"),
    Agreement("port_of_loading", "EXACT", "ROUTE"),
    Agreement("port_of_discharge", "EXACT", "ROUTE"),
    Agreement("container_numbers", "SET", "IDENTIFIER"),
    Agreement("transport_document_number", "EXACT", "IDENTIFIER"),
    Agreement("invoice_number", "EXACT", "IDENTIFIER"),
    Agreement("declared_classification_code", "PREFIX", "CLASSIFICATION"),
    Agreement("shipped_on_board_date", "DATE", "DATE"),
)


@dataclass(frozen=True)
class Workflow:
    required_document_types: frozenset[str] = frozenset()
    required_fields: frozenset[str] = frozenset()
    agreements: tuple[Agreement, ...] = _AGREEMENTS
    confirmed_name_links: frozenset[frozenset[str]] = frozenset()
    quantity_tolerance: Decimal = Decimal(0)
    description_lower: Decimal = Decimal("0.6")
    description_upper: Decimal = Decimal("0.9")
    currency_precision: tuple[tuple[str, int], ...] = ()
    container_rule_verified: bool = False
    allowed_labels: frozenset[str] = frozenset(_LABELS)


@dataclass(frozen=True)
class Finding:
    finding_id: str
    reason_code: str
    outcome: Outcome
    facts: tuple[Fact, ...]
    explanation: str
    core: tuple[str, ...] = ()


@dataclass(frozen=True)
class Edge:
    kind: str
    rule: str
    facts: tuple[str, ...]


@dataclass(frozen=True)
class CanonicalFact:
    key: str
    value: str | tuple[str, ...]
    source_fact_ids: tuple[str, ...]
    unit: str | None = None
    status: str = "VERIFIED"
    label: str = "DERIVED"


class CanonicalWriter(Protocol):
    async def write(self, case_id: str, fact: CanonicalFact) -> None: ...


@dataclass(frozen=True)
class ConsistencyReport:
    case_id: str
    evaluation_time: str
    configuration_hash: str
    nodes: tuple[str, ...]
    edges: tuple[Edge, ...]
    findings: tuple[Finding, ...]
    checked: tuple[str, ...]
    not_evaluable: tuple[str, ...]
    canonical: tuple[CanonicalFact, ...]
    outcome: Outcome
    reason_codes: tuple[str, ...]
    counts: tuple[tuple[str, int], ...]
    pack_version: str = "1.0.0"

    @property
    def output_hash(self) -> str:
        return domain_hash("ctc/payload/v1", asdict(self))

    async def publish(self, writer: CanonicalWriter) -> None:
        for fact in self.canonical:
            await writer.write(self.case_id, fact)


def container_rule_verified(registry_path: Path) -> bool:
    entries = yaml.safe_load(registry_path.read_text(encoding="utf-8"))["sources"]
    return any(
        row.get("source_id") == _SOURCE_ID
        and row.get("status") == "VERIFIED"
        and row.get("label") == "DERIVED"
        for row in entries
    )


def valid_container(value: str) -> bool:
    value = comparison_form(value).replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{3}[UJZ][0-9]{7}", value, re.ASCII):
        return False
    numeric = ord("0")
    total = 0
    for index, char in enumerate(value[:-1]):
        if index >= 4:
            code = ord(char) - numeric
        else:
            code = ord(char) - ord("A") + 10
            code += (code - 1) // 10
        total += code * (2**index)
    return (total % 11) % 10 == int(value[-1])


def quantity(
    fact: Fact, *, tolerance: Decimal = Decimal(0), exact: bool = False
) -> tuple[str | None, Interval]:
    if not re.fullmatch(r"[+-]?[0-9]{1,32}(?:\.[0-9]{1,20})?", fact.value):
        raise ValueError("INVALID_DECIMAL")
    if not exact and (fact.scale is None or not 0 <= fact.scale <= 20):
        raise ValueError("MISSING_DECIMAL_PRECISION")
    value = Decimal(fact.value)
    factor = _MASS.get(fact.unit or "", Decimal(1))
    unit = "kg" if fact.unit in _MASS else fact.unit
    half = Decimal(0) if exact else Decimal(5).scaleb(-int(fact.scale or 0) - 1)
    return unit, Interval((value - half) * factor - tolerance, (value + half) * factor + tolerance)


def decimal_amount(fact: Fact) -> Decimal:
    if not re.fullmatch(r"[+-]?[0-9]{1,32}(?:\.[0-9]{1,20})?", fact.value):
        raise ValueError("INVALID_DECIMAL")
    return Decimal(fact.value)


def _normalized_name(value: str) -> str:
    value = comparison_form(value).rstrip(".")
    for suffix in _SUFFIXES:
        if value.endswith(" " + suffix):
            return value.removesuffix(" " + suffix)
    return value


def _identifiers(value: str) -> tuple[str, ...]:
    return tuple(sorted({comparison_form(piece) for piece in value.split(",") if piece.strip()}))


def _compare(
    agreement: Agreement,
    facts: Sequence[Fact],
    workflow: Workflow,
) -> tuple[str, str | tuple[str, ...], str | None]:
    values = tuple(comparison_form(fact.value) for fact in facts)
    comparator = agreement.comparator
    if comparator in {"QUANTITY", "COUNT"}:
        ranges = [
            quantity(fact, tolerance=workflow.quantity_tolerance, exact=comparator == "COUNT")
            for fact in facts
        ]
        unit, _ = ranges[0]
        low = max(interval.low for _, interval in ranges)
        high = min(interval.high for _, interval in ranges)
        ok = all(other_unit == unit for other_unit, _ in ranges) and low <= high
        return ("agree" if ok else "disagree"), Interval(low, high).as_value(), unit
    if comparator == "MONEY":
        from capabilities.f01.arithmetic import money_minor

        currencies = dict(workflow.currency_precision)
        if any(fact.currency not in currencies for fact in facts):
            raise ValueError("CURRENCY_PRECISION_UNAVAILABLE")
        amounts = {(fact.currency, money_minor(fact, currencies)) for fact in facts}
        currency = facts[0].currency
        return ("agree" if len(amounts) == 1 else "disagree"), values[0], currency
    if comparator == "PREFIX":
        shortest = min(values, key=len)
        return (
            ("agree" if all(v.startswith(shortest) for v in values) else "disagree"),
            shortest,
            None,
        )
    if comparator == "SET":
        sets = tuple(_identifiers(fact.value) for fact in facts)
        return ("agree" if len(set(sets)) == 1 else "disagree"), sets[0], None
    if comparator == "NAME":
        equal = all(
            _normalized_name(left) == _normalized_name(right)
            or frozenset((left, right)) in workflow.confirmed_name_links
            for left in values
            for right in values
        )
        return ("agree" if equal else "disagree"), _normalized_name(values[0]), None
    if comparator == "TOKENS":
        sets_of_tokens = tuple(set(value.split()) for value in values)
        similarity = min(
            Decimal(len(a & b)) / max(1, len(a | b)) for a in sets_of_tokens for b in sets_of_tokens
        )
        if similarity < workflow.description_lower:
            return "disagree", values[0], None
        return (
            ("informational" if similarity < workflow.description_upper else "agree"),
            values[0],
            None,
        )
    if comparator not in {"EXACT", "DATE"}:
        raise ValueError("UNKNOWN_COMPARATOR")
    return ("agree" if len(set(values)) == 1 else "disagree"), values[0], None


def _finding(
    code: str,
    outcome: Outcome,
    facts: Sequence[Fact],
    explanation: str,
    core: tuple[str, ...] = (),
) -> Finding:
    facts = tuple(sorted(facts, key=lambda fact: fact.fact_id))
    code = f"F01.{code}"
    identifier = domain_hash("ctc/payload/v1", [code, explanation, [f.fact_id for f in facts]])
    return Finding(identifier, code, outcome, facts, explanation, core)


def evaluate(
    case_id: str,
    facts: Sequence[Fact],
    document_types: Sequence[str],
    workflow: Workflow,
    *,
    evaluation_time: str = "",
    configuration_hash: str = "",
) -> ConsistencyReport:
    from capabilities.f01.arithmetic import arithmetic_findings

    selected = sorted(facts, key=lambda fact: (fact.document_id, fact.field, fact.fact_id))
    by_field: dict[str, list[Fact]] = {}
    for fact in selected:
        by_field.setdefault(fact.field, []).append(fact)
    findings = []
    edges = []
    canonical = []
    checked = []
    skipped = []
    missing = sorted(workflow.required_document_types.difference(document_types))
    if missing:
        findings.append(
            _finding(
                "ABSTAIN.DOC_NOT_PRESENT",
                "ABSTAIN",
                (),
                "Required documents absent: " + ", ".join(missing),
            )
        )
    with localcontext() as ctx:
        ctx.prec = 120
        for rule in workflow.agreements:
            given = by_field.get(rule.field, [])
            group = [f for f in given if f.status == "VERIFIED"]
            by_document: dict[str, set[tuple[str, str | None]]] = {}
            for fact in group:
                by_document.setdefault(fact.document_id, set()).add((fact.value, fact.unit))
            if any(len(values) > 1 for values in by_document.values()):
                findings.append(
                    _finding(
                        "FACT.CONFLICTED",
                        "ESCALATE",
                        group,
                        f"Conflicting values for {rule.field} in one document.",
                    )
                )
                continue
            if len(by_document) < rule.minimum_documents:
                skipped.append(rule.field)
                if rule.field in workflow.required_fields:
                    code = "FACT_NOT_VERIFIED" if len(given) > len(group) else "MISSING_COUNTERPART"
                    findings.append(
                        _finding(
                            f"ABSTAIN.{code}",
                            "ABSTAIN",
                            group,
                            f"Comparable evidence is missing for {rule.field}.",
                        )
                    )
                continue
            if len(given) > len(group) and rule.field in workflow.required_fields:
                findings.append(
                    _finding(
                        "ABSTAIN.FACT_NOT_VERIFIED",
                        "ABSTAIN",
                        group,
                        f"Some needed evidence for {rule.field} is unverified.",
                    )
                )
                continue
            try:
                verdict, value, unit = _compare(rule, group, workflow)
            except ValueError, InvalidOperation:
                skipped.append(rule.field)
                findings.append(
                    _finding(
                        "ABSTAIN.FACT_NOT_VERIFIED",
                        "ABSTAIN",
                        group,
                        f"Values for {rule.field} cannot be compared.",
                    )
                )
                continue
            checked.append(rule.field)
            ids = tuple(sorted(f.fact_id for f in group))
            if verdict == "disagree":
                edges.append(Edge("CONTRADICTS", rule.field, ids))
                findings.append(
                    _finding(
                        f"MISMATCH.{rule.mismatch}",
                        "ESCALATE",
                        group,
                        f"Document values disagree on {rule.field}.",
                    )
                )
            elif verdict == "agree":
                edges.append(Edge("AGREES", rule.field, ids))
                if not missing and all(f.label in workflow.allowed_labels for f in group):
                    canonical.append(CanonicalFact(f"shipment.{rule.field}", value, ids, unit))
                elif any(f.label not in workflow.allowed_labels for f in group):
                    findings.append(
                        _finding(
                            "ABSTAIN.LABEL_INSUFFICIENT",
                            "ABSTAIN",
                            group,
                            f"Evidence labels are insufficient for {rule.field}.",
                        )
                    )

        for fact in by_field.get("container_numbers", []):
            if fact.status != "VERIFIED":
                continue
            if not workflow.container_rule_verified:
                findings.append(
                    _finding(
                        "ABSTAIN.RULE_UNAVAILABLE",
                        "ABSTAIN",
                        [fact],
                        "The container check-digit source is unavailable.",
                    )
                )
            elif any(not valid_container(value) for value in _identifiers(fact.value)):
                findings.append(
                    _finding(
                        "ID.CHECK_DIGIT",
                        "HOLD",
                        [fact],
                        "A cited container number fails its check digit.",
                    )
                )
        for finding, edge in arithmetic_findings(selected, workflow):
            if finding:
                findings.append(finding)
            edges.append(edge)
    if not findings:
        findings.append(_finding("OK.ALL_AGREE", "ALLOW", (), "Evaluated checks agree."))
    reasons = tuple(sorted({f.reason_code for f in findings}))
    outcome = max((f.outcome for f in findings), key=_OUTCOMES.index)
    invalid = {
        f.fact_id
        for finding in findings
        if finding.outcome in {"HOLD", "ESCALATE"}
        for f in finding.facts
    }
    canonical = [f for f in canonical if not invalid.intersection(f.source_fact_ids)]
    return ConsistencyReport(
        case_id,
        evaluation_time,
        configuration_hash,
        tuple(sorted({fid for edge in edges for fid in edge.facts})),
        tuple(edges),
        tuple(findings),
        tuple(checked),
        tuple(skipped),
        tuple(canonical),
        outcome,
        reasons,
        tuple(sorted(Counter(f.outcome for f in findings).items())),
    )


def evaluation_record(report: ConsistencyReport, facts: Sequence[Fact]) -> Mapping[str, object]:
    ordered = sorted(facts, key=lambda f: f.fact_id)
    return {
        "input_hash": domain_hash("ctc/payload/v1", [asdict(f) for f in ordered]),
        "output_hash": report.output_hash,
        "configuration_hash": report.configuration_hash,
        "evaluation_time": report.evaluation_time,
        "capability_version": "1.0.0",
        "pack_version": report.pack_version,
    }
