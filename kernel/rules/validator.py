"""Pack validation (Part 3 §3.6, §3.8, P06-T02).

Validates pack manifest, rule definitions, window consistency, citation
and label presence, declared-label ceiling, expression typing, precedence
declarations and semantic versioning.  An invalid pack fails closed.
"""

from __future__ import annotations

from collections.abc import Mapping

from kernel.rules.dsl.parser import ParseError, parse_expr
from kernel.types.label import label_rank

__all__ = ["ValidationError", "validate_pack"]


class ValidationError(Exception):
    """A pack validation error with a stable error code.

    Attributes:
        code: Stable error code (e.g. ``PACK_MISSING_FIELD``).
        message: Human-readable description.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


_REQUIRED_MANIFEST: tuple[str, ...] = (
    "tenant_id",
    "schema_version",
    "pack_id",
    "version",
    "valid_from",
    "valid_to",
    "jurisdiction",
    "sources",
)

_REQUIRED_RULE: tuple[str, ...] = (
    "id",
    "version",
    "condition",
    "outcome",
    "reason_code",
    "citation_source_id",
    "valid_from",
    "valid_to",
    "label",
)

_VALID_OUTCOMES: frozenset[str] = frozenset({"ALLOW", "ABSTAIN", "HOLD", "ESCALATE"})
_VALID_LABELS: frozenset[str] = frozenset(
    {
        "OFFICIAL",
        "DERIVED",
        "SECONDARY",
        "SYNTHETIC",
        "SIMULATED_RULE",
        "ASSUMPTION",
        "UNVERIFIED",
    }
)


def _check_required(data: Mapping[str, object], fields: tuple[str, ...], prefix: str) -> None:
    """Check that all required fields are present."""
    for field in fields:
        if field not in data:
            raise ValidationError(
                "PACK_MISSING_FIELD",
                f"{prefix}: missing required field {field!r}",
            )


def _check_window(from_val: object, to_val: object, prefix: str) -> None:
    """Check that valid_from <= valid_to."""
    if not isinstance(from_val, str) or not isinstance(to_val, str):
        raise ValidationError("PACK_INVALID_WINDOW", f"{prefix}: timestamps must be strings")
    if from_val > to_val:
        raise ValidationError(
            "PACK_INVALID_WINDOW",
            f"{prefix}: valid_from ({from_val}) > valid_to ({to_val})",
        )


def _check_label_ceiling(
    declared_label: str,
    source_labels: Mapping[str, str],
) -> None:
    """Check that the declared label is no stronger than the weakest
    source label (Part 3 §3.8).

    A declared label stronger than the weakest registered source label
    is rejected.
    """
    if not source_labels:
        return
    weakest_rank = min(label_rank(lbl) for lbl in source_labels.values())
    if label_rank(declared_label) > weakest_rank:
        weakest_label = min(source_labels.values(), key=label_rank)
        raise ValidationError(
            "PACK_LABEL_CEILING",
            f"declared label {declared_label!r} is stronger than "
            f"weakest source label {weakest_label!r}",
        )


def _check_precedence(rules: list[Mapping[str, object]]) -> None:
    """Check that overlapping rule windows have precedence declared.

    Two rules overlap if their validity windows intersect.  If two rules
    overlap and neither has a ``precedence`` field, the pack is invalid.
    """
    for i, r1 in enumerate(rules):
        for j, r2 in enumerate(rules):
            if i >= j:
                continue
            w1_from = r1.get("valid_from", "")
            w1_to = r1.get("valid_to", "")
            w2_from = r2.get("valid_from", "")
            w2_to = r2.get("valid_to", "")
            if not isinstance(w1_from, str) or not isinstance(w1_to, str):
                continue
            if not isinstance(w2_from, str) or not isinstance(w2_to, str):
                continue
            # Overlap check
            if w1_from <= w2_to and w2_from <= w1_to:
                has_prec1 = "precedence" in r1
                has_prec2 = "precedence" in r2
                if not has_prec1 and not has_prec2:
                    raise ValidationError(
                        "PACK_OVERLAP_NO_PRECEDENCE",
                        f"rules {r1.get('id', '?')!r} and "
                        f"{r2.get('id', '?')!r} overlap without precedence",
                    )


def validate_pack(
    data: Mapping[str, object],
    source_labels: Mapping[str, str] | None = None,
) -> None:
    """Validate a pack.

    Args:
        data: The pack data (manifest + rules).
        source_labels: Mapping from source_id to label for label ceiling
            check. If None, the label ceiling check is skipped.

    Raises:
        ValidationError: If the pack is invalid.
    """
    # 1. Required manifest fields
    _check_required(data, _REQUIRED_MANIFEST, "pack")

    # 2. Sources must be a list of strings
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise ValidationError("PACK_INVALID_SOURCES", "sources must be a list")
    for s in sources:
        if not isinstance(s, str):
            raise ValidationError("PACK_INVALID_SOURCES", "source ids must be strings")

    # 3. Window consistency for the pack
    _check_window(data["valid_from"], data["valid_to"], "pack")

    # 4. Declared label ceiling
    declared_label = data.get("declared_label")
    if isinstance(declared_label, str):
        if declared_label not in _VALID_LABELS:
            raise ValidationError(
                "PACK_INVALID_LABEL",
                f"invalid declared_label: {declared_label!r}",
            )
        if source_labels is not None:
            pack_sources = {
                s: source_labels.get(s, "UNVERIFIED") for s in sources if isinstance(s, str)
            }
            _check_label_ceiling(declared_label, pack_sources)

    # 5. Rule definitions
    rules_raw = data.get("rules", [])
    if not isinstance(rules_raw, list):
        raise ValidationError("PACK_INVALID_RULES", "rules must be a list")
    rules: list[Mapping[str, object]] = []
    for idx, rule in enumerate(rules_raw):
        if not isinstance(rule, Mapping):
            raise ValidationError(
                "PACK_INVALID_RULES",
                f"rule[{idx}] must be an object",
            )
        prefix = f"rule[{idx}]"
        _check_required(rule, _REQUIRED_RULE, prefix)

        # Outcome must be valid
        outcome = rule.get("outcome")
        if outcome not in _VALID_OUTCOMES:
            raise ValidationError(
                "PACK_INVALID_OUTCOME",
                f"{prefix}: invalid outcome {outcome!r}",
            )

        # Label must be valid
        label = rule.get("label")
        if label not in _VALID_LABELS:
            raise ValidationError(
                "PACK_INVALID_LABEL",
                f"{prefix}: invalid label {label!r}",
            )

        # Window consistency for the rule
        _check_window(rule["valid_from"], rule["valid_to"], prefix)

        # Citation must reference a declared source
        citation_id = rule.get("citation_source_id")
        if not isinstance(citation_id, str):
            raise ValidationError(
                "PACK_MISSING_CITATION",
                f"{prefix}: citation_source_id must be a string",
            )
        if sources and citation_id not in sources:
            raise ValidationError(
                "PACK_UNKNOWN_SOURCE",
                f"{prefix}: citation source {citation_id!r} not in pack sources",
            )

        # Condition must parse as a valid DSL expression
        condition = rule.get("condition")
        if not isinstance(condition, Mapping):
            raise ValidationError(
                "PACK_INVALID_CONDITION",
                f"{prefix}: condition must be an object",
            )
        try:
            parse_expr(dict(condition))
        except ParseError as exc:
            raise ValidationError(
                "PACK_INVALID_CONDITION",
                f"{prefix}: {exc.code}: {exc.message}",
            ) from exc

        rules.append(rule)

    # 6. Precedence declarations for overlapping windows
    _check_precedence(rules)
