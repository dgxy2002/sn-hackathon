from scripts.evaluate_material_terms import evaluate_material_terms


def test_phase3_synthetic_gold_set_meets_baseline() -> None:
    metrics = evaluate_material_terms()

    assert metrics.case_count == 5
    assert metrics.precision >= 0.95
    assert metrics.recall >= 0.90
    assert metrics.unknown_accuracy == 1.0
    assert metrics.citation_binding == 1.0