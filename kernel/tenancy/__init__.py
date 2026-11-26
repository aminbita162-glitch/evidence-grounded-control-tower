"""Kernel tenancy — configuration, activation and freeze (P11-T04).

Per-tenant budgets, rate limits, retention classes, autonomy policy and
pack activation set, recorded on the tenant system chain.  Tenant
overlays may add rules and never remove deployment rules.  Tenant freeze
integrates with the P07 kill switches.  The region profile is stored
with the tenant configuration; narrowing and widening follow the roles
of Part 3 §3.24.

Spec: Part 3 §3.24, §3.30; Part 4 §4.4; P11-T04.
"""

from __future__ import annotations

from kernel.tenancy.activation import (
    OverlayError,
    PackActivationSet,
)
from kernel.tenancy.config import (
    REGION_LOCAL_ONLY,
    TenantConfig,
    TenantConfigError,
    TenantSystemChain,
)
from kernel.tenancy.freeze import (
    FREEZE_PROBLEM_CODE,
    TenantFreeze,
    TenantFreezeError,
)

__all__ = [
    "TenantConfig",
    "TenantConfigError",
    "TenantSystemChain",
    "REGION_LOCAL_ONLY",
    "TenantFreeze",
    "TenantFreezeError",
    "FREEZE_PROBLEM_CODE",
    "PackActivationSet",
    "OverlayError",
]
