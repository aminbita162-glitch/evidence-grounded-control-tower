"""Tenant context for row-level security (P04-T03).

A :class:`TenantContext` binds a tenant identifier to the principal that
initiated the operation.  It cannot be constructed without a principal
(Part 3 §3.24): the principal is the identity (user id or role) that
authorises the tenant scope.

The context is passed to repositories and used to set the transaction-local
database setting ``ctc.tenant_id`` at the start of each transaction.

Spec: Part 3 §3.24; Part 4 §4.4; P04-T03.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "TenantContext",
    "TenantContextError",
]

_TENANT_SETTING = "ctc.tenant_id"


class TenantContextError(ValueError):
    """Raised when a tenant context is invalid (missing principal or tenant)."""


@dataclass(frozen=True)
class TenantContext:
    """Tenant scope bound to a principal (Part 3 §3.24).

    Attributes:
        tenant_id: the tenant identifier.
        principal: the identity (user id or role) that authorises the scope.
    """

    tenant_id: str
    principal: str

    def __post_init__(self) -> None:
        if not self.tenant_id:
            raise TenantContextError("tenant_id is required")
        if not self.principal:
            raise TenantContextError("principal is required")

    @property
    def setting_name(self) -> str:
        """The PostgreSQL setting key for the transaction-local tenant."""
        return _TENANT_SETTING

    def set_sql(self) -> str:
        """Return the SQL statement to set the tenant in the current transaction."""
        return f"SET LOCAL {_TENANT_SETTING} = '{self.tenant_id}'"
