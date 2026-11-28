"""Run validated OCR in the parser worker and return logical-order lines."""

from __future__ import annotations

import csv
import io
import subprocess  # nosec B404
from pathlib import Path


def extract(payload: bytes, program: Path, version: str) -> dict[str, object]:
    observed = (
        subprocess.run(  # nosec B603  # noqa: S603
            [str(program), "--version"],
            capture_output=True,
            check=True,
            timeout=3,
        )
        .stdout.decode(errors="replace")
        .splitlines()
    )
    if not observed or observed[0].strip() != version:
        return {"reason": "TEXT_UNAVAILABLE"}
    output = subprocess.run(  # nosec B603  # noqa: S603
        [
            str(program),
            "stdin",
            "stdout",
            "--tessdata-dir",
            str(program.parent),
            "-l",
            "eng+ara",
            "tsv",
        ],
        input=payload,
        capture_output=True,
        check=True,
        timeout=8,
    ).stdout.decode()
    lines: dict[tuple[int, int, int, int], list[tuple[str, float, int, int, int, int]]] = {}
    for row in csv.DictReader(io.StringIO(output), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row["level"] != "5" or not row["text"].strip():
            continue
        key = (
            int(row["page_num"]),
            int(row["block_num"]),
            int(row["par_num"]),
            int(row["line_num"]),
        )
        confidence = float(row["conf"])
        left, top, width, height = (int(row[name]) for name in ("left", "top", "width", "height"))
        if not 0 <= confidence <= 100 or min(left, top, width, height) < 0:
            raise ValueError("OCR_LOCATOR_INVALID")
        lines.setdefault(key, []).append(
            (row["text"], confidence, left, top, left + width, top + height),
        )
    segments = []
    for key, words in sorted(lines.items()):
        left = min(row[2] for row in words)
        top = min(row[3] for row in words)
        segments.append(
            {
                "page": key[0] - 1,
                "text": " ".join(row[0] for row in words),
                "confidence": min(row[1] for row in words),
                "box": (
                    left,
                    top,
                    max(row[4] for row in words) - left,
                    max(row[5] for row in words) - top,
                ),
            }
        )
    return {"segments": segments}
