import json
from pathlib import Path


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "policies"


def test_policy_fixture_manifest_is_complete_and_bounded() -> None:
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text())

    assert manifest["fixture_version"] == "1.0.0"
    assert manifest["licensing"]
    assert set(manifest["match_rules"]) == {
        "text",
        "amount_sgd",
        "duration",
        "enum",
        "unknown",
    }

    documents = manifest["documents"]
    assert len(documents) == 3
    assert len({document["fixture_id"] for document in documents}) == 3

    page_width = manifest["page_size"]["width"]
    page_height = manifest["page_size"]["height"]
    field_paths = set()

    for document in documents:
        assert document["synthetic"] is True
        source = FIXTURE_DIR / document["file"]
        assert source.is_file()
        assert source.read_text().startswith("<svg")

        for field in document["fields"]:
            field_paths.add(field["path"])
            assert field["match"] in manifest["match_rules"]
            assert field["page"] == 1
            region = field["region"]
            assert 0 <= region["x"] < page_width
            assert 0 <= region["y"] < page_height
            assert region["x"] + region["width"] <= page_width
            assert region["y"] + region["height"] <= page_height

    assert {
        "policy.insurer_name",
        "policy.plan_name",
        "policy.policy_type",
        "premium.amount_sgd",
        "premium.frequency",
    }.issubset(field_paths)


def test_unknown_fixture_truth_is_explicit() -> None:
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text())
    unknown_fields = [
        field
        for document in manifest["documents"]
        for field in document["fields"]
        if field["match"] == "unknown"
    ]

    assert unknown_fields == [
        {
            "path": "underwriting.occupation_class",
            "value": "unknown",
            "match": "unknown",
            "page": 1,
            "region": {"x": 92, "y": 984, "width": 958, "height": 62},
        }
    ]