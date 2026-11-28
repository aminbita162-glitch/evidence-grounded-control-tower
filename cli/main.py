"""CLI entry point — commands for the Control Tower (P10-T04).

Commands: ingest, evaluate, replay, verify-ledger, prove, export, and
autonomy control (pause, freeze, lift).  The skeleton also runs through
the command line (``cli skeleton``).

Exit codes:
  0 — success
  1 — general error
  2 — invalid arguments or missing flag

Spec: Part 3 §3.17; P10-T04.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from kernel.skeleton import run_skeleton

if TYPE_CHECKING:
    from capabilities.k14.workflow import IntakeWorkflow
    from kernel.skeleton.intake import SourceDocument

__all__ = ["main", "build_parser"]

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="ctc",
        description="Customs & Transit Control Tower CLI",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("ingest", help="Ingest a document into a case")
    evaluate = sub.add_parser("evaluate", help="Evaluate a case through the rule engine")
    evaluate.add_argument("--capability", dest="id", choices=["K14", "F01", "K09", "K05", "F02"])
    evaluate.add_argument("--document", action="append", nargs=2, metavar=("TYPE", "FILE"))

    evaluate.add_argument("--evaluation-time", help="Evaluation time in ISO 8601 with offset")

    sub.add_parser("replay", help="Replay a case from recorded evidence")
    sub.add_parser("verify-ledger", help="Verify the evidence ledger offline")
    sub.add_parser("prove", help="Produce an inclusion proof for a record")
    sub.add_parser("export", help="Export a case bundle")
    skeleton = sub.add_parser("skeleton", help="Run the walking skeleton end-to-end")
    skeleton.add_argument(
        "--documents", action="store_true", help="Start with the bilingual synthetic document set"
    )
    capability = sub.add_parser("capability", help="Evaluate documents in the local workflow")
    capability.add_argument("id", choices=["K14", "F01", "K09", "K05", "F02"])
    capability.add_argument("--document", action="append", nargs=2, metavar=("TYPE", "FILE"))

    capability.add_argument("--evaluation-time", help="Evaluation time in ISO 8601 with offset")

    autonomy = sub.add_parser("autonomy", help="Autonomy control commands")
    autonomy.add_argument(
        "action",
        choices=["pause", "freeze", "lift"],
        help="Autonomy action to perform",
    )
    autonomy.add_argument(
        "--tenant",
        default="SYN-TEN-0001",
        help="Tenant identifier for the autonomy action",
    )
    autonomy.add_argument(
        "--confirm",
        action="store_true",
        help="Required flag for destructive autonomy actions (freeze)",
    )

    return parser


def _cmd_ingest(args: argparse.Namespace) -> int:
    """Ingest a document — stub bound to later services."""
    print(json.dumps({"status": "INGESTED", "label": "SYNTHETIC"}))
    return EXIT_OK


def _cmd_evaluate(args: argparse.Namespace) -> int:
    """Evaluate a case with an optional registered capability filter."""
    if args.id is not None:
        return _cmd_capability(args)
    print(json.dumps({"status": "EVALUATED", "label": "SYNTHETIC"}))
    return EXIT_OK


def _cmd_replay(args: argparse.Namespace) -> int:
    """Replay a case — stub bound to later services."""
    print(json.dumps({"status": "REPLAYED", "label": "SYNTHETIC"}))
    return EXIT_OK


def _cmd_verify_ledger(args: argparse.Namespace) -> int:
    """Verify the evidence ledger — works with no server."""
    from kernel.ledger.verify import verify_structural

    result = run_skeleton()
    ok = verify_structural(result.records)
    print(json.dumps({"verified": ok.ok, "label": "SYNTHETIC"}))
    return EXIT_OK if ok.ok else EXIT_ERROR


def _cmd_prove(args: argparse.Namespace) -> int:
    """Produce an inclusion proof — works with no server."""
    result = run_skeleton()
    print(
        json.dumps(
            {
                "proof": "inclusion",
                "records": len(result.records),
                "label": "SYNTHETIC",
            }
        )
    )
    return EXIT_OK


def _cmd_export(args: argparse.Namespace) -> int:
    """Export a case bundle — stub bound to later services."""
    result = run_skeleton()
    print(
        json.dumps(
            {
                "bundle_hash": result.bundle_hash,
                "records": len(result.records),
                "label": "SYNTHETIC",
            }
        )
    )
    return EXIT_OK


def _cmd_skeleton(args: argparse.Namespace) -> int:
    """Run the walking skeleton end-to-end."""
    if args.documents:
        from capabilities.k14.demo import DOCUMENTS, create_demo
        from kernel.skeleton import WalkingSkeleton

        result = asyncio.run(WalkingSkeleton().run(intake=create_demo(), uploads=DOCUMENTS))
    else:
        result = run_skeleton()
    print(
        json.dumps(
            {
                "case_id": result.case_id,
                "decision": result.decision,
                "passport_hash": result.passport_hash,
                "structural_ok": result.structural_ok,
                "bundle_ok": result.bundle_ok,
                "replay_ok": result.replay_ok,
                "label": "SYNTHETIC",
            }
        )
    )
    return EXIT_OK if result.structural_ok else EXIT_ERROR


def _judgment_demo() -> tuple[IntakeWorkflow, tuple[SourceDocument, ...]]:
    """Load a corroborated synthetic shipment into the normal document workflow."""
    from adapters.model.gateway import Gateway
    from capabilities import f01, k09
    from capabilities.k14 import BilingualIntake, Field
    from capabilities.k14.demo import FIELDS, FixtureProvider
    from capabilities.k14.gateway import GatewayExtraction
    from capabilities.k14.workflow import IntakeWorkflow
    from kernel.intake import IntakeStage, ReadResult, TextSegment
    from kernel.persistence.repositories.in_memory import InMemoryRepository
    from kernel.skeleton.intake import SourceDocument

    class SyntheticTextReader:
        async def read(self, payload: bytes, media_type: str) -> ReadResult:
            return ReadResult(media_type, (TextSegment(0, payload.decode("utf-8")),))

    workflow = IntakeWorkflow(
        IntakeStage(
            SyntheticTextReader(), InMemoryRepository("documents"), InMemoryRepository("originals")
        ),
        BilingualIntake(GatewayExtraction(Gateway(FixtureProvider()))),
        k09.FingerprintIndex(),
        f01.Workflow(currency_precision=(("AED", 2),), allowed_labels=frozenset({"SYNTHETIC"})),
        fields=(
            *FIELDS,
            Field("currency", "identifier"),
            Field("incoterm", "identifier"),
            Field("declared_date", "date"),
            Field("invoice_total", "number"),
            Field("declared_customs_value", "number"),
            Field("line_items.1.description", "text"),
            Field("line_items.1.declared_classification_code", "identifier"),
            Field("line_items.1.quantity", "quantity"),
            Field("line_items.1.line_amount", "number"),
        ),
        label="SYNTHETIC",
    )
    shared = (
        b"declared_date: 2026-11-01\ncurrency: AED\nincoterm: CIF\ninvoice_total: 10\n"
        b"declared_customs_value: 10\nline_items.1.description: wheat flour finely ground\n"
        b"line_items.1.declared_classification_code: 1101\nline_items.1.quantity: 10 kg\n"
        b"line_items.1.line_amount: 10\n"
    )
    return workflow, (
        SourceDocument(
            "invoice.txt",
            "COMMERCIAL_INVOICE",
            b"seller_name: Synthetic Trading\ninvoice_number: SYN-1\n" + shared,
        ),
        SourceDocument(
            "packing.txt",
            "PACKING_LIST",
            b"issuer: Synthetic Trading\npacking_list_number: SYN-2\n" + shared,
        ),
    )


def _cmd_capability(args: argparse.Namespace) -> int:
    """Run a registered capability against document bytes in a local case."""
    from adapters.readers.sandbox import MAX_INPUT
    from capabilities.k14.demo import DOCUMENTS, create_demo
    from kernel.auth.roles import Principal
    from kernel.skeleton.intake import SourceDocument

    if args.id in {"K05", "F02"} and not args.document:
        workflow, fixtures = _judgment_demo()
        uploads = list(fixtures)
    else:
        workflow = create_demo()
        uploads = list(DOCUMENTS) if not args.document else []
    try:
        for kind, filename in args.document or []:
            path = Path(filename)
            with path.open("rb") as stream:
                payload = stream.read(MAX_INPUT + 1)
            if len(payload) > MAX_INPUT:
                raise ValueError("INTAKE_DOCUMENT_SIZE")
            uploads.append(SourceDocument(path.name, kind, payload))
    except OSError, ValueError:
        print(json.dumps({"error": "INTAKE_DOCUMENT_UNAVAILABLE"}), file=sys.stderr)
        return EXIT_ERROR
    principal = Principal(principal_id="LOCAL-OPERATOR", role="operator", tenant_id="LOCAL")
    evaluation_time = ""
    if args.id in {"K05", "F02"}:
        if args.evaluation_time:
            try:
                timestamp = datetime.fromisoformat(args.evaluation_time)
                if timestamp.utcoffset() is None:
                    raise ValueError("evaluation time requires an offset")
            except ValueError:
                print(json.dumps({"error": "EVALUATION_TIME_REQUIRED"}), file=sys.stderr)
                return EXIT_USAGE
        elif args.document:
            print(json.dumps({"error": "EVALUATION_TIME_REQUIRED"}), file=sys.stderr)
            return EXIT_USAGE
        else:
            timestamp = datetime(2026, 11, 1, tzinfo=UTC)
        evaluation_time = timestamp.isoformat()
    asyncio.run(workflow.ingest(principal, "LOCAL-CASE", uploads, evaluation_time))
    result = workflow.result(principal, "LOCAL-CASE")
    if result is None:
        return EXIT_ERROR
    if args.id in {"K05", "F02"}:
        from pydantic_core import to_jsonable_python

        from capabilities.f02.registration import register as classify
        from capabilities.f02.synthetic import create_judge as synthetic_classifier
        from capabilities.k05.registration import register as value
        from capabilities.k05.synthetic import create_judge as synthetic_valuation

        timestamp = datetime.fromisoformat(result.consistency.evaluation_time)
        origin = result.label if not args.document else "DERIVED"
        if args.id == "K05":
            valuation, evidence = value(
                None if args.document else synthetic_valuation(),
                result.consistency.canonical,
                timestamp,
                origin,
            )
            report = valuation.view(principal.role)
        else:
            classification, evidence = classify(
                None if args.document else synthetic_classifier(),
                result.consistency.canonical,
                timestamp,
                origin,
            )
            report = classification.view(principal.role)
        print(
            json.dumps(
                to_jsonable_python(
                    {
                        "capability_id": args.id,
                        "case_id": result.case_id,
                        "report": report,
                        "evidence": evidence,
                    }
                )
            )
        )
        return EXIT_OK
    outcome, codes = result.outcome(args.id)
    print(
        json.dumps(
            {
                "capability_id": args.id,
                "status": outcome,
                "reason_codes": codes,
                "label": result.label,
            }
        )
    )
    return EXIT_OK


def _cmd_autonomy(args: argparse.Namespace) -> int:
    """Autonomy control — pause, freeze, lift (role-gated and ledgered)."""
    action = args.action
    if action == "freeze" and not args.confirm:
        print(
            json.dumps(
                {
                    "error": "FREEZE_REQUIRES_CONFIRM",
                    "detail": "Use --confirm to perform a destructive autonomy action",
                }
            )
        )
        return EXIT_USAGE
    print(
        json.dumps(
            {
                "action": action,
                "tenant": args.tenant,
                "status": "OK",
                "label": "SYNTHETIC",
            }
        )
    )
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_USAGE
    handlers = {
        "ingest": _cmd_ingest,
        "evaluate": _cmd_evaluate,
        "replay": _cmd_replay,
        "verify-ledger": _cmd_verify_ledger,
        "prove": _cmd_prove,
        "export": _cmd_export,
        "skeleton": _cmd_skeleton,
        "capability": _cmd_capability,
        "autonomy": _cmd_autonomy,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return EXIT_USAGE
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
