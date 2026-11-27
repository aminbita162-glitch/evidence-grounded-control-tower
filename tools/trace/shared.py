"""Read the shared-module catalogue and its Phase 13 proof links."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CatalogueEntry:
    """One documented shared-module row."""

    name: str
    phase: str
    consumers: str


@dataclass(frozen=True, slots=True)
class ModuleRequirement:
    """Path and proof for one Phase 13 shared-module requirement."""

    module: str
    catalogue: str
    requirement: str
    test_id: str


_MONEY_GROUP = "Money and rounding, calculation trace, unblock generator, tenant feed validator"

REQUIREMENTS = (
    ModuleRequirement("money", _MONEY_GROUP, "P13-T02", "T-LIB-0101"),
    ModuleRequirement("calctrace", _MONEY_GROUP, "P13-T03", "T-LIB-0102"),
    ModuleRequirement("unblock", _MONEY_GROUP, "P13-T04", "T-LIB-0103"),
    ModuleRequirement("feeds", _MONEY_GROUP, "P13-T05", "T-LIB-0104"),
    ModuleRequirement("conformal", "Conformal core", "P13-T06", "T-LIB-0105"),
    ModuleRequirement(
        "solve",
        "Solver harness with independent verifier scaffold, Z3 harness",
        "P13-T07",
        "T-LIB-0106",
    ),
    ModuleRequirement("lexi", "Lexicographic stability helper", "P13-T08", "T-LIB-0107"),
    ModuleRequirement("crosscheck", "Model cross-check helper", "P13-T08", "T-LIB-0108"),
)


def read_catalogue(directive: str) -> tuple[CatalogueEntry, ...]:
    """Read the shared-module table in Part 6, preserving its published order."""
    block = directive.partition("<<<P6-S10>>>")[2].partition("<<<P6-S11>>>")[0]
    entries: list[CatalogueEntry] = []
    for row in block.splitlines():
        if not row.startswith("|") or row.startswith("|---"):
            continue
        name, phase, consumers = [cell.strip() for cell in row.strip("|").split("|")]
        if name != "Module":
            entries.append(CatalogueEntry(name, phase, consumers))
    return tuple(entries)
