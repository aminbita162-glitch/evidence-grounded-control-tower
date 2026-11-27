"""Independent verification, consistency and expiry checks for the solver harness."""

import pytest

from kernel.lib.solve import (
    Constraint,
    IntegerModel,
    Result,
    Settings,
    Term,
    Variable,
    check_candidate,
    solve_consistent,
    solve_cp_sat,
    solve_z3,
)
from kernel.lib.solve.checker import violations

_SETTINGS = Settings(seed=17, workers=1, seconds=2)
_TERMS = (Term("x", 1),)


def _model() -> IntegerModel:
    return IntegerModel(
        (Variable("x", 0, 10),),
        (Constraint("minimum", _TERMS, lower=3),),
        _TERMS,
    )


def _impossible() -> IntegerModel:
    return IntegerModel(
        (Variable("x", 0, 10),),
        (Constraint("minimum", _TERMS, lower=3), Constraint("maximum", _TERMS, upper=2)),
    )


@pytest.mark.fast
def test_T_LIB_0077() -> None:
    """Check reject a seeded incorrect solver assignment.

    id: T-LIB-0077
    title: Reject a seeded incorrect solver assignment
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Reject a seeded incorrect solver assignment
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    result = check_candidate(_model(), {"x": 0}, backend="TEST", settings=_SETTINGS)
    assert result.status == "ABSTAIN" and result.reason == "INVALID_ASSIGNMENT"
    assert result.evidence == ("minimum",)


@pytest.mark.fast
def test_T_LIB_0078() -> None:
    """Check find and independently verify a cp-sat optimum.

    id: T-LIB-0078
    title: Find and independently verify a CP-SAT optimum
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Find and independently verify a CP-SAT optimum
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    result = solve_cp_sat(_model(), _SETTINGS)
    assert result.status == "SOLVED"
    assert result.assignment == (("x", 3),) and result.objective == 3
    assert result.reason == "VERIFIED_ASSIGNMENT"


@pytest.mark.fast
def test_T_LIB_0079() -> None:
    """Check check satisfiability with the z3 encoding.

    id: T-LIB-0079
    title: Check satisfiability with the Z3 encoding
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Check satisfiability with the Z3 encoding
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    result = solve_z3(_model(), _SETTINGS)
    assert result.status == "SOLVED"
    assert not violations(_model(), dict(result.assignment))


@pytest.mark.fast
def test_T_LIB_0080() -> None:
    """Check attach an unsatisfiable core to cp-sat infeasibility.

    id: T-LIB-0080
    title: Attach an unsatisfiable core to CP-SAT infeasibility
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Attach an unsatisfiable core to CP-SAT infeasibility
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    result = solve_cp_sat(_impossible(), _SETTINGS)
    assert result.status == "INFEASIBLE"
    assert result.reason == "Z3_UNSAT"
    assert set(result.evidence) == {"minimum", "maximum"}


@pytest.mark.fast
def test_T_LIB_0081() -> None:
    """Check record z3 infeasibility independently.

    id: T-LIB-0081
    title: Record Z3 infeasibility independently
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Record Z3 infeasibility independently
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    result = solve_z3(_impossible(), _SETTINGS)
    assert result.status == "INFEASIBLE"
    assert result.evidence == ("maximum", "minimum")


@pytest.mark.fast
def test_T_LIB_0082() -> None:
    """Check confirm stability across fixed thread counts.

    id: T-LIB-0082
    title: Confirm stability across fixed thread counts
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Confirm stability across fixed thread counts
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    result = solve_consistent(_model(), _SETTINGS, other_workers=2)
    assert result.status == "SOLVED" and result.assignment == (("x", 3),)
    assert result.settings.seed == _SETTINGS.seed


@pytest.mark.fast
def test_T_LIB_0083(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check reject seeded instability between worker counts.

    id: T-LIB-0083
    title: Reject seeded instability between worker counts
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Reject seeded instability between worker counts
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    model = IntegerModel((Variable("x", 0, 1),), ())

    def ambiguous(current: IntegerModel, settings: Settings) -> Result:
        return check_candidate(
            current, {"x": settings.workers - 1}, backend="CP-SAT", settings=settings
        )

    monkeypatch.setattr("kernel.lib.solve.solve_cp_sat", ambiguous)
    result = solve_consistent(model, _SETTINGS, other_workers=2)
    assert result.reason == "THREAD_INSTABILITY" and result.status == "ABSTAIN"
    assert not result.assignment


@pytest.mark.fast
def test_T_LIB_0084() -> None:
    """Check record cp-sat timeout as abstention.

    id: T-LIB-0084
    title: Record CP-SAT timeout as abstention
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Record CP-SAT timeout as abstention
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    result = solve_cp_sat(_model(), Settings(seed=17, workers=1, seconds=0))
    assert result.status == "ABSTAIN" and result.reason == "TIME_LIMIT"


@pytest.mark.fast
def test_T_LIB_0085() -> None:
    """Check record exhausted z3 time budget as abstention.

    id: T-LIB-0085
    title: Record exhausted Z3 time budget as abstention
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Record exhausted Z3 time budget as abstention
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    result = solve_z3(_model(), Settings(seed=17, workers=1, seconds=0))
    assert result.status == "ABSTAIN" and result.reason == "TIME_LIMIT"


@pytest.mark.fast
def test_T_LIB_0086() -> None:
    """Check reject domain and completeness errors independently.

    id: T-LIB-0086
    title: Reject domain and completeness errors independently
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Reject domain and completeness errors independently
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    assert violations(_model(), {"x": 100}) == ("domain:x",)
    assert violations(_model(), {"x": True}) == ("domain:x",)
    assert violations(_model(), {"wrong": 4}) == ("ASSIGNMENT_VARIABLES",)


@pytest.mark.fast
def test_T_LIB_0087() -> None:
    """Check match mathematical enumeration for an encoded objective.

    id: T-LIB-0087
    title: Match mathematical enumeration for an encoded objective
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Match mathematical enumeration for an encoded objective
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    model = _model()
    oracle = min(value for value in range(11) if value >= 3)
    assert solve_cp_sat(model, _SETTINGS).objective == oracle


@pytest.mark.fast
def test_T_LIB_0088() -> None:
    """Check require known variables before encoding.

    id: T-LIB-0088
    title: Require known variables before encoding
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Require known variables before encoding
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    with pytest.raises(ValueError, match="unknown variable"):
        IntegerModel((Variable("x", 0, 1),), (Constraint("bad", (Term("unknown", 1),), lower=1),))


@pytest.mark.fast
def test_T_LIB_0089() -> None:
    """Check preserve the exact numeric model in the result scope.

    id: T-LIB-0089
    title: Preserve the exact numeric model in the result scope
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Preserve the exact numeric model in the result scope
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """
    model = _model()
    result = solve_cp_sat(model, _SETTINGS)
    assert result.scope == "ENCODED_MODEL_ONLY"
    assert result.model_hash == model.digest()
    assert result.model_hash != _impossible().digest()


@pytest.mark.fast
def test_T_LIB_0090(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check avoid infeasibility claims lacking independent evidence.

    id: T-LIB-0090
    title: Avoid infeasibility claims lacking independent evidence
    purpose: Verify solver results, declared assumptions and failure states
    level: fast
    requirement: P13-T07
    input: Synthetic integer model or a seeded candidate assignment
    expected: Avoid infeasibility claims lacking independent evidence
    risk: An incorrect solver result is presented as verified
    capability: shared-library
    """

    def unknown(model: IntegerModel, settings: Settings) -> Result:
        return Result("ABSTAIN", model.digest(), "Z3", settings, "TIME_LIMIT")

    monkeypatch.setattr("kernel.lib.solve.solve_z3", unknown)
    result = solve_cp_sat(_impossible(), _SETTINGS)
    assert result.status == "ABSTAIN" and result.reason == "INFEASIBILITY_UNCONFIRMED"
    assert result.evidence == ("TIME_LIMIT",)
