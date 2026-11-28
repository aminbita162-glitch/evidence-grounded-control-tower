"""Record F03 clock evaluations and render an accessible timeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import escape

from pydantic import ConfigDict, TypeAdapter

from capabilities.f03 import CaseClocks, ContainerClock, Reason, evaluate
from kernel.hashing import domain_hash
from kernel.lib.money import CurrencyTable

CAPABILITY_ID = "F03"


@dataclass(frozen=True, slots=True)
class ClockInput:
    __pydantic_config__ = ConfigDict(extra="forbid")

    clocks: tuple[ContainerClock, ...]
    currencies: dict[str, int]
    currency_source: str
    canonical_containers: frozenset[str]
    synthetic: bool = False


INPUT = TypeAdapter(ClockInput)
OUTPUT = TypeAdapter(CaseClocks)


def register(data: ClockInput, at: datetime) -> tuple[CaseClocks, dict[str, object]]:
    """Bind each report to the committed input, configuration and evaluation time."""
    result = evaluate(
        data.clocks,
        at,
        CurrencyTable(data.currencies, data.currency_source),
        data.canonical_containers,
        synthetic=data.synthetic,
    )
    inputs = INPUT.dump_python(data, mode="json")
    inputs["canonical_containers"] = sorted(data.canonical_containers)
    for clock in inputs["clocks"]:
        if clock["calendar"] is not None:
            clock["calendar"]["weekend"].sort()
            clock["calendar"]["holidays"].sort()
    output = OUTPUT.dump_python(result, mode="json")
    source = {
        "terms": sorted({(c.terms.source_id, c.terms.version) for c in data.clocks if c.terms}),
        "calendars": sorted(
            {(c.calendar.source_id, c.calendar.version) for c in data.clocks if c.calendar}
        ),
        "currency_source": data.currency_source,
        "currencies": data.currencies,
    }
    return result, {
        "capability_id": CAPABILITY_ID,
        "evaluation_time": at.isoformat(),
        "configuration_hash": domain_hash("ctc/payload/v1", source),
        "input_hash": domain_hash("ctc/payload/v1", inputs),
        "output_hash": domain_hash("ctc/payload/v1", output),
        "clock_records": [
            {
                "container": row["container"],
                "charge_kind": row["charge_kind"],
                "output_hash": domain_hash("ctc/payload/v1", row),
            }
            for row in output["clocks"]
        ],
    }


def render_timeline(result: CaseClocks) -> str:
    """Render each clock as a timeline with text equivalents for its bars."""
    sections = []
    for clock in result.clocks:
        title = escape(f"{clock.container} · {clock.charge_kind}")
        events = "".join(
            f"<li>{escape(event.kind)} {escape(event.instant.isoformat())}"
            f" ({escape(event.source_id)})</li>"
            for event in clock.timeline
        )
        windows = "".join(
            f"<li>{escape(window.start.isoformat())} to {escape(window.end.isoformat())}"
            f" ({escape(window.source_id)})</li>"
            for window in clock.suspensions
        )
        projections = "".join(
            f"<li>{escape(row.action)} by {escape(row.latest_effective.isoformat())} · "
            f"{row.savings} {escape(clock.currency or '')} projected savings "
            f"at +{row.days_ahead} days</li>"
            for row in clock.projections
        )
        periods = ""
        if clock.free_expiry is not None:
            periods = (
                f"<p>Free period ends {escape(clock.free_expiry.isoformat())}. "
                f"Remaining {escape(str(clock.remaining))}.</p>"
                '<div class="clock-bar free" aria-hidden="true"></div>'
                f"<p>Accrual {clock.charge} {escape(clock.currency or '')} "
                f"for {clock.chargeable_days} tariff days.</p>"
                '<div class="clock-bar accrual" aria-hidden="true"></div>'
            )
        state_label = (
            "Review recorded milestones" if clock.reason is Reason.ORDER else clock.state.value
        )
        sections.append(
            f"<article><h3>{title}</h3><p>{escape(state_label)}</p>{periods}"
            f"<h4>Events</h4><ol>{events}</ol><h4>Verified suspensions</h4><ul>{windows}</ul>"
            f"<h4>Action options</h4><ul>{projections}</ul></article>"
        )
    return '<section id="f03" aria-label="Container clocks">' + "".join(sections) + "</section>"
