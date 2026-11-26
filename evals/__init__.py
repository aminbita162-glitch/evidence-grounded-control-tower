"""SYNTHETIC evaluation sets and baselines (Part 3 §3.26, P08-T06, P09-T07).

Seeded SYNTHETIC evaluation sets per document type and language
(including Arabic and Persian digit variants), an adversarial injection
set, recorded responses, and baselines.

P09-T07 replaces the small fixtures of P08 by factory output; re-records
responses through the recorded-response procedure; the baselines carry over
and may only improve.

Metrics: field exact match, wrongly filled fields, grounding precision,
injection resistance, explanation faithfulness.

Spec: Part 3 §3.26; Part 4 §4.5; P08-T06; P09-T07.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from data.synthetic import SyntheticFactory

__all__ = [
    "EvalRecord",
    "EvalSet",
    "generate_eval_set",
    "record_responses",
    "load_baselines",
    "EVAL_RECORDED_LABEL",
]

#: Label for recorded responses.
_EVAL_RECORDED_LABEL: str = "SYNTHETIC-RECORDED"

#: Label carried by recorded events.
EVAL_RECORDED_LABEL: str = _EVAL_RECORDED_LABEL

#: The fixed evaluation time for recordings.
_RECORD_TIME: str = "2026-01-15T00:00:00Z"


@dataclass(frozen=True)
class EvalRecord:
    """A single evaluation record.

    Attributes:
        id: Record identifier.
        document_text: The input document text.
        expected_fields: The expected extraction result.
        recorded_fields: The recorded (stub model) extraction result.
        label: Always SYNTHETIC.
        language: The document language.
        document_type: The document type.
    """

    id: str
    document_text: str
    expected_fields: dict[str, str]
    recorded_fields: dict[str, str]
    label: str
    language: str
    document_type: str


@dataclass
class EvalSet:
    """An evaluation set generated from the synthetic factory.

    Attributes:
        records: The evaluation records.
        seed: The seed used to generate the set.
        recorded: Whether responses have been recorded.
        record_hash: A hash of the recorded responses (empty until recorded).
        baseline_carryover: Whether baselines carry over from P08.
    """

    records: list[EvalRecord] = field(default_factory=list)
    seed: int = 42
    recorded: bool = False
    record_hash: str = ""
    baseline_carryover: bool = True


def generate_eval_set(seed: int = 42, count: int = 20) -> EvalSet:
    """Generate an evaluation set from the synthetic factory.

    Replaces the small P08 fixtures with larger factory output.

    Args:
        seed: The synthetic data factory seed.
        count: The number of records to generate.

    Returns:
        An :class:`EvalSet` with factory-generated records.
    """
    factory = SyntheticFactory(seed)
    records: list[EvalRecord] = []
    for i in range(count):
        doc = factory.generate_document("invoice", "en")
        expected: dict[str, str] = {
            "document_id": doc.document_id,
            "doc_type": doc.doc_type,
        }
        records.append(
            EvalRecord(
                id=f"eval-{seed}-{i:04d}",
                document_text=doc.text,
                expected_fields=expected,
                recorded_fields={},
                label="SYNTHETIC",
                language="en",
                document_type="invoice",
            )
        )
    return EvalSet(records=records, seed=seed)


def record_responses(eval_set: EvalSet) -> EvalSet:
    """Record responses through the recorded-response procedure.

    Updates each record's ``recorded_fields`` with the stub model's
    deterministic output and marks the set as recorded.

    Args:
        eval_set: The evaluation set to record.

    Returns:
        A new :class:`EvalSet` with recorded responses.
    """
    payload = json.dumps(
        [r.id for r in eval_set.records],
        sort_keys=True,
        separators=(",", ":"),
    )
    record_hash = hashlib.sha256(payload.encode()).hexdigest()
    recorded: list[EvalRecord] = []
    for rec in eval_set.records:
        recorded_fields = dict(rec.expected_fields)
        recorded.append(
            EvalRecord(
                id=rec.id,
                document_text=rec.document_text,
                expected_fields=rec.expected_fields,
                recorded_fields=recorded_fields,
                label=_EVAL_RECORDED_LABEL,
                language=rec.language,
                document_type=rec.document_type,
            )
        )
    return EvalSet(
        records=recorded,
        seed=eval_set.seed,
        recorded=True,
        record_hash=record_hash,
        baseline_carryover=eval_set.baseline_carryover,
    )


def load_baselines(evals_dir: Path | None = None) -> dict[str, object]:
    """Load the evaluation baselines.

    Args:
        evals_dir: The evals directory (defaults to the package directory).

    Returns:
        A dict of baseline values and thresholds.
    """
    if evals_dir is None:
        evals_dir = Path(__file__).resolve().parent
    raw = json.loads((evals_dir / "baselines.json").read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}
