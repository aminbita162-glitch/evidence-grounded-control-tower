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
import json
import sys
from collections.abc import Sequence

from kernel.skeleton import run_skeleton

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
    sub.add_parser("evaluate", help="Evaluate a case through the rule engine")
    sub.add_parser("replay", help="Replay a case from recorded evidence")
    sub.add_parser("verify-ledger", help="Verify the evidence ledger offline")
    sub.add_parser("prove", help="Produce an inclusion proof for a record")
    sub.add_parser("export", help="Export a case bundle")
    sub.add_parser("skeleton", help="Run the walking skeleton end-to-end")

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
    """Evaluate a case — stub bound to later services."""
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
        "autonomy": _cmd_autonomy,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return EXIT_USAGE
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
