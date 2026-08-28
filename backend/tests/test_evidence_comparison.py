from app.config import Settings
from app.main import create_app
from tests.support import request


REFERENCES = {
    "profile_id": "profile-fixture-001",
    "profile_version": 1,
    "catalogue_version": "2026.08.1",
    "recommendation_id": "recommendation-fixture-001",
    "revision_id": "summary-v1",
}


def test_synthetic_comparison_is_neutral_cited_and_canonically_isolated() -> None:
    app = create_app(
        Settings.from_env({"APP_ENV": "test", "EVIDENCE_MODE": "cached"})
    )
    response = request(
        app,
        "POST",
        "/v1/evidence/compare",
        json={
            "product_ids": [
                "synthetic-lioncity-critical-cover",
                "synthetic-harbour-essential-ci",
            ],
            "canonical_references": REFERENCES,
            "comparison_mode": "synthetic_fixture",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["label"] == "Evidence comparison - not a recommendation"
    assert payload["canonical_references"] == REFERENCES
    assert [item["provider"] for item in payload["products"]] == [
        "Harbour Life",
        "LionCity Mutual",
    ]
    assert all(item["eligibility"] == "comparison_eligible" for item in payload["products"])
    assert all("rank" not in item and "score" not in item for item in payload["products"])
    available = [
        field
        for product in payload["products"]
        for field in product["fields"]
        if field["state"] == "available"
    ]
    assert available
    assert all(field["evidence_ids"] for field in available)
    assert all(field["date_type"] != "unknown" for field in available)
    assert all(field["unit"] for field in available)


def test_comparison_rejects_duplicate_and_mixed_category_selections() -> None:
    app = create_app(
        Settings.from_env({"APP_ENV": "test", "EVIDENCE_MODE": "synthetic"})
    )
    duplicate = request(
        app,
        "POST",
        "/v1/evidence/compare",
        json={
            "product_ids": [
                "synthetic-harbour-essential-ci",
                "synthetic-harbour-essential-ci",
            ],
            "canonical_references": REFERENCES,
        },
    )
    assert duplicate.status_code == 422

    mixed = request(
        app,
        "POST",
        "/v1/evidence/compare",
        json={
            "product_ids": [
                "synthetic-lioncity-term-flex",
                "synthetic-harbour-essential-ci",
            ],
            "canonical_references": REFERENCES,
        },
    )
    assert mixed.status_code == 422
    assert "MIXED_CATEGORY_SELECTION" in mixed.json()["error"]["details"]["gate_reasons"]["selection"]


def test_cached_real_products_remain_blocked_without_source_approval() -> None:
    app = create_app(Settings.from_env({"APP_ENV": "test", "EVIDENCE_MODE": "cached"}))
    search = request(
        app,
        "POST",
        "/v1/evidence/search",
        json={"query": "critical illness protection", "max_results": 2},
    )
    product_ids = [item["policy_id"] for item in search.json()["evidence"]]
    assert len(product_ids) == 2

    compared = request(
        app,
        "POST",
        "/v1/evidence/compare",
        json={"product_ids": product_ids, "canonical_references": REFERENCES},
    )
    assert compared.status_code == 422
    payload = compared.json()
    assert payload["error"]["code"] == "EVIDENCE_COMPARISON_NOT_ELIGIBLE"
    assert all(
        "SOURCE_REUSE_NOT_APPROVED" in reasons
        for product_id, reasons in payload["error"]["details"]["gate_reasons"].items()
        if product_id != "selection"
    )