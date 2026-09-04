from app.personalization import build_context, classify_goal, next_question
from tests.factories import make_profile


def test_goal_classification_uses_project_wording_and_word_timeframes() -> None:
    family = classify_goal("Protect dependants")
    home = classify_goal("I want to buy a flat in three years")

    assert family.categories == ("family_protection",)
    assert family.priorities == ("family_protection", "affordability")
    assert home.categories == ("home_purchase",)
    assert home.timeframe_years == 3


def test_no_policy_profile_does_not_ask_for_nonexistent_private_cover() -> None:
    profile = make_profile()
    profile.data.monthly_budget.state = "unknown"
    profile.data.monthly_budget.value = None

    question = next_question(profile)

    assert question is not None
    assert question.field == "monthly_budget"


def test_personalization_context_records_version_goals_and_unknowns() -> None:
    profile = make_profile(version=2, goal="Protect my income")

    context = build_context(profile)

    assert context["profile_version"] == 2
    assert context["goal_categories"] == ["income_protection"]
    assert context["priorities"] == ["affordability"]
    assert "existing_death_cover" in context["unknown_fields"]