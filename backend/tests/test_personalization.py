from datetime import date

from app.personalization import classify_goal, next_question
from tests.factories import make_profile


def test_classifies_home_purchase_goal() -> None:
    result = classify_goal("I want to buy a flat in three years")

    assert result.categories == ("home_purchase",)
    assert result.timeframe_years == 3
    assert "affordability" in result.priorities
    assert result.vague is False


def test_classifies_family_protection_goal() -> None:
    result = classify_goal("I want to protect my parents")

    assert result.categories == ("family_protection",)
    assert result.vague is False


def test_vague_goal_requires_clarification() -> None:
    result = classify_goal("I want to be financially secure")

    assert result.vague is True
    assert result.categories == ()


def test_missing_information_returns_one_focused_question() -> None:
    profile = make_profile(monthly_income=None, monthly_income_state="unknown")

    question = next_question(profile)

    assert question is not None
    assert question.field == "monthly_income"