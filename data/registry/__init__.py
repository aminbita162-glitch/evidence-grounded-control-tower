"""Source Registry validator for the Control Tower (P02-T02).

Loads ``data/registry/sources.yaml`` and validates each entry against
``schemas/source.json``.  Enforces:

- Every field present (required fields from the schema).
- Unique ``source_id`` values across all entries.
- ``retrieved_month`` is month-level only (YYYY-MM); day-level dates are rejected.
- ``redistributable`` flag exists on every entry.
- ``label`` must be a known label from the taxonomy.
- ``BASELINE.json`` hash matches each entry; a changed entry without a baseline
  update fails.

The baseline update path:
  ``update_baseline(registry_path, baseline_path)``
  Recomputes and writes ``BASELINE.json``.  Call only via ``gate data
  --update-baseline`` (P02-T05), never directly from task code.

Spec: Part 3 §3.12, Part 4 §4.12, P02-T02, schemas/source.json.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

__all__ = [
    "RegistryError",
    "RegistryEntry",
    "RegistryValidationResult",
    "REQUIRED_FIELDS",
    "VALID_LABELS",
    "VALID_KINDS",
    "VALID_USE_CLASSES",
    "VALID_STATUS",
    "VALID_REDISTRIBUTABLE",
    "MONTH_RE",
    "SOURCE_ID_RE",
    "load_registry",
    "validate_entry",
    "validate_registry",
    "compute_entry_hash",
    "load_baseline",
    "update_baseline",
    "check_baseline",
]

REQUIRED_FIELDS: tuple[str, ...] = (
    "source_id",
    "publisher",
    "reference",
    "retrieved_month",
    "label",
    "license_summary",
    "redistributable",
    "kind",
    "use_class",
    "status",
    "max_age_months",
)

VALID_LABELS: frozenset[str] = frozenset(
    {
        "OFFICIAL",
        "DERIVED",
        "SECONDARY",
        "SIMULATED_RULE",
        "SYNTHETIC",
        "ASSUMPTION",
        "UNVERIFIED",
    }
)

VALID_KINDS: frozenset[str] = frozenset({"SOURCE", "DATASET", "DEPENDENCY", "STANDARD"})

VALID_USE_CLASSES: frozenset[str] = frozenset(
    {
        "SCREENING",
        "MEASURE",
        "TARIFF",
        "CODELIST",
        "CALENDAR",
        "CATALOGUE",
        "TERMS",
        "SIMULATION",
        "LIBRARY",
    }
)

VALID_STATUS: frozenset[str] = frozenset({"UNVERIFIED", "VERIFIED"})

VALID_REDISTRIBUTABLE: frozenset[str] = frozenset({"yes", "no", "unknown"})

#: Month-level date pattern (YYYY-MM).  Day-level dates are rejected.
MONTH_RE: re.Pattern[str] = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

#: source_id pattern: SRC- or SIM- then upper-case letters, digits and hyphens.
SOURCE_ID_RE: re.Pattern[str] = re.compile(r"^(SRC|SIM)-[A-Z0-9-]+$")


class RegistryError(ValueError):
    """A registry validation error."""


@dataclass(frozen=True)
class RegistryEntry:
    """One validated Source Registry entry."""

    source_id: str
    publisher: str
    reference: str
    retrieved_month: str
    label: str
    license_summary: str
    redistributable: str
    kind: str
    use_class: str
    status: str
    max_age_months: int
    v_item: str


@dataclass(frozen=True)
class RegistryValidationResult:
    """Result of validating the registry."""

    entries: list[RegistryEntry]
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        """Return True if no errors were found."""
        return not self.errors


def load_registry(path: Path) -> list[dict[str, Any]]:
    """Load the raw registry YAML from *path*.

    Args:
        path: Path to sources.yaml.

    Returns:
        List of raw entry dicts.

    Raises:
        RegistryError: If the file cannot be read or is not valid YAML.
    """
    if not path.is_file():
        raise RegistryError(f"registry file not found: {path}")
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RegistryError(f"cannot parse registry {path}: {exc}") from exc
    if raw is None:
        return []
    if not isinstance(raw, dict):
        raise RegistryError(f"registry {path} must be a YAML mapping")
    sources_raw = raw.get("sources", [])
    if not isinstance(sources_raw, list):
        raise RegistryError(f"registry {path}: 'sources' must be a list")
    return [item for item in sources_raw if isinstance(item, dict)]


def validate_entry(raw: dict[str, Any], index: int) -> tuple[RegistryEntry | None, list[str]]:
    """Validate one raw entry dict.

    Args:
        raw: The raw YAML dict for the entry.
        index: 0-based position in the registry (for error messages).

    Returns:
        Tuple of (RegistryEntry or None, list of error strings).
    """
    errors: list[str] = []
    sid = str(raw.get("source_id", "")) if "source_id" in raw else ""
    label = f"entry[{index}] source_id={sid!r}" if sid else f"entry[{index}]"

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in raw or raw[field] is None or raw[field] == "":
            errors.append(f"{label}: missing required field '{field}'")

    if errors:
        return None, errors

    # source_id format
    if not SOURCE_ID_RE.match(sid):
        errors.append(f"{label}: source_id {sid!r} does not match pattern ^(SRC|SIM)-[A-Z0-9-]+$")

    # retrieved_month: month-level only
    retrieved = str(raw["retrieved_month"])
    if not MONTH_RE.match(retrieved):
        errors.append(f"{label}: retrieved_month {retrieved!r} is not YYYY-MM format")

    # label
    lbl = str(raw["label"])
    if lbl not in VALID_LABELS:
        errors.append(f"{label}: label {lbl!r} is not a valid label ({sorted(VALID_LABELS)})")

    # redistributable
    rdist = str(raw["redistributable"])
    if rdist not in VALID_REDISTRIBUTABLE:
        errors.append(
            f"{label}: redistributable {rdist!r} must be one of {sorted(VALID_REDISTRIBUTABLE)}"
        )

    # kind
    kind = str(raw["kind"])
    if kind not in VALID_KINDS:
        errors.append(f"{label}: kind {kind!r} must be one of {sorted(VALID_KINDS)}")

    # use_class
    use_class = str(raw["use_class"])
    if use_class not in VALID_USE_CLASSES:
        errors.append(
            f"{label}: use_class {use_class!r} must be one of {sorted(VALID_USE_CLASSES)}"
        )

    # status
    status = str(raw["status"])
    if status not in VALID_STATUS:
        errors.append(f"{label}: status {status!r} must be one of {sorted(VALID_STATUS)}")

    # max_age_months
    max_age = raw["max_age_months"]
    if not isinstance(max_age, int) or max_age < 1:
        errors.append(f"{label}: max_age_months must be a positive integer, got {max_age!r}")

    if errors:
        return None, errors

    return (
        RegistryEntry(
            source_id=sid,
            publisher=str(raw["publisher"]),
            reference=str(raw["reference"]),
            retrieved_month=retrieved,
            label=lbl,
            license_summary=str(raw["license_summary"]),
            redistributable=rdist,
            kind=kind,
            use_class=use_class,
            status=status,
            max_age_months=int(max_age),
            v_item=str(raw.get("v_item", "none")),
        ),
        [],
    )


def validate_registry(path: Path) -> RegistryValidationResult:
    """Validate the registry at *path*.

    Enforces uniqueness of source_id, presence of all required fields,
    month-level dates, valid enumerations and that the redistributable flag exists.

    Args:
        path: Path to sources.yaml.

    Returns:
        A :class:`RegistryValidationResult` with entries and errors.
    """
    try:
        raw_entries = load_registry(path)
    except RegistryError as exc:
        return RegistryValidationResult(entries=[], errors=[str(exc)])

    errors: list[str] = []
    entries: list[RegistryEntry] = []
    seen_ids: dict[str, int] = {}

    for i, raw in enumerate(raw_entries):
        entry, entry_errors = validate_entry(raw, i)
        errors.extend(entry_errors)
        if entry is not None:
            if entry.source_id in seen_ids:
                errors.append(
                    f"duplicate source_id {entry.source_id!r} at entries "
                    f"{seen_ids[entry.source_id]} and {i}"
                )
            else:
                seen_ids[entry.source_id] = i
                entries.append(entry)

    return RegistryValidationResult(entries=entries, errors=errors)


def compute_entry_hash(entry: dict[str, Any]) -> str:
    """SHA-256 of the canonical JSON of an entry dict.

    Args:
        entry: Raw entry dict (from YAML).

    Returns:
        Hex digest string.
    """
    canonical = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_baseline(baseline_path: Path) -> dict[str, str]:
    """Load BASELINE.json from *baseline_path*.

    Returns an empty dict if the file does not exist.

    Args:
        baseline_path: Path to BASELINE.json.

    Returns:
        Mapping from source_id to content hash.
    """
    if not baseline_path.is_file():
        return {}
    raw: object = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items()}


def update_baseline(registry_path: Path, baseline_path: Path) -> None:
    """Recompute and write BASELINE.json from the current registry.

    Should be called only via ``gate data --update-baseline``.

    Args:
        registry_path: Path to sources.yaml.
        baseline_path: Path to BASELINE.json (will be written).
    """
    raw_entries = load_registry(registry_path)
    baseline: dict[str, str] = {}
    for entry in raw_entries:
        sid = str(entry.get("source_id", ""))
        if sid:
            baseline[sid] = compute_entry_hash(entry)
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps(baseline, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def check_baseline(registry_path: Path, baseline_path: Path) -> list[str]:
    """Check that every entry in the registry matches its baseline hash.

    An entry changed without a baseline update is a failure.

    Args:
        registry_path: Path to sources.yaml.
        baseline_path: Path to BASELINE.json.

    Returns:
        List of error messages (empty = clean).
    """
    baseline = load_baseline(baseline_path)
    errors: list[str] = []
    try:
        raw_entries = load_registry(registry_path)
    except RegistryError as exc:
        return [str(exc)]

    current_ids: set[str] = set()
    for entry in raw_entries:
        sid = str(entry.get("source_id", ""))
        if not sid:
            continue
        current_ids.add(sid)
        current_hash = compute_entry_hash(entry)
        if sid not in baseline:
            errors.append(
                f"source_id {sid!r} is not in BASELINE.json — run gate data --update-baseline"
            )
        elif baseline[sid] != current_hash:
            errors.append(
                f"source_id {sid!r} changed without a baseline update — "
                f"run gate data --update-baseline in a named task"
            )

    # Check for entries in baseline that are no longer in the registry
    for sid in baseline:
        if sid not in current_ids:
            errors.append(
                f"source_id {sid!r} is in BASELINE.json but not in the registry"
            )

    return errors
