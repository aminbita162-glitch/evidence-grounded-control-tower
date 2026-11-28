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
