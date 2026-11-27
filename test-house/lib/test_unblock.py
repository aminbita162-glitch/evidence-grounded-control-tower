"""Requirement minimization and Passport serialization checks."""

import pytest

from kernel.contracts._generated.passport import Passport
from kernel.lib.unblock import (
    Requirement,
    RequirementKind,
    UnblockItem,
    open_items,
    requirements_for,
)
from kernel.types.decision import DecisionValue

_FACT = Requirement(RequirementKind.FACT, "amount")
_PACK = Requirement(RequirementKind.PACK, "currency reference")
_CHECK = Requirement(RequirementKind.VERIFICATION, "citation confirmation")
_RULES = {
    "SYN.MISSING": ((_FACT,),),
    "SYN.ABSTAIN": ((_PACK,),),
    "SYN.CONFLICT": ((_CHECK,),),
}


def _items(outcome: DecisionValue, reasons: list[str]) -> tuple[UnblockItem, ...]:
    return requirements_for(outcome, reasons, _RULES)


def _fixture_decision(evidence: set[Requirement]) -> DecisionValue:
    return DecisionValue.ALLOW if {_FACT, _PACK} <= evidence else DecisionValue.HOLD


@pytest.mark.fast
def test_T_LIB_0043() -> None:
    """Check map a hold code to the missing fact.

    id: T-LIB-0043
    title: Map a hold code to the missing fact
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Map a hold code to the missing fact
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    assert _items(DecisionValue.HOLD, ["SYN.MISSING"]) == (UnblockItem(_FACT, ("SYN.MISSING",)),)


@pytest.mark.fast
def test_T_LIB_0044() -> None:
    """Check map abstention to missing pack evidence.

    id: T-LIB-0044
    title: Map abstention to missing pack evidence
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Map abstention to missing pack evidence
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    assert _items(DecisionValue.ABSTAIN, ["SYN.ABSTAIN"]) == (UnblockItem(_PACK, ("SYN.ABSTAIN",)),)


@pytest.mark.fast
def test_T_LIB_0045() -> None:
    """Check map escalation to unresolved verification.

    id: T-LIB-0045
    title: Map escalation to unresolved verification
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Map escalation to unresolved verification
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    assert _items(DecisionValue.ESCALATE, ["SYN.CONFLICT"]) == (
        UnblockItem(_CHECK, ("SYN.CONFLICT",)),
    )


@pytest.mark.fast
def test_T_LIB_0046() -> None:
    """Check choose the smallest shared alternative across reasons.

    id: T-LIB-0046
    title: Choose the smallest shared alternative across reasons
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Choose the smallest shared alternative across reasons
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    rules = {"A": ((_FACT,), (_CHECK,)), "B": ((_CHECK,),)}
    items = requirements_for(DecisionValue.HOLD, ["B", "A"], rules)
    assert items == (UnblockItem(_CHECK, ("A", "B")),)


@pytest.mark.fast
def test_T_LIB_0047() -> None:
    """Check deduplicate repeated reasons and shared requirements.

    id: T-LIB-0047
    title: Deduplicate repeated reasons and shared requirements
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Deduplicate repeated reasons and shared requirements
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    assert _items(DecisionValue.HOLD, ["SYN.MISSING", "SYN.MISSING", "SYN.MISSING"]) == _items(
        DecisionValue.HOLD, ["SYN.MISSING"]
    )


@pytest.mark.fast
def test_T_LIB_0048() -> None:
    """Check reevaluate to allow after fixture requirements are resolved.

    id: T-LIB-0048
    title: Reevaluate to allow after fixture requirements are resolved
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Reevaluate to allow after fixture requirements are resolved
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    before = _items(DecisionValue.HOLD, ["SYN.MISSING", "SYN.ABSTAIN"])
    assert {item.requirement for item in before} == {_FACT, _PACK}
    assert _fixture_decision({_FACT}) == DecisionValue.HOLD
    assert _fixture_decision({item.requirement for item in before}) == DecisionValue.ALLOW
    assert _items(DecisionValue.ALLOW, ["SYN.MISSING"]) == ()


@pytest.mark.fast
def test_T_LIB_0049() -> None:
    """Check return stable output for reason order permutations.

    id: T-LIB-0049
    title: Return stable output for reason order permutations
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Return stable output for reason order permutations
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    forward = _items(DecisionValue.HOLD, ["SYN.CONFLICT", "SYN.MISSING", "SYN.ABSTAIN"])
    backward = _items(DecisionValue.HOLD, ["SYN.ABSTAIN", "SYN.MISSING", "SYN.CONFLICT"])
    assert open_items(forward) == open_items(backward)


@pytest.mark.fast
def test_T_LIB_0050() -> None:
    """Check serialize items in the passport contract.

    id: T-LIB-0050
    title: Serialize items in the Passport contract
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Serialize items in the Passport contract
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    items = open_items(_items(DecisionValue.HOLD, ["SYN.MISSING"]))
    passport = Passport.model_validate(
        {
            "case_id": "SYN-CASE",
            "passport_id": "SYN-PASS",
            "schema_version": 1,
            "signature": "0" * 64,
            "tenant_id": "SYN-TEN",
            "open_items": items,
        }
    )
    assert passport.model_dump()["open_items"] == [
        {"kind": "FACT", "name": "amount", "reasons": ["SYN.MISSING"]}
    ]


@pytest.mark.fast
def test_T_LIB_0051() -> None:
    """Check require a closed reason mapping.

    id: T-LIB-0051
    title: Require a closed reason mapping
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Require a closed reason mapping
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    with pytest.raises(ValueError, match="no unblock declaration"):
        _items(DecisionValue.HOLD, ["SYN.UNKNOWN"])


@pytest.mark.fast
def test_T_LIB_0052() -> None:
    """Check remove already resolved inputs from the smallest list.

    id: T-LIB-0052
    title: Remove already resolved inputs from the smallest list
    purpose: Verify reason mappings and their reproducible minimal output
    level: fast
    requirement: P13-T04
    input: Synthetic advisory decisions and requirement declarations
    expected: Remove already resolved inputs from the smallest list
    risk: A blocked case cannot identify the missing inputs
    capability: shared-library
    """
    remaining = requirements_for(
        DecisionValue.HOLD, ["SYN.ABSTAIN", "SYN.MISSING"], _RULES, resolved=[_FACT]
    )
    assert remaining == (UnblockItem(_PACK, ("SYN.ABSTAIN",)),)
