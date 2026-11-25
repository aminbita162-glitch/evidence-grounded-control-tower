"""Model provider adapters (D-06, P08-T02).

Three adapters behind the same contract test suite:
- :class:`~adapters.model.providers.primary.PrimaryAdapter` — primary commercial provider
- :class:`~adapters.model.providers.secondary.SecondaryAdapter` — second commercial provider
- :class:`~adapters.model.providers.local.LocalAdapter` — locally hosted open-weights model

All adapters are exercised against local mock servers, never a live service.
"""

from __future__ import annotations

from adapters.model.providers.local import LocalAdapter
from adapters.model.providers.primary import PrimaryAdapter
from adapters.model.providers.secondary import SecondaryAdapter

__all__ = [
    "PrimaryAdapter",
    "SecondaryAdapter",
    "LocalAdapter",
]
