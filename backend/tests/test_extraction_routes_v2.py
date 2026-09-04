import asyncio
from pathlib import Path
from typing import Any

import pymupdf
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from app.analysis_service import AnalysisSessionService
from app.api_v2 import create_v2_router
from app.document_service import DocumentService


def pdf_bytes(text: str) -> bytes:
    document = pymupdf.open()
    document.new_page().insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def request(
    app: FastAPI,
    method: str,
    path: str,
    *,
    files: dict[str, tuple[str, bytes, str]] | None = None,
    headers: dict[str, str] | None = None,
    json: dict[str, Any] | None = None,
) -> Response:
    async def send() -> Response:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(
                method,
                path,
                files=files,
                headers=headers,
                json=json,
            )

    return asyncio.run(send())


def create_analysis(app: FastAPI) -> str:
    response = request(
        app,
        "POST",
        "/api/v2/analyses",
        json={"purpose": "considering_offer"},
    )
    assert response.status_code == 201
    return response.json()["analysis"]["analysis_id"]


def upload_and_scan(app: FastAPI, analysis_id: str, content: bytes) -> list[dict[str, Any]]:
    uploaded = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/documents",
        files={"document": ("private-name.pdf", content, "application/pdf")},
        headers={"Idempotency-Key": "upload"},
    )
    assert uploaded.status_code == 201
    scanned = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/privacy-scan",
        headers={"Idempotency-Key": "privacy-scan"},
    )
    assert scanned.status_code == 200
    return scanned.json()["findings"]


def create_test_app(tmp_path: Path) -> FastAPI:
    app = FastAPI()
    app.include_router(
        create_v2_router(
            AnalysisSessionService(),
            DocumentService(workspace_root=tmp_path),
        )
    )
    return app


def test_extracts_typed_premium_terms_from_redacted_source_spans(
    tmp_path: Path,
) -> None:
    app = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    findings = upload_and_scan(
        app,
        analysis_id,
        pdf_bytes(
            "Name: Alice Tan\n"
            "NRIC: S1234567D\n"
            "Premium Amount: S$123.45\n"
            "Premium Frequency: Monthly\n"
            "Premium Payment Period: 20 years"
        ),
    )
    decisions = [
        {
            "finding_id": finding["finding_id"],
            "action": "redact",
            "confirmed": True,
        }
        for finding in findings
    ]
    reviewed = request(
        app,
        "PATCH",
        f"/api/v2/analyses/{analysis_id}/privacy-findings",
        headers={"Idempotency-Key": "privacy-review"},
        json={"decisions": decisions},
    )
    assert reviewed.status_code == 200

    extracted = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/extract",
        headers={"Idempotency-Key": "extract"},
    )

    assert extracted.status_code == 200
    payload = extracted.json()
    serialized = extracted.text
    assert "Alice Tan" not in serialized
    assert "S1234567D" not in serialized
    assert any("[REDACTED]" in span["redacted_text"] for span in payload["spans"])
    span_ids = {span["span_id"] for span in payload["spans"]}
    terms = {term["taxonomy_key"]: term for term in payload["terms"]}
    assert terms["premium.amount"]["value"] == {
        "state": "present",
        "value": {"amount": "123.45", "currency": "SGD"},
    }
    assert terms["premium.frequency"]["value"] == {
        "state": "present",
        "value": "monthly",
    }
    assert terms["premium.payment_duration"]["value"] == {
        "state": "present",
        "value": {"duration": 20, "unit": "years"},
    }
    assert all(set(term["source_span_ids"]).issubset(span_ids) for term in terms.values())
    assert all(not term["confirmed"] for term in terms.values())
    session = request(app, "GET", f"/api/v2/analyses/{analysis_id}")
    assert session.json()["analysis"]["stage"] == "term_review"


def test_missing_premium_fields_remain_unknown(tmp_path: Path) -> None:
    app = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    findings = upload_and_scan(
        app,
        analysis_id,
        pdf_bytes("Premium Amount: SGD 90.00"),
    )
    assert findings == []

    extracted = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/extract",
        headers={"Idempotency-Key": "extract"},
    )

    assert extracted.status_code == 200
    terms = {term["taxonomy_key"]: term for term in extracted.json()["terms"]}
    assert terms["premium.amount"]["value"]["state"] == "present"
    assert terms["premium.frequency"]["value"] == {
        "state": "unknown",
        "value": None,
    }
    assert terms["premium.frequency"]["source_span_ids"] == []
    assert terms["premium.payment_duration"]["value"] == {
        "state": "unknown",
        "value": None,
    }
    assert terms["premium.payment_duration"]["source_span_ids"] == []


def test_material_terms_require_confirmed_payload_bound_review(
    tmp_path: Path,
) -> None:
    app = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    findings = upload_and_scan(
        app,
        analysis_id,
        pdf_bytes(
            "Premium Amount: S$123.45\n"
            "Premium Frequency: Monthly\n"
            "Premium Payment Period: 20 years"
        ),
    )
    assert findings == []
    extracted = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/extract",
        headers={"Idempotency-Key": "extract"},
    )
    terms = extracted.json()["terms"]
    decisions = [
        {
            "term_id": term["term_id"],
            "value": term["value"],
            "source_span_ids": term["source_span_ids"],
            "confirmed": True,
        }
        for term in terms
    ]

    reviewed = request(
        app,
        "PATCH",
        f"/api/v2/analyses/{analysis_id}/terms",
        headers={"Idempotency-Key": "term-review"},
        json={"decisions": decisions},
    )
    replayed = request(
        app,
        "PATCH",
        f"/api/v2/analyses/{analysis_id}/terms",
        headers={"Idempotency-Key": "term-review"},
        json={"decisions": decisions},
    )
    changed_decisions = [dict(decision) for decision in decisions]
    changed_decisions[0] = {
        **changed_decisions[0],
        "value": {
            "state": "present",
            "value": {"amount": "999.00", "currency": "SGD"},
        },
    }
    conflict = request(
        app,
        "PATCH",
        f"/api/v2/analyses/{analysis_id}/terms",
        headers={"Idempotency-Key": "term-review"},
        json={"decisions": changed_decisions},
    )

    assert reviewed.status_code == 200
    assert all(term["confirmed"] for term in reviewed.json()["terms"])
    assert replayed.json() == reviewed.json()
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    session = request(app, "GET", f"/api/v2/analyses/{analysis_id}")
    assert session.json()["analysis"]["stage"] == "ready"


def test_unresolved_privacy_blocks_extraction(tmp_path: Path) -> None:
    app = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    findings = upload_and_scan(
        app,
        analysis_id,
        pdf_bytes("Name: Alice Tan\nPremium Amount: S$100.00"),
    )
    assert findings

    extracted = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/extract",
        headers={"Idempotency-Key": "extract"},
    )

    assert extracted.status_code == 409
    assert extracted.json()["error"]["code"] == "PRIVACY_REVIEW_REQUIRED"


def test_conflicting_premium_values_remain_unknown(tmp_path: Path) -> None:
    app = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    findings = upload_and_scan(
        app,
        analysis_id,
        pdf_bytes(
            "Premium Amount: S$100.00\n"
            "Premium Amount: S$200.00"
        ),
    )
    assert findings == []

    extracted = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/extract",
        headers={"Idempotency-Key": "extract"},
    )

    assert extracted.status_code == 200
    terms = {term["taxonomy_key"]: term for term in extracted.json()["terms"]}
    assert terms["premium.amount"]["value"] == {
        "state": "unknown",
        "value": None,
    }
    assert terms["premium.amount"]["confidence"] == 0.5
    assert terms["premium.amount"]["source_span_ids"]


def test_extracts_identity_coverage_and_exit_terms_from_explicit_labels(
    tmp_path: Path,
) -> None:
    app = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    findings = upload_and_scan(
        app,
        analysis_id,
        pdf_bytes(
            "Benefit Illustration\n"
            "Insurer: Example Life Pte. Ltd.\n"
            "Product Name: Steady Future Plus\n"
            "Illustration Date: 4 September 2026\n"
            "Policy Status: Proposed\n"
            "Premium Escalation: 3% annually\n"
            "Coverage Commencement: 01/10/2026\n"
            "Maturity Date: 2046-10-01\n"
            "Free-look Period: 14 days"
        ),
    )
    assert findings == []

    extracted = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/extract",
        headers={"Idempotency-Key": "extract-taxonomy"},
    )

    assert extracted.status_code == 200
    terms = {term["taxonomy_key"]: term for term in extracted.json()["terms"]}
    assert terms["commitment.insurer"]["value"] == {
        "state": "present",
        "value": "Example Life Pte. Ltd",
    }
    assert terms["commitment.product_name"]["value"]["value"] == (
        "Steady Future Plus"
    )
    assert terms["commitment.document_type"]["value"]["value"] == (
        "benefit_illustration"
    )
    assert terms["commitment.issue_date"]["value"]["value"] == "2026-09-04"
    assert terms["commitment.policy_status"]["value"]["value"] == "proposed"
    assert terms["premium.escalation"]["value"]["value"] == {
        "percentage": "3",
        "frequency": "annual",
    }
    assert terms["coverage.commencement"]["value"]["value"] == "2026-10-01"
    assert terms["coverage.expiry_or_maturity"]["value"]["value"] == (
        "2046-10-01"
    )
    assert terms["exit.free_look_period"]["value"]["value"] == {
        "duration": 14,
        "unit": "days",
    }
    assert all(term["source_span_ids"] for term in terms.values() if term["value"]["state"] == "present")


def test_extracts_explicit_identity_and_date_from_brochure_wording(
    tmp_path: Path,
) -> None:
    app = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    findings = upload_and_scan(
        app,
        analysis_id,
        pdf_bytes(
            "AIA Hospital Income is an affordable plan designed to help.\n"
            "Annual Premium (S$, includes 9% GST)\n"
            "This insurance plan is underwritten by AIA Singapore Private "
            "Limited (Reg. No. 201106386R).\n"
            "This brochure is not a contract of insurance.\n"
            "The information is correct as at 1 January 2024."
        ),
    )
    assert findings == []

    extracted = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/extract",
        headers={"Idempotency-Key": "extract-brochure"},
    )

    assert extracted.status_code == 200
    terms = {term["taxonomy_key"]: term for term in extracted.json()["terms"]}
    assert terms["commitment.product_name"]["value"]["value"] == (
        "AIA Hospital Income"
    )
    assert terms["commitment.insurer"]["value"]["value"] == (
        "AIA Singapore Private Limited"
    )
    assert terms["commitment.document_type"]["value"]["value"] == "brochure"
    assert terms["commitment.issue_date"]["value"]["value"] == "2024-01-01"
    assert terms["premium.frequency"]["value"]["value"] == "annual"
    assert terms["premium.amount"]["value"]["state"] == "unknown"
