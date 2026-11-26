"""Role definitions and boundaries (Part 3 §3.15, §3.24, P11-T01).

Roles: viewer, operator, reviewer, administrator (tenant-bound) and
platform operator (no tenant, deployment routes only, no tenant data
access).  The tenant is derived from the credential only and never from
a request field, header or path parameter.

Spec: Part 3 §3.15, §3.24; P11-T01.
"""

from __future__ import annotations

from typing import Literal, Protocol

__all__ = [
    "RoleType",
    "ROLE_VIEWER",
    "ROLE_OPERATOR",
    "ROLE_REVIEWER",
    "ROLE_ADMINISTRATOR",
    "ROLE_PLATFORM",
    "ALL_ROLES",
    "TENANT_BOUND_ROLES",
    "PLATFORM_ROLE",
    "RoleError",
    "Principal",
    "RolePolicy",
    "DEPLOYMENT_ROUTES",
]

RoleType = Literal["viewer", "operator", "reviewer", "administrator", "platform"]

ROLE_VIEWER: RoleType = "viewer"
ROLE_OPERATOR: RoleType = "operator"
ROLE_REVIEWER: RoleType = "reviewer"
ROLE_ADMINISTRATOR: RoleType = "administrator"
ROLE_PLATFORM: RoleType = "platform"

ALL_ROLES: frozenset[str] = frozenset(
    {ROLE_VIEWER, ROLE_OPERATOR, ROLE_REVIEWER, ROLE_ADMINISTRATOR, ROLE_PLATFORM}
)

TENANT_BOUND_ROLES: frozenset[str] = frozenset(
    {ROLE_VIEWER, ROLE_OPERATOR, ROLE_REVIEWER, ROLE_ADMINISTRATOR}
)

PLATFORM_ROLE: str = ROLE_PLATFORM

#: Routes reachable by the platform credential (deployment routes only).
DEPLOYMENT_ROUTES: frozenset[str] = frozenset(
    {"/api/v1/health", "/api/v1/health/live", "/api/v1/health/ready"}
)


class RoleError(ValueError):
    """Raised when a role boundary is violated or a credential is invalid."""


class Principal:
    """The identity bound to a tenant scope (Part 3 §3.24).

    Attributes:
        principal_id: opaque user or component id.
        role: one of the five roles.
        tenant_id: tenant id, or None for the platform credential.
    """

    __slots__ = ("_principal_id", "_role", "_tenant_id")

    def __init__(
        self,
        *,
        principal_id: str,
        role: RoleType,
        tenant_id: str | None = None,
    ) -> None:
        """Create a principal.

        Args:
            principal_id: opaque identity.
            role: one of the five roles.
            tenant_id: tenant id, or None only for the platform role.

        Raises:
            RoleError: if the platform role has a tenant or a tenant-bound
                role has no tenant.
        """
        if not principal_id:
            raise RoleError("principal_id is required")
        if role not in ALL_ROLES:
            raise RoleError(f"unknown role: {role}")
        if role == PLATFORM_ROLE:
            if tenant_id is not None:
                raise RoleError("platform role must not carry a tenant")
        elif tenant_id is None or not tenant_id:
            raise RoleError(f"role {role} requires a tenant_id")
        self._principal_id = principal_id
        self._role: RoleType = role
        self._tenant_id: str | None = tenant_id

    @property
    def principal_id(self) -> str:
        """The opaque principal id."""
        return self._principal_id

    @property
    def role(self) -> RoleType:
        """The role."""
        return self._role

    @property
    def tenant_id(self) -> str | None:
        """The tenant id, or None for the platform credential."""
        return self._tenant_id

    @property
    def is_platform(self) -> bool:
        """True if this principal is the platform operator (no tenant)."""
        return self._role == PLATFORM_ROLE

    @property
    def is_tenant_bound(self) -> bool:
        """True if this principal is bound to a tenant."""
        return self._tenant_id is not None

    @property
    def is_reviewer(self) -> bool:
        """True if this principal has the reviewer role."""
        return self._role == ROLE_REVIEWER

    def can_access_route(self, route: str) -> bool:
        """Check whether this principal may access the given route.

        The platform credential reaches only deployment routes.
        Tenant-bound principals reach all tenant-scoped routes.

        Args:
            route: the API route path.

        Returns:
            True if the route is allowed.
        """
        if self.is_platform:
            return route in DEPLOYMENT_ROUTES
        return True

    def can_approve(self) -> bool:
        """True if this principal may approve proposals (reviewer role)."""
        return self._role == ROLE_REVIEWER

    def can_operate(self) -> bool:
        """True if this principal may perform operator actions."""
        return self._role in (ROLE_OPERATOR, ROLE_ADMINISTRATOR)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Principal(id={self._principal_id!r}, role={self._role!r})"


class RolePolicy(Protocol):
    """Policy for checking role-based access to routes and operations."""

    def can_access(self, principal: Principal, route: str, *, is_tenant_scoped: bool) -> bool:
        """Check whether *principal* may access *route*.

        Args:
            principal: the authenticated principal.
            route: the route path.
            is_tenant_scoped: whether the route is tenant-scoped.

        Returns:
            True if access is allowed; False if denied.
        """
        ...


class DefaultRolePolicy:
    """Default role policy (Part 3 §3.15, §3.24).

    A platform credential is denied every tenant-scoped route.
    Tenant-bound principals may access tenant-scoped routes.
    Every platform action is recorded on the deployment chain.
    """

    def can_access(self, principal: Principal, route: str, *, is_tenant_scoped: bool) -> bool:
        """Check route access.

        Args:
            principal: the authenticated principal.
            route: the route path.
            is_tenant_scoped: whether the route is tenant-scoped.

        Returns:
            True if access is allowed.
        """
        if principal.is_platform:
            if is_tenant_scoped:
                return False
            return route in DEPLOYMENT_ROUTES
        if not is_tenant_scoped:
            return route in DEPLOYMENT_ROUTES or route.startswith("/api/")
        return True


def enforce_role_boundary(
    principal: Principal,
    route: str,
    *,
    is_tenant_scoped: bool,
    policy: RolePolicy | None = None,
) -> None:
    """Raise RoleError if the principal may not access the route.

    Args:
        principal: the authenticated principal.
        route: the route path.
        is_tenant_scoped: whether the route is tenant-scoped.
        policy: optional policy; defaults to DefaultRolePolicy.

    Raises:
        RoleError: if access is denied.
    """
    pol: RolePolicy = policy or DefaultRolePolicy()
    if not pol.can_access(principal, route, is_tenant_scoped=is_tenant_scoped):
        raise RoleError(f"role {principal.role} denied access to {route}")


def derive_tenant_from_credential(
    principal: Principal,
    body_tenant: str | None = None,
    header_tenant: str | None = None,
    path_tenant: str | None = None,
    claim_tenant: str | None = None,
) -> str | None:
    """Derive the tenant from the credential only (Part 3 §3.24).

    The tenant is never taken from a request body, header, path or claim.
    Only the credential-bound tenant is used.  A platform credential
    carries no tenant.

    Args:
        principal: the authenticated principal.
        body_tenant: ignored (never used).
        header_tenant: ignored (never used).
        path_tenant: ignored (never used).
        claim_tenant: ignored (never used).

    Returns:
        The tenant id from the credential, or None for the platform role.
    """
    _ = (body_tenant, header_tenant, path_tenant, claim_tenant)
    return principal.tenant_id
