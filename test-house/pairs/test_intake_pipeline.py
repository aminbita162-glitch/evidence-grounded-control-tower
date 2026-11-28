"""Phase 14 transfers through the library, command line and API."""

from __future__ import annotations

import asyncio
import base64
import json
import sys

import pytest
from fastapi.testclient import TestClient

from api.app import AppPorts, create_app
from api.authentication import operator_principal, tenant_principal
from capabilities.k14.demo import DOCUMENTS, create_demo
from cli.main import main
from kernel.auth.roles import Principal
from kernel.intake import ReadResult, TextSegment
from kernel.skeleton import WalkingSkeleton
from kernel.skeleton.intake import SourceDocument

pytestmark = pytest.mark.fast
_OWNER = Principal(principal_id="SYN-OPERATOR", role="operator", tenant_id="SYN-TEN-0001")


class FixtureReader:
    async def read(self, payload: bytes, media_type: str) -> ReadResult:
        return ReadResult(media_type, (TextSegment(0, payload.decode()),))


# id: T-INT-0041
# title: Parallel extraction feeds consistency
# purpose: Verify parallel extraction feeds consistency.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0041_parallel_extraction_feeds_consistency() -> None:
    workflow = create_demo(FixtureReader())
    asyncio.run(workflow.ingest(_OWNER, "case", DOCUMENTS, "2026-11"))
    result = workflow.result(_OWNER, "case")
    assert result is not None
    assert result.consistency.outcome == "ALLOW"
    assert result.consistency.canonical[0].key == "shipment.gross_weight"
    assert result.shield.outcome == "ALLOW"
    assert all(report.calls for report in result.extraction)


# id: T-INT-0042
# title: Flagged value is not canonical
# purpose: Verify flagged value is not canonical.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0042_flagged_value_is_not_canonical() -> None:
    workflow = create_demo(FixtureReader())
    first, second = DOCUMENTS
    different = SourceDocument(
        second.filename,
        second.document_type,
        second.payload.replace("١٢٥٠".encode(), "١٢٥١".encode()),
        second.parallel_group,
    )
    asyncio.run(workflow.ingest(_OWNER, "case", (first, different), "2026-11"))
    result = workflow.result(_OWNER, "case")
    assert result is not None
    assert result.consistency.outcome == "ABSTAIN"
    assert result.consistency.canonical == ()
    assert all(
        "K14.NEEDS_REVIEW.PARALLEL_DIFFERENCE" in report.reason_codes
        for report in result.extraction
    )


# id: T-INT-0043
# title: Skeleton reaches replayed passport
# purpose: Verify skeleton reaches replayed passport.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0043_skeleton_reaches_replayed_passport() -> None:
    result = asyncio.run(
        WalkingSkeleton().run(intake=create_demo(FixtureReader()), uploads=DOCUMENTS)
    )
    assert any(r.record_type == "document_shield" for r in result.records)
    assert result.structural_ok and result.bundle_ok and result.replay_ok


# id: T-INT-0044
# title: Api uniform capability path
# purpose: Verify api uniform capability path.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0044_api_uniform_capability_path() -> None:
    app = create_app(AppPorts(intake=create_demo(FixtureReader())))
    app.dependency_overrides[tenant_principal] = lambda: _OWNER
    app.dependency_overrides[operator_principal] = lambda: _OWNER
    intake = "/api/v1/capabilities/K14"
    facts = {
        "case_id": "case",
        "documents": [
            {
                "filename": doc.filename,
                "document_type": doc.document_type,
                "content_base64": base64.b64encode(doc.payload).decode(),
                "parallel_group": doc.parallel_group,
            }
            for doc in DOCUMENTS
        ],
    }
    with TestClient(app) as client:
        response = client.post(f"{intake}/invoke", json={"facts": facts})
        assert response.status_code == 200
        result = client.get("/api/v1/capabilities/F01/result", params={"case_id": "case"})
        assert result.status_code == 200
        assert result.json()["decision"] == "ALLOW"
        evidence = client.get(f"{intake}/evidence", params={"case_id": "case"})
        assert len(evidence.json()["records"]) == 2
        stranger = Principal(principal_id="SYN-STRANGER", role="viewer", tenant_id="SYN-OTHER")
        app.dependency_overrides[tenant_principal] = lambda: stranger
        foreign = client.get(f"{intake}/result", params={"case_id": "case"})
        unknown = client.get(f"{intake}/result", params={"case_id": "unknown"})
        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json() == unknown.json()


# id: T-INT-0045
# title: Cli document workflow
# purpose: Verify cli document workflow.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-09
# capability: kernel
@pytest.mark.fast
def test_T_INT_0045_cli_document_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["capability", "F01"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["label"] == "SYNTHETIC"
    if sys.platform == "linux":
        assert report["status"] == "ALLOW"


# id: T-INT-0046
# title: Reviewer relation and erasure refresh related case evidence
# purpose: Verify the lifecycle of cross-case duplicate findings.
# level: fast
# requirement: PR-02 PR-16
# input: Two uploads of a synthetic invoice and tenant-scoped reviewer access.
# expected: Reuse holds both cases until reviewer approval and erasure removes the stored match.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
def test_T_INT_0046_relation_and_erasure() -> None:
    from kernel.humangate import HumanGateError

    reviewer = Principal(principal_id="SYN-REVIEW", role="reviewer", tenant_id=_OWNER.tenant_id)
    admin = Principal(principal_id="SYN-ADMIN", role="administrator", tenant_id=_OWNER.tenant_id)
    foreign = Principal(principal_id="SYN-REVIEW", role="reviewer", tenant_id="SYN-DIFFERENT")
    workflow = create_demo(
        FixtureReader(),
        case_access=lambda principal, case: (
            principal.tenant_id == _OWNER.tenant_id and case in {"first", "second"}
        ),
    )

    async def run() -> None:
        await workflow.ingest(_OWNER, "first", DOCUMENTS[:1], "2026-11")
        await workflow.ingest(_OWNER, "second", DOCUMENTS[:1], "2026-11")
        prior, newest = workflow.result(_OWNER, "first"), workflow.result(_OWNER, "second")
        assert prior is not None and newest is not None
        assert prior.shield.outcome == newest.shield.outcome == "HOLD"
        assert prior.evidence["K09"][-1]["supersedes"] == prior.evidence["K09"][0]["output_hash"]
        doc = prior.documents[0].record.document_id
        other = newest.documents[0].record.document_id
        for denied in (_OWNER, foreign):
            with pytest.raises(PermissionError, match="CASE_NOT_FOUND"):
                await workflow.declare_relation(denied, "first", "second", doc, other, "SPLIT_OF")
        with pytest.raises(PermissionError, match="CASE_NOT_FOUND"):
            await workflow.declare_relation(reviewer, "first", "second", doc, "missing", "SPLIT_OF")
        await workflow.declare_relation(reviewer, "first", "second", doc, other, "SPLIT_OF")
        with pytest.raises(HumanGateError):
            await workflow.declare_relation(reviewer, "first", "second", doc, other, "SPLIT_OF")
        current = workflow.result(reviewer, "first")
        assert current is not None and current.shield.outcome == "ALLOW"
        assert "K09.OBS.RELATION_APPLIED" in current.shield.reason_codes
        with pytest.raises(PermissionError, match="CASE_NOT_FOUND"):
            await workflow.erase_document(reviewer, "first", doc)
        assert not await workflow.erase_document(admin, "first", "missing")
        assert await workflow.erase_document(admin, "first", doc)
        result = workflow.result(admin, "first")
        assert result is not None and not result.documents
        retained = workflow.result(admin, "second")
        assert retained is not None and retained.shield.outcome == "ALLOW"

    asyncio.run(run())


# id: T-INT-0047
# title: Access, write-path and name-link boundaries survive repeat ingestion
# purpose: Verify same-tenant ownership checks and canonical writes on upgraded inputs.
# level: fast
# requirement: PR-02 PR-11 PR-16
# input: Paired synthetic documents, an explicit name variant and a tenant-scoped writer.
# expected: Canonical writes contain only agreeing facts and proposed name links stay advisory.
# risk: THR-SEC-08
# capability: K14
@pytest.mark.fast
def test_T_INT_0047_case_ownership_and_repeat_intake() -> None:
    from capabilities.f01 import CanonicalFact
    from capabilities.k09 import FingerprintIndex
    from kernel.ledger.chain import InMemoryCaseChain

    class Writer:
        def __init__(self) -> None:
            self.keys: list[str] = []

        async def write(self, case_id: str, fact: CanonicalFact) -> None:
            assert case_id == "case"
            self.keys.append(fact.key)

    writer = Writer()
    index = FingerprintIndex()
    workflow = create_demo(
        FixtureReader(),
        name_variants={"مثال": ("example ltd",)},
        canonical_writer=writer,
        fingerprints=index,
    )
    same_scope = Principal(principal_id="SYN-STRANGER", role="operator", tenant_id=_OWNER.tenant_id)
    no_tenant = Principal(principal_id="SYN-PLATFORM", role="platform")
    wrong_tenant = Principal(principal_id="SYN-OTHER", role="operator", tenant_id="SYN-OTHER")
    first, second = DOCUMENTS
    alternate = SourceDocument(
        second.filename,
        second.document_type,
        second.payload + "\nseller_name: مثال".encode(),
        second.parallel_group,
    )
    unrelated = SourceDocument(
        "unrelated.txt", "DELIVERY_ORDER", b"Synthetic unrelated document", "different"
    )

    async def run() -> None:
        assert workflow.result(no_tenant, "case") is None
        with pytest.raises(PermissionError, match="CASE_NOT_FOUND"):
            await workflow.ingest(no_tenant, "case", (first,), "2026-11")
        with pytest.raises(PermissionError, match="CASE_NOT_FOUND"):
            await workflow.ingest(
                _OWNER, "other", (first,), "2026-11", chain=InMemoryCaseChain("SYN-OTHER", "other")
            )
        await workflow.ingest(_OWNER, "case", (first, alternate, unrelated), "2026-11")
        result = workflow.result(_OWNER, "case")
        assert result is not None
        assert "shipment.gross_weight" in writer.keys
        assert any(report.name_link_proposals for report in result.extraction)
        assert all(f.key != "shipment.seller_name" for f in result.consistency.canonical)
        assert result.outcome("K09")[0] == "ABSTAIN"
        with pytest.raises(PermissionError, match="CASE_NOT_FOUND"):
            await workflow.ingest(same_scope, "case", (first,), "2026-11")
        await workflow.ingest(_OWNER, "case", (first,), "2026-11")
        result = workflow.result(_OWNER, "case")
        assert result is not None and "K09.OBS.SAME_CASE_DUPLICATE" in result.shield.reason_codes
        await workflow.ingest(wrong_tenant, "case", (first,), "2026-11")
        assert result.documents[0].record.tenant_id == _OWNER.tenant_id
        index.upsert(
            next(
                fp
                for fp in index._documents[_OWNER.tenant_id or ""].values()
                if fp.case_id == "case"
            )
        )
        assert workflow.result(_OWNER, "case") is None

    asyncio.run(run())
