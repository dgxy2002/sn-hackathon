import asyncio
import os
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import cast

import pymupdf
import pytest
from fastapi import FastAPI, UploadFile
from httpx import ASGITransport, AsyncClient, Response

from app.analysis_service import AnalysisSessionService
from app.api_v2 import create_v2_router
from app.document_service import DocumentService




class CancelledUpload:
    content_type = "application/pdf"

    def __init__(self) -> None:
        self._read_count = 0

    async def read(self, _: int) -> bytes:
        self._read_count += 1
        if self._read_count == 1:
            return b"%PDF-1.7\n"
        raise asyncio.CancelledError

    async def close(self) -> None:
        return None

def pdf_bytes(text: str = "Policy summary") -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def encrypted_pdf_bytes() -> bytes:
    document = pymupdf.open()
    document.new_page().insert_text((72, 72), "Private policy")
    content = document.tobytes(
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="owner-password",
        user_pw="user-password",
    )
    document.close()
    return content


def scanned_pdf_bytes(text: str = "Scanned policy summary") -> bytes:
    source = pymupdf.open()
    source_page = source.new_page()
    source_page.insert_text((72, 100), text, fontsize=24)
    image = source_page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)

    scanned = pymupdf.open()
    scanned_page = scanned.new_page()
    scanned_page.insert_image(scanned_page.rect, stream=image.tobytes("png"))
    content = scanned.tobytes()
    scanned.close()
    source.close()
    return content


def create_test_app(
    workspace_root: Path,
    *,
    max_size_bytes: int = 20 * 1024 * 1024,
    max_page_count: int = 100,
) -> tuple[FastAPI, DocumentService]:
    analyses = AnalysisSessionService()
    documents = DocumentService(
        workspace_root=workspace_root,
        max_size_bytes=max_size_bytes,
        max_page_count=max_page_count,
    )
    app = FastAPI()
    app.include_router(create_v2_router(analyses, documents))
    return app, documents


def request(
    app: FastAPI,
    method: str,
    path: str,
    *,
    files: dict[str, tuple[str, bytes, str]] | None = None,
    headers: dict[str, str] | None = None,
    json: dict[str, str] | None = None,
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


def upload(
    app: FastAPI,
    analysis_id: str,
    content: bytes,
    *,
    filename: str = "policy.pdf",
    media_type: str = "application/pdf",
    idempotency_key: str = "upload-1",
) -> Response:
    return request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/documents",
        files={"document": (filename, content, media_type)},
        headers={"Idempotency-Key": idempotency_key},
    )


def test_pdf_upload_lists_metadata_and_deletes_opaque_artifacts(tmp_path: Path) -> None:
    app, _ = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    content = pdf_bytes()

    response = upload(
        app,
        analysis_id,
        content,
        filename="../../customer-name-policy.pdf",
    )

    assert response.status_code == 201
    uploaded = response.json()["document"]
    assert uploaded["analysis_id"] == analysis_id
    assert uploaded["content_sha256"] == sha256(content).hexdigest()
    assert uploaded["media_type"] == "application/pdf"
    assert uploaded["page_count"] == 1
    assert uploaded["size_bytes"] == len(content)
    assert uploaded["state"] == "ready"
    assert "filename" not in uploaded
    assert "text" not in uploaded

    listed = request(app, "GET", f"/api/v2/analyses/{analysis_id}/documents")
    assert listed.status_code == 200
    assert listed.json() == {"documents": [uploaded]}

    artifacts = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert len(artifacts) == 1
    assert artifacts[0].name == f"{uploaded['document_id']}.pdf"
    assert "customer-name" not in str(artifacts[0])

    deleted = request(app, "DELETE", f"/api/v2/analyses/{analysis_id}")
    assert deleted.status_code == 204
    assert not list(tmp_path.rglob("*"))


def test_duplicate_content_is_idempotent_and_key_is_payload_bound(tmp_path: Path) -> None:
    app, _ = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    content = pdf_bytes()

    first = upload(app, analysis_id, content, idempotency_key="first-key")
    duplicate = upload(app, analysis_id, content, idempotency_key="second-key")
    conflict = upload(
        app,
        analysis_id,
        pdf_bytes("Different policy"),
        idempotency_key="first-key",
    )

    assert first.status_code == 201
    assert duplicate.status_code == 201
    assert duplicate.json() == first.json()
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert len([path for path in tmp_path.rglob("*.pdf")]) == 1


def test_upload_rejects_mime_spoofing_malformed_and_oversized_files(
    tmp_path: Path,
) -> None:
    app, _ = create_test_app(tmp_path, max_size_bytes=256)
    analysis_id = create_analysis(app)

    wrong_mime = upload(
        app,
        analysis_id,
        b"%PDF-1.7\n",
        media_type="text/plain",
        idempotency_key="mime",
    )
    malformed = upload(
        app,
        analysis_id,
        b"%PDF-1.7\nnot a valid document",
        idempotency_key="malformed",
    )
    oversized = upload(
        app,
        analysis_id,
        pdf_bytes(),
        idempotency_key="oversized",
    )

    assert wrong_mime.status_code == 415
    assert wrong_mime.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "INVALID_PDF"
    assert oversized.status_code == 413
    assert oversized.json()["error"]["code"] == "DOCUMENT_TOO_LARGE"
    assert not list(tmp_path.rglob("*"))


def test_upload_rejects_encrypted_pdf_and_requires_idempotency_key(
    tmp_path: Path,
) -> None:
    app, _ = create_test_app(tmp_path)
    analysis_id = create_analysis(app)

    encrypted = upload(
        app,
        analysis_id,
        encrypted_pdf_bytes(),
        idempotency_key="encrypted",
    )
    missing_key = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/documents",
        files={"document": ("policy.pdf", pdf_bytes(), "application/pdf")},
    )

    assert encrypted.status_code == 422
    assert encrypted.json()["error"]["code"] == "ENCRYPTED_PDF"
    assert missing_key.status_code == 400
    assert missing_key.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"
    assert not list(tmp_path.rglob("*"))


def test_expired_analysis_deletes_document_workspace(tmp_path: Path) -> None:
    current_time = [datetime(2026, 9, 3, tzinfo=UTC)]
    analyses = AnalysisSessionService(
        ttl=timedelta(minutes=5),
        clock=lambda: current_time[0],
    )
    documents = DocumentService(workspace_root=tmp_path, clock=lambda: current_time[0])
    app = FastAPI()
    app.include_router(create_v2_router(analyses, documents))
    analysis_id = create_analysis(app)
    assert upload(app, analysis_id, pdf_bytes()).status_code == 201
    assert list(tmp_path.rglob("*.pdf"))

    current_time[0] += timedelta(minutes=6)
    expired = request(app, "GET", f"/api/v2/analyses/{analysis_id}")

    assert expired.status_code == 404
    assert not list(tmp_path.rglob("*"))


def test_cancelled_upload_removes_partial_artifacts(tmp_path: Path) -> None:
    documents = DocumentService(workspace_root=tmp_path)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            documents.upload(
                "analysis-id",
                cast(UploadFile, CancelledUpload()),
                "cancelled-upload",
            )
        )

    assert not list(tmp_path.rglob("*"))


def test_restart_sweeps_abandoned_workspace(tmp_path: Path) -> None:
    abandoned = tmp_path / "opaque-workspace"
    abandoned.mkdir()
    (abandoned / "partial.upload").write_bytes(b"private bytes")
    old_timestamp = datetime(2026, 9, 3, tzinfo=UTC).timestamp()
    os.utime(abandoned, (old_timestamp, old_timestamp))

    DocumentService(
        workspace_root=tmp_path,
        orphan_ttl=timedelta(minutes=30),
        clock=lambda: datetime(2026, 9, 3, 0, 31, tzinfo=UTC),
    )

    assert not abandoned.exists()


def test_privacy_scan_detects_seeded_categories_without_value_leakage(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app, _ = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    sensitive_values = (
        "Alice Tan",
        "S1234567D",
        "alice.tan@example.com",
        "+65 9123 4567",
        "10 Anson Road #10-01 Singapore 079903",
        "POL-12345678",
        "123-456-789",
        "diabetes",
    )
    content = pdf_bytes(
        "Name: Alice Tan\n"
        "NRIC: S1234567D\n"
        "Email: alice.tan@example.com\n"
        "Mobile: +65 9123 4567\n"
        "Address: 10 Anson Road #10-01 Singapore 079903\n"
        "Policy Number: POL-12345678\n"
        "Account Number: 123-456-789\n"
        "Medical history: diabetes\n"
        "Signature: signed"
    )
    assert upload(app, analysis_id, content).status_code == 201

    response = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/privacy-scan",
        headers={"Idempotency-Key": "privacy-scan-1"},
    )

    assert response.status_code == 200
    findings = response.json()["findings"]
    assert {finding["category"] for finding in findings} == {
        "name",
        "national_id",
        "contact",
        "address",
        "policy_number",
        "account_detail",
        "signature",
        "health_information",
    }
    assert all(finding["action"] in {"redact", "review"} for finding in findings)
    exposed = response.text + caplog.text
    assert all(value not in exposed for value in sensitive_values)

    session = request(app, "GET", f"/api/v2/analyses/{analysis_id}")
    assert session.json()["analysis"]["stage"] == "privacy_review"


def test_scanned_pdf_uses_local_ocr_and_page_limits_are_enforced(
    tmp_path: Path,
) -> None:
    app, _ = create_test_app(tmp_path / "ocr")
    analysis_id = create_analysis(app)

    scanned = upload(app, analysis_id, scanned_pdf_bytes(), idempotency_key="scan")

    assert scanned.status_code == 201
    assert scanned.json()["document"]["parser_path"] == "ocr"

    limited_app, _ = create_test_app(tmp_path / "limited", max_page_count=1)
    limited_analysis_id = create_analysis(limited_app)
    two_pages = pymupdf.open()
    for page_number in range(2):
        two_pages.new_page().insert_text((72, 72), f"Page {page_number + 1}")
    two_page_content = two_pages.tobytes()
    two_pages.close()

    limited = upload(
        limited_app,
        limited_analysis_id,
        two_page_content,
        idempotency_key="page-limit",
    )

    assert limited.status_code == 422
    assert limited.json()["error"]["code"] == "PAGE_LIMIT_EXCEEDED"
    assert not list((tmp_path / "limited").rglob("*"))


def test_generic_health_brochure_language_is_not_private_health_information(
    tmp_path: Path,
) -> None:
    app, _ = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    content = pdf_bytes(
        "AIA Hospital Income\n"
        "Buying health insurance products that are not suitable for you may "
        "impact your ability to finance future healthcare needs.\n"
        "Use the daily cash allowance for alternative therapies, medication, "
        "or to replace income while you recover from treatment.\n"
        "Benefits may apply following a cancer, stroke, or heart disease event."
    )
    assert upload(app, analysis_id, content).status_code == 201

    response = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/privacy-scan",
        headers={"Idempotency-Key": "brochure-privacy-scan"},
    )

    assert response.status_code == 200
    assert response.json()["findings"] == []


def test_privacy_findings_require_confirmed_payload_bound_review(
    tmp_path: Path,
) -> None:
    app, _ = create_test_app(tmp_path)
    analysis_id = create_analysis(app)
    content = pdf_bytes(
        "Name: Alice Tan\n"
        "NRIC: S1234567D\n"
        "Medical history: diabetes"
    )
    assert upload(app, analysis_id, content).status_code == 201
    scanned = request(
        app,
        "POST",
        f"/api/v2/analyses/{analysis_id}/privacy-scan",
        headers={"Idempotency-Key": "privacy-scan"},
    )
    findings = scanned.json()["findings"]
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
    replayed = request(
        app,
        "PATCH",
        f"/api/v2/analyses/{analysis_id}/privacy-findings",
        headers={"Idempotency-Key": "privacy-review"},
        json={"decisions": decisions},
    )
    changed_decisions = [dict(decision) for decision in decisions]
    changed_decisions[0]["action"] = "keep"
    conflict = request(
        app,
        "PATCH",
        f"/api/v2/analyses/{analysis_id}/privacy-findings",
        headers={"Idempotency-Key": "privacy-review"},
        json={"decisions": changed_decisions},
    )

    assert reviewed.status_code == 200
    assert all(finding["confirmed"] for finding in reviewed.json()["findings"])
    assert replayed.json() == reviewed.json()
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    session = request(app, "GET", f"/api/v2/analyses/{analysis_id}")
    assert session.json()["analysis"]["stage"] == "extracting"
