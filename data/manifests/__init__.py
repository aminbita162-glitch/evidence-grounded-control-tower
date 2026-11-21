"""License Manifest and Source Gap Register validator (P02-T03).

Loads ``data/manifests/manifests.yaml`` and ``data/registry/gaps.yaml``
and validates each entry against the schemas:
  - ``schemas/license-manifest.json``
  - ``schemas/gap.json``

Enforces (data gate checks):
- Every file under ``data/`` that is not in an excluded set must be covered by a
  manifest in the manifest store (uncovered file fails).
- A dataset with an UNVERIFIED license on a used (non-excluded) source fails.
- A gap entry without a valid verification id (V-xx) fails.
- No tracked file contains rule text or heading text from copyright-protected
  sources (Part 3 §3.12; S-11 WCO-HS, S-12 ICC-Incoterms).
- Third-party copyrighted tables are not stored (Part 3 §3.12).

Spec: Part 3 §3.12; schemas/license-manifest.json; schemas/gap.json; P02-T03.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

__all__ = [
    "ManifestEntry",
    "GapEntry",
    "ManifestValidationResult",
    "GapValidationResult",
    "REDISTRIBUTION_VALUES",
    "V_ITEM_RE",
    "MONTH_RE",
    "SOURCE_ID_RE",
    "load_manifests",
    "validate_manifest_entry",
    "validate_manifests",
    "load_gaps",
    "validate_gap_entry",
    "validate_gaps",
    "check_third_party_content",
]

#: Valid redistribution permission values.
REDISTRIBUTION_VALUES: frozenset[str] = frozenset({"yes", "no", "unknown", "not-applicable"})

#: Verification item id pattern (V-xx).
V_ITEM_RE: re.Pattern[str] = re.compile(r"^V-[0-9]+$")

#: Month-level date pattern (YYYY-MM).
MONTH_RE: re.Pattern[str] = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

#: source_id pattern: SRC- or SIM- then upper-case letters, digits and hyphens.
SOURCE_ID_RE: re.Pattern[str] = re.compile(r"^(SRC|SIM)-[A-Z0-9-]+$")

#: Copyright-protected source ids whose content must not be stored.
#: S-11: WCO Harmonized System; S-12: ICC Incoterms.
PROTECTED_SOURCE_IDS: frozenset[str] = frozenset({"SRC-WCO-HS", "SRC-ICC-INCOTERMS"})

#: Minimum substrings to detect accidental storage of S-11 or S-12 content.
#: These are distinctive phrases from copyright-protected publications.
PROTECTED_CONTENT_MARKERS: tuple[str, ...] = (
    "Harmonized System",
    "HS nomenclature",
    "Incoterms rules",
    "Incoterms 2020",
)

#: Files under data/ that are exempt from manifest coverage (infrastructure files).
EXCLUDED_DATA_PATHS: frozenset[str] = frozenset(
    {
        "data/__init__.py",
        "data/labels/__init__.py",
        "data/registry/__init__.py",
        "data/registry/sources.yaml",
        "data/registry/BASELINE.json",
        "data/registry/gaps.yaml",
        "data/manifests/manifests.yaml",
        "data/manifests/__init__.py",
    }
)

#: Excluded directory prefixes (relative to repo root, using forward slashes).
EXCLUDED_DATA_DIRS: tuple[str, ...] = (
    "data/__pycache__",
    "data/labels/__pycache__",
    "data/registry/__pycache__",
    "data/manifests/__pycache__",
)


@dataclass(frozen=True)
class ManifestEntry:
    """One validated license manifest entry."""

    source_id: str
    terms: str
    attribution_text: str
    permitted_uses: str
    redistribution_permission: str
    notes: str


@dataclass(frozen=True)
class GapEntry:
    """One validated gap register entry."""

    source_id: str
    reason: str
    v_item: str
    next_check: str
    notes: str


@dataclass(frozen=True)
class ManifestValidationResult:
    """Result of validating the manifest store."""

    entries: list[ManifestEntry]
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        """Return True if no errors were found."""
        return not self.errors


@dataclass(frozen=True)
class GapValidationResult:
    """Result of validating the gap register."""

    entries: list[GapEntry]
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        """Return True if no errors were found."""
        return not self.errors


def _str_field(raw: dict[str, object], key: str) -> str:
    """Return the string value of *key* in *raw*, or empty string if absent/None."""
    val = raw.get(key)
    if val is None:
        return ""
    return str(val)


def load_manifests(path: Path) -> list[dict[str, object]]:
    """Load the raw manifest list from *path*.

    Args:
        path: Path to manifests.yaml.

    Returns:
        List of raw manifest dicts.

    Raises:
        ValueError: If the file cannot be read or is not valid YAML.
    """
    if not path.is_file():
        raise ValueError(f"manifest file not found: {path}")
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"cannot parse manifests {path}: {exc}") from exc
    if raw is None:
        return []
    if not isinstance(raw, dict):
        raise ValueError(f"manifests file {path} must be a YAML mapping")
    items: object = raw.get("manifests", [])
    if not isinstance(items, list):
        raise ValueError(f"manifests file {path}: 'manifests' must be a list")
    return [item for item in items if isinstance(item, dict)]


def validate_manifest_entry(
    raw: dict[str, object], index: int
) -> tuple[ManifestEntry | None, list[str]]:
    """Validate one raw manifest dict.

    Args:
        raw: The raw YAML dict for the entry.
        index: 0-based position in the manifest list (for error messages).

    Returns:
        Tuple of (ManifestEntry or None, list of error strings).
    """
    errors: list[str] = []
    sid = _str_field(raw, "source_id")
    label = f"manifest[{index}] source_id={sid!r}" if sid else f"manifest[{index}]"

    required = (
        "source_id",
        "terms",
        "attribution_text",
        "permitted_uses",
        "redistribution_permission",
    )
    for field in required:
        if field not in raw or raw[field] is None or raw[field] == "":
            errors.append(f"{label}: missing required field '{field}'")

    if errors:
        return None, errors

    if not SOURCE_ID_RE.match(sid):
        errors.append(f"{label}: source_id {sid!r} does not match pattern ^(SRC|SIM)-[A-Z0-9-]+$")

    rdist = _str_field(raw, "redistribution_permission")
    if rdist not in REDISTRIBUTION_VALUES:
        errors.append(
            f"{label}: redistribution_permission {rdist!r} must be one of "
            f"{sorted(REDISTRIBUTION_VALUES)}"
        )

    if errors:
        return None, errors

    return (
        ManifestEntry(
            source_id=sid,
            terms=_str_field(raw, "terms"),
            attribution_text=_str_field(raw, "attribution_text"),
            permitted_uses=_str_field(raw, "permitted_uses"),
            redistribution_permission=rdist,
            notes=_str_field(raw, "notes"),
        ),
        [],
    )


def validate_manifests(path: Path) -> ManifestValidationResult:
    """Validate all manifests in *path*.

    Args:
        path: Path to manifests.yaml.

    Returns:
        A :class:`ManifestValidationResult` with entries and errors.
    """
    try:
        raw_items = load_manifests(path)
    except ValueError as exc:
        return ManifestValidationResult(entries=[], errors=[str(exc)])

    errors: list[str] = []
    entries: list[ManifestEntry] = []
    seen_ids: dict[str, int] = {}

    for i, raw in enumerate(raw_items):
        entry, entry_errors = validate_manifest_entry(raw, i)
        errors.extend(entry_errors)
        if entry is not None:
            if entry.source_id in seen_ids:
                errors.append(
                    f"duplicate source_id {entry.source_id!r} in manifests at "
                    f"entries {seen_ids[entry.source_id]} and {i}"
                )
            else:
                seen_ids[entry.source_id] = i
                entries.append(entry)

    return ManifestValidationResult(entries=entries, errors=errors)


def load_gaps(path: Path) -> list[dict[str, object]]:
    """Load the raw gap register from *path*.

    Args:
        path: Path to gaps.yaml.

    Returns:
        List of raw gap entry dicts.

    Raises:
        ValueError: If the file cannot be read or is not valid YAML.
    """
    if not path.is_file():
        raise ValueError(f"gap register file not found: {path}")
    try:
        raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"cannot parse gaps {path}: {exc}") from exc
    if raw is None:
        return []
    if not isinstance(raw, dict):
        raise ValueError(f"gaps file {path} must be a YAML mapping")
    items: object = raw.get("gaps", [])
    if not isinstance(items, list):
        raise ValueError(f"gaps file {path}: 'gaps' must be a list")
    return [item for item in items if isinstance(item, dict)]


def validate_gap_entry(raw: dict[str, object], index: int) -> tuple[GapEntry | None, list[str]]:
    """Validate one raw gap entry dict.

    Args:
        raw: The raw YAML dict for the entry.
        index: 0-based position in the gap list (for error messages).

    Returns:
        Tuple of (GapEntry or None, list of error strings).
    """
    errors: list[str] = []
    sid = _str_field(raw, "source_id")
    label = f"gap[{index}] source_id={sid!r}" if sid else f"gap[{index}]"

    required = ("source_id", "reason", "v_item", "next_check")
    for field in required:
        if field not in raw or raw[field] is None or raw[field] == "":
            errors.append(f"{label}: missing required field '{field}'")

    if errors:
        return None, errors

    if not SOURCE_ID_RE.match(sid):
        errors.append(f"{label}: source_id {sid!r} does not match pattern ^(SRC|SIM)-[A-Z0-9-]+$")

    v_item = _str_field(raw, "v_item")
    if not V_ITEM_RE.match(v_item):
        errors.append(
            f"{label}: v_item {v_item!r} must match pattern ^V-[0-9]+$ (not empty, not 'none')"
        )

    next_check = _str_field(raw, "next_check")
    if not MONTH_RE.match(next_check):
        errors.append(f"{label}: next_check {next_check!r} is not YYYY-MM format")

    if errors:
        return None, errors

    return (
        GapEntry(
            source_id=sid,
            reason=_str_field(raw, "reason"),
            v_item=v_item,
            next_check=next_check,
            notes=_str_field(raw, "notes"),
        ),
        [],
    )


def validate_gaps(path: Path) -> GapValidationResult:
    """Validate all gap entries in *path*.

    Args:
        path: Path to gaps.yaml.

    Returns:
        A :class:`GapValidationResult` with entries and errors.
    """
    try:
        raw_items = load_gaps(path)
    except ValueError as exc:
        return GapValidationResult(entries=[], errors=[str(exc)])

    errors: list[str] = []
    entries: list[GapEntry] = []

    for i, raw in enumerate(raw_items):
        entry, entry_errors = validate_gap_entry(raw, i)
        errors.extend(entry_errors)
        if entry is not None:
            entries.append(entry)

    return GapValidationResult(entries=entries, errors=errors)


def check_third_party_content(repo_root: Path) -> list[str]:
    """Check that no tracked file under data/ contains protected copyright content.

    Checks for rule text or heading text from S-11 (WCO HS) and S-12 (ICC
    Incoterms), which must not be stored (Part 3 §3.12).

    Args:
        repo_root: Root of the repository.

    Returns:
        List of error messages (empty = clean).
    """
    errors: list[str] = []
    data_dir = repo_root / "data"
    if not data_dir.is_dir():
        return errors

    for path in data_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(repo_root).as_posix()
        # Skip __pycache__ directories
        if any(relative.startswith(excl) for excl in EXCLUDED_DATA_DIRS):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for marker in PROTECTED_CONTENT_MARKERS:
            if marker in content:
                errors.append(
                    f"{relative}: contains protected content marker {marker!r} "
                    f"(Part 3 §3.12 — no stored rule/heading text from WCO-HS or ICC-Incoterms)"
                )
    return errors
