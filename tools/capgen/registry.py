"""Check the phase and capability dependency registries."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

_CAP_ID = r"\b[FKL]\d{2}\b"
_HEADER = re.compile(r"^H: ([FKL]\d{2}) · .*? · depends: (.*?) · output:", re.M)
_INTERFACE = re.compile(r"^T10 Interfaces?\.(.*)$", re.M)
_INPUT = re.compile(r"^T2 Inputs?\..*?(?=^T3 |\Z)", re.M | re.S)


@dataclass(frozen=True, slots=True)
class CapabilityEntry:
    """Declared edges and input scope of one capability."""

    depends: tuple[str, ...] = ()
    inputs: tuple[str, ...] = ()
    tenant_scope: bool = False


def read_capabilities(directive: str) -> dict[str, CapabilityEntry]:
    """Read dependencies and explicit scope and inputs from capability sections."""
    entries: dict[str, CapabilityEntry] = {}
    headers = list(_HEADER.finditer(directive))
    for index, header in enumerate(headers):
        capability, dependencies = header.groups()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(directive)
        section = directive[header.end() : end]
        interface = _INTERFACE.search(section)
        inputs = _INPUT.search(section)
        tenant_scope = bool(interface and "tenant-scope route" in interface[1].lower())
        # The Passport excludes the cross-case reconciliation report explicitly.
        entries[capability] = CapabilityEntry(
            tuple(re.findall(_CAP_ID, dependencies)),
            tuple(re.findall(_CAP_ID, inputs[0])) if inputs else (),
            tenant_scope or capability == "K03",
        )
    return entries


def dependency_errors(graph: Mapping[str, tuple[str, ...]]) -> list[str]:
    """Report unknown dependencies and dependency cycles with their paths."""
    visiting: list[str] = []
    visited: set[str] = set()
    errors: list[str] = []

    def visit(node: str) -> None:
        if node in visiting:
            cycle = visiting[visiting.index(node) :] + [node]
            errors.append(f"dependency cycle: {' -> '.join(cycle)}")
            return
        if node in visited:
            return
        visiting.append(node)
        for dependency in sorted(set(graph[node])):
            if dependency in graph:
                visit(dependency)
            else:
                errors.append(f"{node}: unknown dependency {dependency}")
        visiting.pop()
        visited.add(node)

    for node in sorted(graph):
        visit(node)
    return errors


def capability_errors(entries: Mapping[str, CapabilityEntry]) -> list[str]:
    """Enforce dependency integrity and the case-only Passport boundary."""
    errors = dependency_errors({key: entry.depends for key, entry in entries.items()})
    passport = entries.get("F06")
    if passport is not None:
        for source in sorted(set(passport.depends + passport.inputs)):
            if source in entries and entries[source].tenant_scope:
                errors.append(f"F06: tenant-scope capability {source} cannot supply Passport input")
    return errors
