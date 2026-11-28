"""Match freight invoice lines to recorded billing bases and audit exact amounts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal
from enum import StrEnum

from kernel.lib.calctrace import (
    Calculation,
    DecimalSettings,
    Formula,
    Operand,
    Operation,
    calculate,
)
from kernel.lib.money import CurrencyTable, Money, RoundAt, RoundingRule, round_at, within_tolerance
from kernel.lib.taxonomy import ChargeName, LineKind, Taxonomy
from kernel.lib.text import comparison_form
from kernel.lib.unblock import Requirement, RequirementKind, open_items, requirements_for
from kernel.types.decision import DecisionValue
from kernel.types.label import is_allow_eligible

_CONTEXT = Context(prec=128)
_SETTINGS = DecimalSettings(128, ROUND_HALF_EVEN)
_ZERO = Decimal(0)
_UNIT_FACTORS = {"kg": Decimal(1), "g": Decimal("0.001"), "t": Decimal(1000)}


class BasisSource(StrEnum):
    QUOTE = "QUOTE"
    TERMS = "TERMS"
    TARIFF = "TARIFF"


class LineClass(StrEnum):
    DUPLICATE = "DUPLICATE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    UNQUOTED = "UNQUOTED"
    AMBIGUOUS = "AMBIGUOUS"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    SURCHARGE_VALIDITY = "SURCHARGE_OUT_OF_VALIDITY"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    RATE_ABOVE_BASIS = "RATE_ABOVE_BASIS"
    ARITHMETIC = "ARITHMETIC"
    FREIGHT_CONFLICT = "FREIGHT_TERMS_CONFLICT"
    MATCH = "MATCH"
    BELOW_BASIS = "BELOW_BASIS"
    TAX = "TAX_EXCLUDED"
    TIME_BASED = "TIME_BASED_MATCHED"
    UNSUPPORTED = "CURRENCY_UNSUPPORTED"
    WEAK_LABEL = "LABEL_INSUFFICIENT"
    UNVERIFIED = "INVOICE_FACT_NOT_VERIFIED"


class Reason(StrEnum):
    MATCH = "L01.OK.MATCH"
    BELOW = "L01.OBS.BELOW_BASIS"
    TAX = "L01.OBS.TAX_EXCLUDED"
    TIME = "L01.OBS.TIME_BASED_MATCHED"
    DUPLICATE = "L01.OVERCHARGE.DUPLICATE"
    RATE = "L01.OVERCHARGE.RATE_ABOVE_BASIS"
    QUANTITY = "L01.OVERCHARGE.QUANTITY"
    ARITHMETIC = "L01.OVERCHARGE.ARITHMETIC"
    SURCHARGE = "L01.OVERCHARGE.SURCHARGE_VALIDITY"
    HEADER = "L01.OVERCHARGE.HEADER_TOTAL"
    CURRENCY = "L01.CURRENCY.MISMATCH"
    POSSIBLE_DUPLICATE = "L01.REVIEW.POSSIBLE_DUPLICATE"
    NO_BASIS = "L01.UNQUOTED.NO_BASIS"
    AMBIGUOUS = "L01.AMBIGUOUS.BASIS"
    FREIGHT = "L01.TERMS.FREIGHT_CONFLICT"
    INVOICE = "L01.ABSTAIN.INVOICE_FACT_NOT_VERIFIED"
    TAXONOMY = "L01.ABSTAIN.TAXONOMY_MISSING"
    PACK = "L01.ABSTAIN.BASIS_PACK_MISSING"
    UNSUPPORTED = "L01.ABSTAIN.CURRENCY_UNSUPPORTED"
    LABEL = "L01.ABSTAIN.LABEL_INSUFFICIENT"


_CODES = {
    LineClass.DUPLICATE: (Reason.DUPLICATE, DecisionValue.HOLD),
    LineClass.POSSIBLE_DUPLICATE: (Reason.POSSIBLE_DUPLICATE, DecisionValue.ESCALATE),
    LineClass.UNQUOTED: (Reason.NO_BASIS, DecisionValue.ESCALATE),
    LineClass.AMBIGUOUS: (Reason.AMBIGUOUS, DecisionValue.ESCALATE),
    LineClass.CURRENCY_MISMATCH: (Reason.CURRENCY, DecisionValue.HOLD),
    LineClass.SURCHARGE_VALIDITY: (Reason.SURCHARGE, DecisionValue.HOLD),
    LineClass.QUANTITY_MISMATCH: (Reason.QUANTITY, DecisionValue.HOLD),
    LineClass.RATE_ABOVE_BASIS: (Reason.RATE, DecisionValue.HOLD),
    LineClass.ARITHMETIC: (Reason.ARITHMETIC, DecisionValue.HOLD),
    LineClass.FREIGHT_CONFLICT: (Reason.FREIGHT, DecisionValue.ESCALATE),
    LineClass.MATCH: (Reason.MATCH, DecisionValue.ALLOW),
    LineClass.BELOW_BASIS: (Reason.BELOW, DecisionValue.ALLOW),
    LineClass.TAX: (Reason.TAX, DecisionValue.ALLOW),
    LineClass.TIME_BASED: (Reason.TIME, DecisionValue.ALLOW),
    LineClass.UNSUPPORTED: (Reason.UNSUPPORTED, DecisionValue.ABSTAIN),
    LineClass.WEAK_LABEL: (Reason.LABEL, DecisionValue.ABSTAIN),
    LineClass.UNVERIFIED: (Reason.INVOICE, DecisionValue.ABSTAIN),
}

_REQUIREMENTS = {
    Reason.DUPLICATE: (RequirementKind.FACT, "invoice line and prior invoice references"),
    Reason.POSSIBLE_DUPLICATE: (RequirementKind.VERIFICATION, "independent charge references"),
    Reason.NO_BASIS: (RequirementKind.PACK, "applicable quotation, contract or tariff"),
    Reason.AMBIGUOUS: (RequirementKind.VERIFICATION, "applicable basis line"),
    Reason.CURRENCY: (RequirementKind.FACT, "verified invoice and basis currency"),
    Reason.SURCHARGE: (RequirementKind.PACK, "surcharge validity"),
    Reason.QUANTITY: (RequirementKind.FACT, "verified shipment quantity"),
    Reason.RATE: (RequirementKind.PACK, "agreed rate and invoice rate evidence"),
    Reason.ARITHMETIC: (RequirementKind.VERIFICATION, "line quantity, rate and amount"),
    Reason.FREIGHT: (RequirementKind.FACT, "verified freight terms and payer"),
    Reason.HEADER: (RequirementKind.VERIFICATION, "header total and invoice lines"),
    Reason.INVOICE: (RequirementKind.FACT, "verified invoice facts"),
    Reason.TAXONOMY: (RequirementKind.PACK, "active charge taxonomy"),
    Reason.PACK: (RequirementKind.PACK, "active charge basis"),
    Reason.UNSUPPORTED: (RequirementKind.PACK, "currency minor-unit table"),
    Reason.LABEL: (RequirementKind.VERIFICATION, "source eligibility"),
}


@dataclass(frozen=True, slots=True)
class Quantity:
    value: Decimal
    unit: str

    def normalized(self) -> tuple[Decimal, str]:
        scale = _UNIT_FACTORS.get(self.unit)
        return (_CONTEXT.multiply(self.value, scale), "kg") if scale else (self.value, self.unit)

    def in_unit(self, unit: str) -> Decimal | None:
        if self.unit == unit:
            return self.value
        if self.unit in _UNIT_FACTORS and unit in _UNIT_FACTORS:
            return _CONTEXT.divide(self.normalized()[0], _UNIT_FACTORS[unit])
        return None


@dataclass(frozen=True, slots=True)
class InvoiceLine:
    id: str
    name: str
    shipment: str
    currency: str
    quantity: Quantity
    rate: Decimal
    amount: Decimal
    citation: str
    tax: bool = False
    verified: bool = True
    service_date: date | None = None
    container: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    freight_conflict: bool = False
    percent_base: Decimal | None = None
    label: str = "DERIVED"

    def __post_init__(self) -> None:
        for value in (self.quantity.value, self.rate, self.amount, self.percent_base):
            if value is not None and (
                not value.is_finite()
                or value < 0
                or len(value.as_tuple().digits) > 50
                or not -30 <= value.adjusted() <= 30
            ):
                raise ValueError(
                    "invoice quantities and amounts must be bounded nonnegative decimals"
                )


@dataclass(frozen=True, slots=True)
class Invoice:
    number: str
    issuer: str
    date: date
    currency: str
    lines: tuple[InvoiceLine, ...]
    label: str
    citation: str
    total: Decimal | None = None
    verified: bool = True

    def __post_init__(self) -> None:
        if not self.number or not self.issuer or not self.citation:
            raise ValueError("an invoice requires an identifier, issuer and citation")
        if len({line.id for line in self.lines}) != len(self.lines):
            raise ValueError("invoice line identifiers must be unique")
        if self.total is not None and not self.total.is_finite():
            raise ValueError("invoice total must be finite")


@dataclass(frozen=True, slots=True)
class Basis:
    id: str
    kind: str
    source: BasisSource
    rate: Decimal
    currency: str
    unit: str
    valid_from: date
    valid_until: date
    citation: str
    label: str
    version: str
    verified: bool = True
    accepted: bool = True
    surcharge: bool = False
    freight: bool = False
    shipment: str | None = None
    rounding: RoundingRule | None = None

    def __post_init__(self) -> None:
        if (
            not self.id
            or not self.version
            or not self.citation
            or self.valid_from >= self.valid_until
            or not self.rate.is_finite()
            or self.rate < 0
            or len(self.rate.as_tuple().digits) > 50
            or not -30 <= self.rate.adjusted() <= 30
        ):
            raise ValueError("invalid invoice charge basis")

    def applies(self, on: date) -> bool:
        return self.valid_from <= on < self.valid_until


@dataclass(frozen=True, slots=True)
class Policy:
    precedence: tuple[int, int, int] = (0, 1, 2)
    near_band: Decimal = Decimal("0.02")
    duplicate_days: int = 30

    def __post_init__(self) -> None:
        if not self.near_band.is_finite() or not _ZERO <= self.near_band <= 1:
            raise ValueError("invalid near-duplicate band")
        if self.duplicate_days < 0:
            raise ValueError("invalid duplicate window")

    def rank(self, source: BasisSource) -> int:
        return self.precedence[tuple(BasisSource).index(source)]


_DEFAULT_POLICY = Policy()


@dataclass(frozen=True, slots=True)
class MatchRecord:
    line_id: str
    kind: str
    basis: Basis | None
    reason: Reason


@dataclass(frozen=True, slots=True)
class AuditedLine:
    line: InvoiceLine
    kind: ChargeName
    classification: LineClass
    reason: Reason
    decision: DecisionValue
    billed: Decimal
    expected: Decimal | None
    trace: dict[str, object] | None
    basis: Basis | None


@dataclass(frozen=True, slots=True)
class CurrencyTotal:
    billed: Decimal
    expected: Decimal | None
    difference: Decimal | None


@dataclass(frozen=True, slots=True)
class HeaderTotal:
    stated: Decimal
    line_sum: Decimal
    matches: bool


@dataclass(frozen=True, slots=True)
class InvoiceAudit:
    outcome: DecisionValue
    lines: tuple[AuditedLine, ...]
    matches: tuple[MatchRecord, ...]
    reason_codes: tuple[Reason, ...]
    totals: dict[str, CurrencyTotal]
    header: HeaderTotal | None
    unblock: tuple[dict[str, object], ...]


def classify_duplicate(
    line: InvoiceLine,
    kind: ChargeName,
    invoice: Invoice,
    taxonomy: Taxonomy,
    previous: tuple[Invoice, ...],
    policy: Policy,
) -> LineClass | None:
    current_key = (kind.code, line.shipment, line.currency)
    others = (
        other
        for bill in (invoice, *previous)
        if bill.verified
        and comparison_form(bill.issuer) == comparison_form(invoice.issuer)
        and abs((invoice.date - bill.date).days) <= policy.duplicate_days
        for other in bill.lines
        if (bill.number != invoice.number or other.id != line.id)
        and other.verified
        and not other.tax
        and (taxonomy.resolve(other.name).code, other.shipment, other.currency) == current_key
    )
    nearby = False
    for other in others:
        if other.amount == line.amount:
            return LineClass.DUPLICATE
        nearby |= bool(policy.near_band) and (
            abs(_CONTEXT.subtract(other.amount, line.amount))
            <= _CONTEXT.multiply(min(other.amount, line.amount), policy.near_band)
        )
    return LineClass.POSSIBLE_DUPLICATE if nearby else None


def select_basis(
    line: InvoiceLine,
    kind: ChargeName,
    at: date,
    bases: tuple[Basis, ...],
    policy: Policy,
) -> tuple[Basis | None, LineClass | None]:
    candidates = [
        basis
        for basis in bases
        if basis.verified
        and (basis.source != BasisSource.QUOTE or basis.accepted)
        and basis.kind == kind.code
        and basis.shipment in (None, line.shipment)
    ]
    valid = [basis for basis in candidates if basis.applies(at)]
    if not valid:
        expired = [basis for basis in candidates if basis.surcharge]
        if expired:
            return min(
                expired, key=lambda basis: (policy.rank(basis.source), basis.id)
            ), LineClass.SURCHARGE_VALIDITY
        return None, LineClass.UNQUOTED
    rank = min(policy.rank(basis.source) for basis in valid)
    selected = sorted(
        (basis for basis in valid if policy.rank(basis.source) == rank), key=lambda basis: basis.id
    )
    if len({(item.rate, item.currency, item.unit, item.rounding) for item in selected}) > 1:
        return None, LineClass.AMBIGUOUS
    return selected[0], None


def _eligible(label: str, synthetic: bool) -> bool:
    return is_allow_eligible(label) or synthetic and label == "SYNTHETIC"


def _equal(a: Decimal, b: Decimal, currency: str, currencies: CurrencyTable) -> bool:
    return within_tolerance(
        Money(a, currency),
        Money(b, currency),
        tolerance_units=0,
        rounding=ROUND_HALF_EVEN,
        currencies=currencies,
        context=_CONTEXT,
    )


def _expected(
    line: InvoiceLine,
    basis: Basis,
    quantity: Decimal,
    currencies: CurrencyTable,
) -> tuple[Decimal, Calculation]:
    trace = calculate(
        Formula("L01.EXPECTED_LINE", 1, Operation.MULTIPLY, basis.citation),
        _SETTINGS,
        Operand(basis.citation, basis.rate, f"{basis.currency}/{basis.unit}", basis.label),
        Operand(line.citation, quantity, basis.unit, line.label),
        unit=basis.currency,
    )
    if basis.rounding is not None and basis.rounding.point == RoundAt.LINE:
        trace = calculate(
            Formula("L01.ROUND_LINE", 1, Operation.QUANTIZE, basis.rounding.source_id),
            DecimalSettings(_SETTINGS.precision, basis.rounding.mode),
            trace,
            Operand(
                currencies.source_id,
                currencies.quantum(basis.currency),
                basis.currency,
                basis.label,
            ),
            unit=basis.currency,
        )
    return trace.result.value, trace


def _row(
    line: InvoiceLine,
    kind: ChargeName,
    code: LineClass,
    basis: Basis | None = None,
    expected: Decimal | None = None,
    trace: Calculation | None = None,
) -> AuditedLine:
    reason, decision = _CODES[code]
    return AuditedLine(
        line,
        kind,
        code,
        reason,
        decision,
        line.amount,
        expected,
        trace.payload() if trace else None,
        basis,
    )


def _audit_basis(
    line: InvoiceLine,
    invoice: Invoice,
    taxonomy: Taxonomy,
    bases: tuple[Basis, ...],
    currencies: CurrencyTable,
    verified_quantities: dict[str, Quantity],
    policy: Policy,
    synthetic: bool,
) -> AuditedLine:
    kind = taxonomy.resolve(line.name, tax=line.tax)
    if not line.verified or not line.id or not line.citation or not line.shipment:
        return _row(line, kind, LineClass.UNVERIFIED)
    if kind.kind == LineKind.TAX:
        return _row(line, kind, LineClass.TAX)
    basis, basis_issue = select_basis(line, kind, line.service_date or invoice.date, bases, policy)
    if basis_issue in (LineClass.UNQUOTED, LineClass.AMBIGUOUS):
        return _row(line, kind, basis_issue)
    if basis is None:
        return _row(line, kind, LineClass.UNQUOTED)
    if line.currency not in currencies.minor_units or basis.currency not in currencies.minor_units:
        return _row(line, kind, LineClass.UNSUPPORTED, basis)
    if line.currency != basis.currency:
        return _row(line, kind, LineClass.CURRENCY_MISMATCH, basis)
    if basis_issue is not None:
        return _row(line, kind, basis_issue, basis)
    if not all(_eligible(label, synthetic) for label in (line.label, basis.label, taxonomy.label)):
        return _row(line, kind, LineClass.WEAK_LABEL, basis)
    if kind.kind == LineKind.TIME_BASED:
        return _row(line, kind, LineClass.TIME_BASED, basis)
    billed_quantity = (
        line.percent_base if basis.unit == "percentage" else line.quantity.in_unit(basis.unit)
    )
    recorded = verified_quantities.get(f"{line.shipment}:{basis.unit}")
    recorded_quantity = recorded.in_unit(basis.unit) if recorded else billed_quantity
    if recorded_quantity is None or billed_quantity is None:
        return _row(line, kind, LineClass.UNVERIFIED, basis)
    expected, trace = _expected(line, basis, recorded_quantity, currencies)
    currency = line.currency
    billed = _CONTEXT.multiply(
        line.rate, line.percent_base if line.percent_base is not None else line.quantity.value
    )
    if basis.rounding is not None:
        billed = round_at(
            Money(billed, currency),
            RoundAt.LINE,
            currencies=currencies,
            context=_CONTEXT,
            rule=basis.rounding,
        ).money.amount
    invoice_rate = line.rate
    if line.quantity.unit in _UNIT_FACTORS and basis.unit in _UNIT_FACTORS:
        invoice_rate = _CONTEXT.divide(
            _CONTEXT.multiply(line.rate, _UNIT_FACTORS[basis.unit]),
            _UNIT_FACTORS[line.quantity.unit],
        )
    if billed_quantity != recorded_quantity:
        code = LineClass.QUANTITY_MISMATCH
    elif invoice_rate > basis.rate and not _equal(invoice_rate, basis.rate, currency, currencies):
        code = LineClass.RATE_ABOVE_BASIS
    elif not _equal(billed, line.amount, currency, currencies):
        code = LineClass.ARITHMETIC
    elif basis.freight and line.freight_conflict:
        code = LineClass.FREIGHT_CONFLICT
    elif _equal(line.amount, expected, currency, currencies):
        code = LineClass.MATCH
    else:
        code = LineClass.BELOW_BASIS
    return _row(line, kind, code, basis, expected, trace)


def _audit_line(
    line: InvoiceLine,
    invoice: Invoice,
    taxonomy: Taxonomy,
    bases: tuple[Basis, ...],
    currencies: CurrencyTable,
    verified_quantities: dict[str, Quantity],
    previous: tuple[Invoice, ...],
    policy: Policy,
    synthetic: bool,
) -> AuditedLine:
    billed = _audit_basis(
        line,
        invoice,
        taxonomy,
        bases,
        currencies,
        verified_quantities,
        policy,
        synthetic,
    )
    if billed.classification in (LineClass.TAX, LineClass.UNVERIFIED):
        return billed
    duplicate = classify_duplicate(line, billed.kind, invoice, taxonomy, previous, policy)
    if duplicate is None:
        return billed
    reason, decision = _CODES[duplicate]
    return replace(
        billed, classification=duplicate, reason=reason, decision=max(decision, billed.decision)
    )


def evaluate(
    invoice: Invoice,
    *,
    at: date,
    taxonomy: Taxonomy | None,
    bases: tuple[Basis, ...],
    currencies: CurrencyTable,
    previous: tuple[Invoice, ...] = (),
    verified_quantities: dict[str, Quantity] | None = None,
    policy: Policy = _DEFAULT_POLICY,
    synthetic: bool = False,
    basis_available: bool = True,
) -> InvoiceAudit:
    """Audit a verified invoice and publish independent time-charge match records."""

    def finish(
        decision: DecisionValue,
        reasons: set[Reason],
        rows: tuple[AuditedLine, ...] = (),
        matches: tuple[MatchRecord, ...] = (),
        totals: dict[str, CurrencyTotal] | None = None,
        header: HeaderTotal | None = None,
    ) -> InvoiceAudit:
        rules = {
            reason.value: ((Requirement(kind, name),),)
            for reason, (kind, name) in _REQUIREMENTS.items()
        }
        needs = requirements_for(decision, (reason for reason in reasons if reason in rules), rules)
        return InvoiceAudit(
            decision,
            rows,
            matches,
            tuple(sorted(reasons)),
            totals or {},
            header,
            tuple(dict(item) for item in open_items(needs)),
        )

    if not invoice.verified or not invoice.lines:
        return finish(DecisionValue.ABSTAIN, {Reason.INVOICE})
    if taxonomy is None or not taxonomy.valid_at(at):
        return finish(DecisionValue.ABSTAIN, {Reason.TAXONOMY})
    if invoice.currency not in currencies.minor_units:
        return finish(DecisionValue.ABSTAIN, {Reason.UNSUPPORTED})
    if not basis_available and not bases:
        return finish(DecisionValue.ABSTAIN, {Reason.PACK})
    if not _eligible(invoice.label, synthetic):
        return finish(DecisionValue.ABSTAIN, {Reason.LABEL})

    rows = tuple(
        _audit_line(
            line,
            invoice,
            taxonomy,
            bases,
            currencies,
            verified_quantities or {},
            previous,
            policy,
            synthetic,
        )
        for line in sorted(invoice.lines, key=lambda line: line.id)
    )
    matches = tuple(
        MatchRecord(row.line.id, row.kind.code, row.basis, row.reason)
        for row in rows
        if row.kind.kind == LineKind.TIME_BASED
    )
    totals = {}
    for currency in sorted({row.line.currency for row in rows}):
        in_currency = [
            row for row in rows if row.line.currency == currency and row.kind.kind != LineKind.TAX
        ]
        billed = _sum(row.billed for row in in_currency)
        expected_values = [row.expected for row in in_currency if row.expected is not None]
        expected = _sum(expected_values) if len(expected_values) == len(in_currency) else None
        difference = _CONTEXT.subtract(billed, expected) if expected is not None else None
        totals[currency] = CurrencyTotal(billed, expected, difference)

    decision = max(row.decision for row in rows)
    reasons = {row.reason for row in rows}
    header = None
    if invoice.total is not None:
        line_sum = _sum(row.billed for row in rows if row.line.currency == invoice.currency)
        match = all(row.line.currency == invoice.currency for row in rows) and _equal(
            line_sum,
            invoice.total,
            invoice.currency,
            currencies,
        )
        header = HeaderTotal(invoice.total, line_sum, match)
        if not match:
            decision = max(decision, DecisionValue.HOLD)
            reasons.add(Reason.HEADER)
    return finish(decision, reasons, rows, matches, totals, header)


def _sum(values: Iterable[Decimal]) -> Decimal:
    result = _ZERO
    for value in values:
        result = _CONTEXT.add(result, value)
    return result
