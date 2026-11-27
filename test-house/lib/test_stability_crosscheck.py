"""Stable plan selection and recorded Gateway cross-check checks."""

from asyncio import run
from collections.abc import Iterable
from itertools import permutations
from typing import cast

import pytest

from adapters.model.gateway import (
    Gateway,
    ModelCallRequest,
    ModelCallResponse,
    compute_prompt_hash,
    compute_response_hash,
)
from adapters.model.recorded import RecordedResponseAdapter
from kernel.extract import FieldLocator
from kernel.lib.crosscheck import (
    Citation,
    CrossCheckRequest,
    CrossCheckResult,
    GatewayExtraction,
    GatewayRun,
    cross_check,
)
from kernel.lib.lexi import choose

type Plan = tuple[str, int, int]

_REQUEST = CrossCheckRequest("SYN-TEN", "SYN-CASE", "SYN-DOC", ("10 20",), ("amount",))


def _choose(plans: Iterable[Plan]) -> Plan | None:
    return choose(
        plans, objective=lambda plan: (plan[1], plan[2]), stable_key=lambda plan: (plan[0],)
    )


def _extractor(provider: str, model: str, amount: str, start: int) -> GatewayExtraction:
    payload: dict[str, object] = {"amount": amount, "start": start}
    prompt = _REQUEST.pages[0]
    response = ModelCallResponse(
        compute_prompt_hash(prompt),
        compute_response_hash(payload),
        payload,
        1,
        1,
        0,
    )
    adapter = RecordedResponseAdapter.from_pairs([(prompt, response)])
    adapter.provider, adapter.model_id = provider, model
    gateway = Gateway(adapter)

    async def invoke(request: CrossCheckRequest) -> GatewayRun:
        schema = {
            "type": "object",
            "properties": {"amount": {"type": "string"}, "start": {"type": "integer"}},
            "required": ["amount", "start"],
        }
        call = ModelCallRequest(
            request.tenant_id, request.case_id, request.pages[0], schema, "middle", "extraction"
        )
        actual = await gateway.call(call)
        record = gateway.make_record(call, actual)
        value = cast(str, actual.response_payload["amount"])
        first = cast(int, actual.response_payload["start"])
        citation = Citation(value, FieldLocator(request.document_id, 0, first, first + len(value)))
        return GatewayRun(
            record.provider,
            record.model_id,
            record.prompt_hash,
            record.response_hash,
            {"amount": citation},
        )

    return invoke


def _check(primary: GatewayExtraction, secondary: GatewayExtraction | None) -> CrossCheckResult:
    return run(
        cross_check(
            _REQUEST, primary=primary, secondary=secondary, normalize=lambda _, value: value.strip()
        )
    )


@pytest.mark.fast
def test_T_LIB_0091() -> None:
    """Check choose the same plan across every input permutation.

    id: T-LIB-0091
    title: Choose the same plan across every input permutation
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Choose the same plan across every input permutation
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    plans = (("C", 2, 3), ("B", 1, 1), ("A", 1, 1))
    assert {_choose(order) for order in permutations(plans)} == {("A", 1, 1)}


@pytest.mark.fast
def test_T_LIB_0092() -> None:
    """Check prioritize the first objective above later costs or keys.

    id: T-LIB-0092
    title: Prioritize the first objective above later costs or keys
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Prioritize the first objective above later costs or keys
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    assert _choose((("A", 2, 0), ("Z", 1, 100))) == ("Z", 1, 100)


@pytest.mark.fast
def test_T_LIB_0093() -> None:
    """Check compare later objective fields before stable keys.

    id: T-LIB-0093
    title: Compare later objective fields before stable keys
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Compare later objective fields before stable keys
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    assert _choose((("A", 0, 4), ("Z", 0, 3))) == ("Z", 0, 3)


@pytest.mark.fast
def test_T_LIB_0094() -> None:
    """Check reject duplicate explicit plan keys.

    id: T-LIB-0094
    title: Reject duplicate explicit plan keys
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Reject duplicate explicit plan keys
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    with pytest.raises(ValueError, match="unique"):
        _choose((("A", 1, 2), ("A", 1, 3)))


@pytest.mark.fast
def test_T_LIB_0095() -> None:
    """Check return an empty choice for an empty feasible set.

    id: T-LIB-0095
    title: Return an empty choice for an empty feasible set
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Return an empty choice for an empty feasible set
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    assert _choose(()) is None


@pytest.mark.fast
def test_T_LIB_0096() -> None:
    """Check hold on grounded disagreement and record both citations.

    id: T-LIB-0096
    title: Hold on grounded disagreement and record both citations
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Hold on grounded disagreement and record both citations
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    result = _check(
        _extractor("provider-1", "model-1", "10", 0), _extractor("provider-2", "model-2", "20", 3)
    )
    item = result.comparisons[0]
    assert result.status == "HOLD" and item.reason == "DISAGREEMENT"
    assert item.primary is not None and item.primary.value == "10"
    assert item.secondary is not None and item.secondary.value == "20"
    assert item.value is None


@pytest.mark.fast
def test_T_LIB_0097() -> None:
    """Check record both independent model identifiers on agreement.

    id: T-LIB-0097
    title: Record both independent model identifiers on agreement
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Record both independent model identifiers on agreement
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    result = _check(
        _extractor("provider-1", "model-1", "10", 0), _extractor("provider-2", "model-2", "10", 0)
    )
    assert result.status == "AGREEMENT"
    assert tuple(run.model_id for run in result.runs) == ("model-1", "model-2")
    assert all(len(run.prompt_hash) == len(run.response_hash) == 64 for run in result.runs)
    assert result.comparisons[0].value == "10"


@pytest.mark.fast
def test_T_LIB_0098() -> None:
    """Check hold if the cited span does not support the value.

    id: T-LIB-0098
    title: Hold if the cited span does not support the value
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Hold if the cited span does not support the value
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    result = _check(
        _extractor("provider-1", "model-1", "10", 0), _extractor("provider-2", "model-2", "20", 0)
    )
    assert result.status == "HOLD"
    assert result.comparisons[0].reason == "UNGROUNDED"


@pytest.mark.fast
def test_T_LIB_0099() -> None:
    """Check hold if the independent extraction is unavailable.

    id: T-LIB-0099
    title: Hold if the independent extraction is unavailable
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Hold if the independent extraction is unavailable
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    result = _check(_extractor("provider-1", "model-1", "10", 0), None)
    assert result.status == "HOLD" and result.reason == "CROSSCHECK_UNAVAILABLE"
    assert len(result.runs) == 1 and not result.comparisons


@pytest.mark.fast
def test_T_LIB_0100() -> None:
    """Check prevent one model from counting as two independent calls.

    id: T-LIB-0100
    title: Prevent one model from counting as two independent calls
    purpose: Verify stable plan selection or independent grounded extraction
    level: fast
    requirement: P13-T08
    input: Synthetic candidate plans or recorded model responses
    expected: Prevent one model from counting as two independent calls
    risk: Plans change with input order or unsupported evidence reaches an outcome
    capability: shared-library
    """
    result = _check(
        _extractor("provider-1", "model-1", "10", 0), _extractor("provider-2", "model-1", "10", 0)
    )
    assert result.status == "HOLD" and result.reason == "MODELS_NOT_INDEPENDENT"
