"""Input contract for the document-driven walking skeleton."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from kernel.auth.roles import Principal
from kernel.decision import FactEntry
from kernel.ledger.chain import CaseChain
from kernel.types.decision import DecisionValue


@dataclass(frozen=True)
class SourceDocument:
    filename: str
    document_type: str
    payload: bytes
    parallel_group: str = ""


@dataclass(frozen=True)
class Judgment:
    """A versioned judgment supplied by the intake composition, with ledger evidence."""

    capability_id: str
    outcome: DecisionValue
    reasons: tuple[str, ...]
    evidence: Mapping[str, object]


@dataclass(frozen=True)
class IntakeInputs:
    facts: tuple[FactEntry, ...]
    required_keys: tuple[str, ...]
    decisions: tuple[tuple[DecisionValue, tuple[str, ...]], ...]
    data_origin: str
    judgments: tuple[Judgment, ...] = ()


class IntakePipelinePort(Protocol):
    async def ingest(
        self,
        principal: Principal,
        case_id: str,
        uploads: Sequence[SourceDocument],
        evaluation_time: str,
        *,
        chain: CaseChain | None = None,
    ) -> IntakeInputs: ...
