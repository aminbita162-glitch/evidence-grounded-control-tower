"""Tests for the error model (P03-T06).

Test IDs: T-KRN-0053 to T-KRN-0058.
Covers: every error code has title, status, documentation; codes are unique;
problem-details object validates; broad exception handlers rejected in core;
typed result types; exceptions for defects only.

Spec: Part 3 §3.17; schemas/errors.json; kernel/errors/.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from kernel.errors import (
    ERROR_CODES,
    ErrorCode,
    ProblemDetails,
    get_error,
    to_problem_details,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# T-KRN-0053 — Every code has title, status and documentation text
# ---------------------------------------------------------------------------
# id: T-KRN-0053
# title: Every code has title, status and documentation text
# purpose: Verify all error codes in the registry have required fields.
# level: fast
# requirement: P03-T06, Part 3 §3.17
# input: the error code registry
# expected: every code has non-empty title, status > 0, non-empty documentation
# risk: an error code lacks a required field
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0053_every_code_has_fields() -> None:
    """Every error code has title, status and documentation."""
    for code, entry in ERROR_CODES.items():
        assert entry.title, f"{code}: empty title"
        assert entry.status > 0, f"{code}: invalid status {entry.status}"
        assert entry.documentation, f"{code}: empty documentation"


# ---------------------------------------------------------------------------
# T-KRN-0054 — Codes are unique and never reused
# ---------------------------------------------------------------------------
# id: T-KRN-0054
# title: Codes are unique and never reused
# purpose: Verify the error code registry has no duplicate codes.
# level: fast
# requirement: P03-T06, Part 3 §3.17
# input: the error code registry
# expected: all codes are unique
# risk: duplicate codes cause ambiguity
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0054_codes_unique() -> None:
    """Error codes are unique in the registry."""
    codes = list(ERROR_CODES.keys())
    assert len(codes) == len(set(codes)), "duplicate error codes found"


# ---------------------------------------------------------------------------
# T-KRN-0055 — The problem-details object validates
# ---------------------------------------------------------------------------
# id: T-KRN-0055
# title: The problem-details object validates
# purpose: Verify to_problem_details produces a valid RFC 9457 object.
# level: fast
# requirement: P03-T06, Part 3 §3.17
# input: a known error code
# expected: ProblemDetails with matching title and status
# risk: the problem-details object is malformed
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0055_problem_details_validates() -> None:
    """to_problem_details produces a valid RFC 9457 object."""
    pd = to_problem_details("VERSION_CONFLICT", detail="stale version")
    assert isinstance(pd, ProblemDetails)
    assert pd.status == 409
    assert pd.title == "Version Conflict"
    assert pd.detail == "stale version"


# ---------------------------------------------------------------------------
# T-KRN-0056 — A broad exception handler in the core is rejected by lint
# ---------------------------------------------------------------------------
# id: T-KRN-0056
# title: A broad exception handler in the core is rejected by lint
# purpose: Verify the kernel source has no bare or broad except blocks.
# level: fast
# requirement: P03-T06, Part 4 §4.4
# input: all kernel/ Python source files
# expected: no 'except:' or 'except Exception' found
# risk: broad exception handlers hide defects
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0056_no_broad_except_in_core() -> None:
    """The kernel source has no bare or broad except blocks."""
    kernel_dir = _REPO_ROOT / "kernel"
    pattern = re.compile(r"^\s*except\s*(\s*Exception\s*|\s*):")
    violations: list[str] = []
    for py_file in kernel_dir.rglob("*.py"):
        for i, line in enumerate(py_file.read_text().splitlines(), 1):
            if pattern.match(line):
                violations.append(f"{py_file.name}:{i}: {line.strip()}")
    assert not violations, f"broad exception handlers found:\n{chr(10).join(violations)}"


# ---------------------------------------------------------------------------
# T-KRN-0057 — Typed result types for expected failures
# ---------------------------------------------------------------------------
# id: T-KRN-0057
# title: Typed result types for expected failures
# purpose: Verify ProblemDetails and ErrorCode are typed and frozen.
# level: fast
# requirement: P03-T06, Part 4 §4.4
# input: ProblemDetails and ErrorCode instances
# expected: both are frozen dataclasses
# risk: error types are mutable
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0057_typed_result_types() -> None:
    """ProblemDetails and ErrorCode are frozen dataclasses."""
    pd = ProblemDetails(title="Test", status=400)
    with pytest.raises(AttributeError):
        pd.title = "Changed"  # type: ignore[misc]
    ec = ErrorCode("CODE", "Title", 400, "doc")
    with pytest.raises(AttributeError):
        ec.code = "OTHER"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# T-KRN-0058 — get_error raises for unknown codes
# ---------------------------------------------------------------------------
# id: T-KRN-0058
# title: get_error raises for unknown codes
# purpose: Verify that an unknown error code raises KeyError.
# level: fast
# requirement: P03-T06, Part 3 §3.17
# input: an unknown error code string
# expected: KeyError is raised
# risk: unknown codes are silently ignored
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0058_unknown_code_raises() -> None:
    """get_error raises KeyError for unknown codes."""
    with pytest.raises(KeyError):
        get_error("NONEXISTENT_CODE")
