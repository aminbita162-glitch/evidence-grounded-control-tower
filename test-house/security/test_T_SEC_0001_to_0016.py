"""Authentication and roles tests (P11-T01).

Test IDs: T-SEC-0001 to T-SEC-0016.
Covers: token never stored in clear; expired or revoked token fails;
forged tenant in body, header, path and claims ignored or rejected;
each role boundary enforced on every operation.

Spec: Part 3 §3.15, §3.24; Part 4 §4.5; P11-T01.
"""

from __future__ import annotations

import asyncio

import pytest

from kernel.auth.roles import (
    DEPLOYMENT_ROUTES,
    ROLE_ADMINISTRATOR,
    ROLE_OPERATOR,
    ROLE_PLATFORM,
    ROLE_REVIEWER,
    ROLE_VIEWER,
    Principal,
    RoleError,
    derive_tenant_from_credential,
    enforce_role_boundary,
)
from kernel.auth.sessions import (
    DevSessionSigner,
    SessionError,
    create_session_cookie,
    verify_session_cookie,
)
from kernel.auth.tokens import (
    InMemoryTokenStore,
    TokenError,
    TokenService,
    hash_token,
)

# ---------------------------------------------------------------------------
# T-SEC-0001: a token is never stored in clear
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0001_token_never_stored_in_clear() -> None:
    """T-SEC-0001: a token is never stored in clear.

    id: T-SEC-0001
    title: Token never stored in clear
    purpose: Verify that only the SHA-256 hash is stored, not the cleartext.
    level: fast
    requirement: PR-06; Part 3 §3.15; P11-T01
    input: TokenService.create_token then inspect store
    expected: store contains hash, not cleartext
    risk: cleartext token leaked
    owning capability: security
    """
    store = InMemoryTokenStore()
    service = TokenService(store)
    token, record = service.create_token(
        principal_id="user-1",
        role=ROLE_VIEWER,
        tenant_id="tenant-a",
    )
    asyncio.run(store.store(record))
    stored = asyncio.run(store.get(record.token_hash))
    assert stored is not None
    assert stored.token_hash == hash_token(token)
    for key in store.all_hashes():
        assert key != token


# ---------------------------------------------------------------------------
# T-SEC-0002: an expired token fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0002_expired_token_fails() -> None:
    """T-SEC-0002: an expired token fails authentication.

    id: T-SEC-0002
    title: Expired token fails
    purpose: Verify that an expired token raises TokenError.
    level: fast
    requirement: PR-06; Part 3 §3.15; P11-T01
    input: token with past expiry
    expected: TokenError raised
    risk: stale credentials accepted
    owning capability: security
    """
    store = InMemoryTokenStore()
    service = TokenService(store)
    token, record = service.create_token(
        principal_id="user-1",
        role=ROLE_VIEWER,
        tenant_id="tenant-a",
        expires_at="2025-01-01T00:00:00Z",
    )
    asyncio.run(store.store(record))
    with pytest.raises(TokenError, match="expired"):
        asyncio.run(service.verify_token(token, current_time="2026-06-01T00:00:00Z"))


# ---------------------------------------------------------------------------
# T-SEC-0003: a revoked token fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0003_revoked_token_fails() -> None:
    """T-SEC-0003: a revoked token fails authentication.

    id: T-SEC-0003
    title: Revoked token fails
    purpose: Verify that a revoked token raises TokenError.
    level: fast
    requirement: PR-06; Part 3 §3.15; P11-T01
    input: valid token then revoke
    expected: TokenError raised after revocation
    risk: revoked credentials still valid
    owning capability: security
    """
    store = InMemoryTokenStore()
    service = TokenService(store)
    token, record = service.create_token(
        principal_id="user-1",
        role=ROLE_VIEWER,
        tenant_id="tenant-a",
    )
    asyncio.run(store.store(record))
    principal = asyncio.run(service.verify_token(token))
    assert principal is not None
    asyncio.run(service.revoke_token(token))
    with pytest.raises(TokenError, match="revoked"):
        asyncio.run(service.verify_token(token))


# ---------------------------------------------------------------------------
# T-SEC-0004: forged tenant in body is ignored
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0004_forged_tenant_body_ignored() -> None:
    """T-SEC-0004: a forged tenant in the request body is ignored.

    id: T-SEC-0004
    title: Forged tenant in body ignored
    purpose: Verify the tenant is never taken from the request body.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: principal with tenant-a, body claims tenant-b
    expected: derived tenant is tenant-a
    risk: tenant forgery via body
    owning capability: security
    """
    principal = Principal(principal_id="user-1", role=ROLE_VIEWER, tenant_id="tenant-a")
    result = derive_tenant_from_credential(principal, body_tenant="tenant-b")
    assert result == "tenant-a"


# ---------------------------------------------------------------------------
# T-SEC-0005: forged tenant in header is ignored
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0005_forged_tenant_header_ignored() -> None:
    """T-SEC-0005: a forged tenant in a header is ignored.

    id: T-SEC-0005
    title: Forged tenant in header ignored
    purpose: Verify the tenant is never taken from a header.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: principal with tenant-a, header claims tenant-b
    expected: derived tenant is tenant-a
    risk: tenant forgery via header
    owning capability: security
    """
    principal = Principal(principal_id="user-1", role=ROLE_VIEWER, tenant_id="tenant-a")
    result = derive_tenant_from_credential(principal, header_tenant="tenant-b")
    assert result == "tenant-a"


# ---------------------------------------------------------------------------
# T-SEC-0006: forged tenant in path is ignored
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0006_forged_tenant_path_ignored() -> None:
    """T-SEC-0006: a forged tenant in a path parameter is ignored.

    id: T-SEC-0006
    title: Forged tenant in path ignored
    purpose: Verify the tenant is never taken from a path parameter.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: principal with tenant-a, path claims tenant-b
    expected: derived tenant is tenant-a
    risk: tenant forgery via path
    owning capability: security
    """
    principal = Principal(principal_id="user-1", role=ROLE_VIEWER, tenant_id="tenant-a")
    result = derive_tenant_from_credential(principal, path_tenant="tenant-b")
    assert result == "tenant-a"


# ---------------------------------------------------------------------------
# T-SEC-0007: forged tenant in claims is ignored
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0007_forged_tenant_claims_ignored() -> None:
    """T-SEC-0007: a forged tenant in token claims is ignored.

    id: T-SEC-0007
    title: Forged tenant in claims ignored
    purpose: Verify the tenant is never taken from token claims.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: principal with tenant-a, claim says tenant-b
    expected: derived tenant is tenant-a
    risk: tenant forgery via claims
    owning capability: security
    """
    principal = Principal(principal_id="user-1", role=ROLE_VIEWER, tenant_id="tenant-a")
    result = derive_tenant_from_credential(principal, claim_tenant="tenant-b")
    assert result == "tenant-a"


# ---------------------------------------------------------------------------
# T-SEC-0008: platform role has no tenant
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0008_platform_role_no_tenant() -> None:
    """T-SEC-0008: the platform role carries no tenant.

    id: T-SEC-0008
    title: Platform role has no tenant
    purpose: Verify platform credential has no tenant_id.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: Principal with platform role
    expected: tenant_id is None
    risk: platform credential accesses tenant data
    owning capability: security
    """
    principal = Principal(principal_id="platform-1", role=ROLE_PLATFORM)
    assert principal.tenant_id is None
    assert principal.is_platform


# ---------------------------------------------------------------------------
# T-SEC-0009: platform role denied tenant-scoped routes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0009_platform_denied_tenant_routes() -> None:
    """T-SEC-0009: platform credential denied tenant-scoped routes.

    id: T-SEC-0009
    title: Platform denied tenant-scoped routes
    purpose: Verify platform credential cannot reach tenant routes.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: platform principal, tenant-scoped route
    expected: RoleError on enforce_role_boundary
    risk: platform credential accesses tenant data
    owning capability: security
    """
    principal = Principal(principal_id="platform-1", role=ROLE_PLATFORM)
    with pytest.raises(RoleError):
        enforce_role_boundary(principal, "/api/v1/cases/123", is_tenant_scoped=True)


# ---------------------------------------------------------------------------
# T-SEC-0010: platform role reaches deployment routes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0010_platform_reaches_deployment_routes() -> None:
    """T-SEC-0010: platform credential reaches deployment routes.

    id: T-SEC-0010
    title: Platform reaches deployment routes
    purpose: Verify platform credential can reach deployment routes.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: platform principal, deployment route
    expected: no error
    risk: platform locked out of health checks
    owning capability: security
    """
    principal = Principal(principal_id="platform-1", role=ROLE_PLATFORM)
    route = next(iter(DEPLOYMENT_ROUTES))
    enforce_role_boundary(principal, route, is_tenant_scoped=False)


# ---------------------------------------------------------------------------
# T-SEC-0011: viewer role can access routes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0011_viewer_can_access() -> None:
    """T-SEC-0011: viewer role can access tenant-scoped routes.

    id: T-SEC-0011
    title: Viewer accesses tenant routes
    purpose: Verify viewer role boundary allows tenant routes.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: viewer principal, tenant route
    expected: no error
    risk: viewer locked out
    owning capability: security
    """
    principal = Principal(principal_id="user-1", role=ROLE_VIEWER, tenant_id="tenant-a")
    enforce_role_boundary(principal, "/api/v1/cases", is_tenant_scoped=True)


# ---------------------------------------------------------------------------
# T-SEC-0012: operator role can access routes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0012_operator_can_access() -> None:
    """T-SEC-0012: operator role can access tenant-scoped routes.

    id: T-SEC-0012
    title: Operator accesses tenant routes
    purpose: Verify operator role boundary allows tenant routes.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: operator principal, tenant route
    expected: no error
    risk: operator locked out
    owning capability: security
    """
    principal = Principal(principal_id="user-2", role=ROLE_OPERATOR, tenant_id="tenant-a")
    enforce_role_boundary(principal, "/api/v1/cases", is_tenant_scoped=True)


# ---------------------------------------------------------------------------
# T-SEC-0013: reviewer role can access and approve
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0013_reviewer_can_approve() -> None:
    """T-SEC-0013: reviewer role can approve proposals.

    id: T-SEC-0013
    title: Reviewer can approve
    purpose: Verify reviewer role can approve, separate from operator.
    level: fast
    requirement: PR-06; Part 3 §3.9; P11-T01
    input: reviewer principal
    expected: can_approve True, can_operate False
    risk: reviewer/operator role confusion
    owning capability: security
    """
    principal = Principal(principal_id="user-3", role=ROLE_REVIEWER, tenant_id="tenant-a")
    assert principal.can_approve() is True
    assert principal.can_operate() is False


# ---------------------------------------------------------------------------
# T-SEC-0014: administrator role can operate
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0014_administrator_can_operate() -> None:
    """T-SEC-0014: administrator role can operate.

    id: T-SEC-0014
    title: Administrator can operate
    purpose: Verify administrator role can operate and access.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T01
    input: administrator principal
    expected: can_operate True
    risk: administrator locked out
    owning capability: security
    """
    principal = Principal(principal_id="user-4", role=ROLE_ADMINISTRATOR, tenant_id="tenant-a")
    assert principal.can_operate() is True
    assert principal.can_access_route("/api/v1/cases") is True


# ---------------------------------------------------------------------------
# T-SEC-0015: session cookie is signed and verifiable
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0015_session_cookie_signed() -> None:
    """T-SEC-0015: session cookie is signed and verifiable.

    id: T-SEC-0015
    title: Session cookie signed
    purpose: Verify a session cookie is signed and round-trips.
    level: fast
    requirement: PR-06; Part 3 §3.15; P11-T01
    input: principal, create then verify cookie
    expected: verify returns same principal
    risk: unsigned session cookie
    owning capability: security
    """
    signer = DevSessionSigner()
    principal = Principal(principal_id="user-1", role=ROLE_VIEWER, tenant_id="tenant-a")
    cookie = create_session_cookie(
        principal=principal,
        signer=signer,
    )
    result = verify_session_cookie(cookie, signer=signer)
    assert result.principal_id == "user-1"
    assert result.tenant_id == "tenant-a"


# ---------------------------------------------------------------------------
# T-SEC-0016: tampered session cookie fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0016_tampered_cookie_fails() -> None:
    """T-SEC-0016: a tampered session cookie fails verification.

    id: T-SEC-0016
    title: Tampered cookie fails
    purpose: Verify a tampered cookie raises SessionError.
    level: fast
    requirement: PR-06; Part 3 §3.15; P11-T01
    input: valid cookie with modified payload
    expected: SessionError raised
    risk: session forgery
    owning capability: security
    """
    signer = DevSessionSigner()
    principal = Principal(principal_id="user-1", role=ROLE_VIEWER, tenant_id="tenant-a")
    cookie = create_session_cookie(principal=principal, signer=signer)
    parts = cookie.rsplit(".", 1)
    tampered = parts[0] + "x." + parts[1]
    with pytest.raises(SessionError, match="invalid signature"):
        verify_session_cookie(tampered, signer=signer)
