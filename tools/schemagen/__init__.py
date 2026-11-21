"""Schema generator for the Control Tower kernel contracts.

Reads JSON Schema files from ``schemas/`` and generates frozen, strictly
typed Pydantic v2 models into ``kernel/contracts/_generated/``.

The generator is reproducible: the same schema files always produce
byte-identical output. Every generated file carries a header marker so the
``generated-files`` gate can detect hand edits.
"""

from tools.schemagen.generator import generate_all, regenerate

__all__ = ["generate_all", "regenerate"]
