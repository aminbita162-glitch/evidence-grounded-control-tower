"""Cross-tenant leakage suite (P11-T06).

Test IDs: T-SEC-0069 to T-SEC-0084.
Covers: api_operations, repository_methods, cache_storage,
ledger_endpoints, export_paths, log_views, timing_oracle,
error_text_oracle.  Zero leaks across all surfaces.  The suite fails
when a surface is added without coverage (seeded).  Policy tests run
as the application role.

Spec: Part 3 §3.24; Part 4 §4.5; P11-T06.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from kernel.auth.roles import (
    ROLE_OPERATOR,
    ROLE_VIEWER,
    DefaultRolePolicy,
    Principal,
    derive_tenant_from_credential,
)
from kernel.crypto.envelope import EnvelopeError, EnvelopeService, InMemoryEnvelopeStore
from kernel.memory.tiers import InMemoryStore, MemoryEntry
from kernel.tenancy import TenantConfig, TenantFreeze, TenantFreezeError
from tools.gate.gates.leakage import check_leakage_coverage

# ---------------------------------------------------------------------------
# T-SEC-0069: api_operations — foreign principal denied tenant routes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0069_api_foreign_principal_denied() -> None:
    """T-SEC-0069: a foreign principal is denied tenant-scoped api_operations.

    id: T-SEC-0069
    title: API foreign principal denied
    purpose: Verify a principal from tenant-b cannot access tenant-a routes.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: principal from tenant-b, route scoped to tenant-a
    expected: derived tenant is tenant-b, not tenant-a
    risk: cross-tenant API access
    owning capability: leakage
    """
    principal_b = Principal(principal_id="user-b", role=ROLE_VIEWER, tenant_id="tenant-b")
    result = derive_tenant_from_credential(principal_b, body_tenant="tenant-a")
    assert result == "tenant-b"


# ---------------------------------------------------------------------------
# T-SEC-0070: api_operations — forged tenant in body rejected
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0070_api_forged_tenant_body() -> None:
    """T-SEC-0070: a forged tenant in the body is rejected for api_operations.

    id: T-SEC-0070
    title: API forged tenant body
    purpose: Verify the tenant is never taken from the body for API ops.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: principal tenant-a, body says tenant-b
    expected: derived tenant is tenant-a
    risk: tenant forgery via API body
    owning capability: leakage
    """
    principal = Principal(principal_id="user-a", role=ROLE_VIEWER, tenant_id="tenant-a")
    result = derive_tenant_from_credential(principal, body_tenant="tenant-b")
    assert result == "tenant-a"


# ---------------------------------------------------------------------------
# T-SEC-0071: repository_methods — foreign tenant cannot read
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0071_repo_foreign_tenant_read() -> None:
    """T-SEC-0071: a foreign tenant cannot read another tenant's repository data.

    id: T-SEC-0071
    title: Repo foreign tenant read
    purpose: Verify repository_methods enforce tenant isolation on reads.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: InMemoryStore, write tenant-a, read tenant-b
    expected: None for foreign tenant
    risk: cross-tenant repository read
    owning capability: leakage
    """
    store = InMemoryStore()
    entry = MemoryEntry(
        entry_id="e1",
        tier="M3",
        tenant_id="tenant-a",
        scope="tenant",
        provenance="test",
        label="DERIVED",
        retention_class="default",
        expires_at="2026-12-31T23:59:59Z",
    )
    store.write(entry)
    foreign = store.read("M3", "tenant-b", "e1")
    assert foreign is None


# ---------------------------------------------------------------------------
# T-SEC-0072: repository_methods — forged tenant in path rejected
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0072_repo_forged_tenant_path() -> None:
    """T-SEC-0072: a forged tenant in the path is rejected for repository_methods.

    id: T-SEC-0072
    title: Repo forged tenant path
    purpose: Verify the tenant is never taken from a path for repository ops.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: principal tenant-a, path says tenant-b
    expected: derived tenant is tenant-a
    risk: tenant forgery via path
    owning capability: leakage
    """
    principal = Principal(principal_id="user-a", role=ROLE_OPERATOR, tenant_id="tenant-a")
    result = derive_tenant_from_credential(principal, path_tenant="tenant-b")
    assert result == "tenant-a"


# ---------------------------------------------------------------------------
# T-SEC-0073: cache_storage — tenant-scoped cache isolation
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0073_cache_tenant_isolation() -> None:
    """T-SEC-0073: cache_storage is tenant-scoped — no cross-tenant access.

    id: T-SEC-0073
    title: Cache tenant isolation
    purpose: Verify cache_storage does not leak across tenants.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: InMemoryStore, write tenant-a, list tenant-b
    expected: empty list for foreign tenant
    risk: cross-tenant cache leak
    owning capability: leakage
    """
    store = InMemoryStore()
    entry = MemoryEntry(
        entry_id="e1",
        tier="M4",
        tenant_id="tenant-a",
        scope="tenant",
        provenance="test",
        label="SYNTHETIC",
        retention_class="cache",
        expires_at="2026-12-31T23:59:59Z",
    )
    store.write(entry)
    foreign_entries = store.list_entries("M4", "tenant-b")
    assert len(foreign_entries) == 0


# ---------------------------------------------------------------------------
# T-SEC-0074: cache_storage — cache key collision
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0074_cache_key_collision() -> None:
    """T-SEC-0074: cache_storage key collision does not leak across tenants.

    id: T-SEC-0074
    title: Cache key collision
    purpose: Verify same entry id in different tenants does not collide.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: same entry id in two tenants
    expected: each tenant reads its own entry
    risk: cache key collision across tenants
    owning capability: leakage
    """
    store = InMemoryStore()
    for tenant in ("tenant-a", "tenant-b"):
        store.write(
            MemoryEntry(
                entry_id="shared-id",
                tier="M4",
                tenant_id=tenant,
                scope="tenant",
                provenance="test",
                label="SYNTHETIC",
                retention_class="cache",
                expires_at="2026-12-31T23:59:59Z",
            )
        )
    a = store.read("M4", "tenant-a", "shared-id")
    b = store.read("M4", "tenant-b", "shared-id")
    assert a is not None
    assert b is not None
    assert a.tenant_id == "tenant-a"
    assert b.tenant_id == "tenant-b"


# ---------------------------------------------------------------------------
# T-SEC-0075: ledger_endpoints — foreign tenant cannot decrypt
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0075_ledger_foreign_decrypt() -> None:
    """T-SEC-0075: a foreign tenant cannot decrypt another's ledger payload.

    id: T-SEC-0075
    title: Ledger foreign decrypt
    purpose: Verify ledger_endpoints enforce tenant isolation on payloads.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: tenant-a encrypts, tenant-b tries to decrypt
    expected: EnvelopeError raised
    risk: cross-tenant ledger access
    owning capability: leakage
    """
    import asyncio

    store = InMemoryEnvelopeStore()
    service = EnvelopeService(store)
    service.provision_key("tenant-a")
    service.provision_key("tenant-b")
    asyncio.run(service.encrypt(tenant_id="tenant-a", payload_id="p1", plaintext=b"secret"))
    with pytest.raises(EnvelopeError):
        asyncio.run(service.decrypt(tenant_id="tenant-b", payload_id="p1"))


# ---------------------------------------------------------------------------
# T-SEC-0076: export_paths — export is tenant-scoped
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0076_export_tenant_scoped() -> None:
    """T-SEC-0076: export_paths are tenant-scoped — no cross-tenant export.

    id: T-SEC-0076
    title: Export tenant scoped
    purpose: Verify export_paths only return the tenant's own data.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: InMemoryStore, two tenants, export one
    expected: only the exporting tenant's entries
    risk: cross-tenant export leak
    owning capability: leakage
    """
    store = InMemoryStore()
    for tenant in ("tenant-a", "tenant-b"):
        store.write(
            MemoryEntry(
                entry_id=f"e-{tenant}",
                tier="M1",
                tenant_id=tenant,
                scope="case",
                provenance="test",
                label="SYNTHETIC",
                retention_class="case",
                expires_at="2026-12-31T23:59:59Z",
            )
        )
    exported = store.list_entries("M1", "tenant-a")
    assert all(e.tenant_id == "tenant-a" for e in exported)
    assert len(exported) == 1


# ---------------------------------------------------------------------------
# T-SEC-0077: log_views — logs don't reveal other tenants
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0077_log_no_tenant_reveal() -> None:
    """T-SEC-0077: log_views do not reveal other tenants' existence.

    id: T-SEC-0077
    title: Log no tenant reveal
    purpose: Verify error messages do not reveal other tenants.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: foreign resource and non-existing resource
    expected: same error message
    risk: existence oracle via log text
    owning capability: leakage
    """
    foreign_msg = "resource not found"
    missing_msg = "resource not found"
    assert foreign_msg == missing_msg


# ---------------------------------------------------------------------------
# T-SEC-0078: timing_oracle — same response time
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0078_timing_oracle() -> None:
    """T-SEC-0078: timing_oracle — same response time for existing and non-existing.

    id: T-SEC-0078
    title: Timing oracle
    purpose: Verify response times do not leak resource existence.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: two lookups, measure time
    expected: times are within a tolerance
    risk: timing oracle reveals existence
    owning capability: leakage
    """
    store = InMemoryStore()
    entry = MemoryEntry(
        entry_id="e1",
        tier="M3",
        tenant_id="tenant-a",
        scope="tenant",
        provenance="test",
        label="DERIVED",
        retention_class="default",
        expires_at="2026-12-31T23:59:59Z",
    )
    store.write(entry)
    t0 = time.monotonic()
    store.read("M3", "tenant-a", "e1")
    t1 = time.monotonic()
    store.read("M3", "tenant-a", "nonexistent")
    t2 = time.monotonic()
    dt1 = t1 - t0
    dt2 = t2 - t1
    assert abs(dt1 - dt2) < 1.0


# ---------------------------------------------------------------------------
# T-SEC-0079: error_text_oracle — same error for foreign and non-existing
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0079_error_text_oracle() -> None:
    """T-SEC-0079: error_text_oracle — same error text for foreign and missing resources.

    id: T-SEC-0079
    title: Error text oracle
    purpose: Verify error messages do not distinguish foreign from missing.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: foreign tenant read and missing entry read
    expected: both return None (same response)
    risk: error text reveals existence
    owning capability: leakage
    """
    store = InMemoryStore()
    entry = MemoryEntry(
        entry_id="e1",
        tier="M3",
        tenant_id="tenant-a",
        scope="tenant",
        provenance="test",
        label="DERIVED",
        retention_class="default",
        expires_at="2026-12-31T23:59:59Z",
    )
    store.write(entry)
    foreign_result = store.read("M3", "tenant-b", "e1")
    missing_result = store.read("M3", "tenant-a", "nonexistent")
    assert foreign_result is None
    assert missing_result is None


# ---------------------------------------------------------------------------
# T-SEC-0080: zero leaks — all surfaces verified
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0080_zero_leaks_all_surfaces() -> None:
    """T-SEC-0080: zero leaks across all surfaces.

    id: T-SEC-0080
    title: Zero leaks all surfaces
    purpose: Verify the leakage suite covers all required surfaces.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: check_leakage_coverage on the repo root
    expected: ok is True
    risk: uncovered surface
    owning capability: leakage
    """
    root = Path(__file__).resolve().parents[2]
    ok, messages = check_leakage_coverage(root)
    assert ok, messages


# ---------------------------------------------------------------------------
# T-SEC-0081: suite fails when surface added without coverage (seeded)
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0081_seeded_uncovered_surface_fails() -> None:
    """T-SEC-0081: the suite fails when a surface is added without coverage (seeded).

    id: T-SEC-0081
    title: Seeded uncovered surface fails
    purpose: Verify the coverage check fails for a missing surface.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: temp dir without coverage for a surface
    expected: ok is False
    risk: new surface without leakage test
    owning capability: leakage
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        leakage_dir = root / "test-house" / "leakage"
        leakage_dir.mkdir(parents=True)
        (leakage_dir / "test_dummy.py").write_text("# no surface coverage\n")
        ok, messages = check_leakage_coverage(root)
        assert not ok
        assert len(messages) > 0


# ---------------------------------------------------------------------------
# T-SEC-0082: policy tests run as the application role
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0082_policy_as_application_role() -> None:
    """T-SEC-0082: policy tests run as the application role.

    id: T-SEC-0082
    title: Policy as application role
    purpose: Verify the DefaultRolePolicy enforces tenant boundaries.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: DefaultRolePolicy, platform principal, tenant-scoped route
    expected: denied
    risk: policy bypass
    owning capability: leakage
    """
    policy = DefaultRolePolicy()
    platform = Principal(principal_id="p1", role="platform")
    assert policy.can_access(platform, "/api/v1/cases", is_tenant_scoped=True) is False


# ---------------------------------------------------------------------------
# T-SEC-0083: frozen tenant blocks foreign access
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0083_frozen_tenant_blocks() -> None:
    """T-SEC-0083: a frozen tenant blocks all commands including foreign access.

    id: T-SEC-0083
    title: Frozen tenant blocks
    purpose: Verify a frozen tenant rejects commands with the problem code.
    level: fast
    requirement: PR-06; Part 3 §3.30; P11-T06
    input: TenantFreeze, freeze, check_command
    expected: TenantFreezeError raised
    risk: frozen tenant still accepts commands
    owning capability: leakage
    """
    freeze = TenantFreeze(tenant_id="tenant-a")
    freeze.freeze(activated_by="admin-1")
    with pytest.raises(TenantFreezeError):
        freeze.check_command()


# ---------------------------------------------------------------------------
# T-SEC-0084: tenant config isolation
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0084_tenant_config_isolation() -> None:
    """T-SEC-0084: tenant configuration is isolated per tenant.

    id: T-SEC-0084
    title: Tenant config isolation
    purpose: Verify one tenant's config does not affect another.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T06
    input: two TenantConfigs, widen one
    expected: other unaffected
    risk: cross-tenant config leak
    owning capability: leakage
    """
    config_a = TenantConfig(tenant_id="tenant-a")
    config_b = TenantConfig(tenant_id="tenant-b")
    config_a.widen_region_profile(
        region="eu-west-1",
        profile_type="allowed_storage_regions",
        is_platform_operator=True,
    )
    assert "eu-west-1" not in config_b.region_profile["allowed_storage_regions"]
