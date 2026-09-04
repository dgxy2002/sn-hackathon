from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .contracts import ProfileField, VersionedProfile


@dataclass(frozen=True)
class GoalContext:
    categories: tuple[str, ...]
    priorities: tuple[str, ...]
    timeframe_years: int | None
    vague: bool


@dataclass(frozen=True)
class FocusedQuestion:
    field: str
    question: str
    reason: str


GOAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "home_purchase": ("buy a house", "buy a home", "buy a flat", "property"),
    "emergency_fund": ("emergency fund", "rainy day", "build savings"),
    "family_protection": (
        "protect my parents",
        "protect my family",
        "support my family",
    ),
    "cashflow_control": ("stop overspending", "manage spending", "budget better"),
    "debt_reduction": ("pay off debt", "clear my loan", "pay off my loan"),
    "wealth_building": ("start investing", "grow my wealth", "invest"),
}

TIMEFRAME_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def classify_goal(text: str) -> GoalContext:
    normalized = " ".join(text.casefold().split())
    categories = [
        category
        for category, phrases in GOAL_PATTERNS.items()
        if any(phrase in normalized for phrase in phrases)
    ]

    timeframe_match = re.search(
        r"\b(?:in|within|over)\s+(\d+|one|two|three|four|five)\s+years?\b",
        normalized,
    )
    timeframe_years = None
    if timeframe_match:
        value = timeframe_match.group(1)
        timeframe_years = int(value) if value.isdigit() else TIMEFRAME_WORDS[value]

    if "family_protection" in categories:
        priorities = ("family_protection", "affordability")
    elif "home_purchase" in categories:
        priorities = ("affordability", "short_term_savings")
    elif "debt_reduction" in categories:
        priorities = ("cashflow_control", "affordability")
    else:
        priorities = ("affordability",)

    return GoalContext(
        categories=tuple(categories),
        priorities=priorities,
        timeframe_years=timeframe_years,
        vague=not categories,
    )


QUESTION_ORDER = (
    "monthly_income",
    "monthly_expenses",
    "dependant_count",
    "existing_death_cover",
    "existing_ci_cover",
    "target_date",
    "monthly_budget",
    "product_preference",
)


QUESTION_DETAILS = {
    "monthly_income": (
        "What is your monthly take-home income?",
        "This helps assess whether a plan is affordable.",
    ),
    "monthly_expenses": (
        "What are your monthly essential expenses?",
        "This prevents the system from suggesting an unrealistic premium.",
    ),
    "dependant_count": (
        "Do you financially support anyone else?",
        "Dependants affect the amount of protection that may be relevant.",
    ),
    "existing_death_cover": (
        "What death or permanent-disability coverage do you already have?",
        "This prevents the system from overstating your protection gap.",
    ),
    "existing_ci_cover": (
        "What critical-illness coverage do you already have?",
        "This prevents duplicate or unnecessary cover assumptions.",
    ),
    "target_date": (
        "When would you like to achieve this goal?",
        "The timeframe helps distinguish short-term affordability from longer-term protection.",
    ),
    "monthly_budget": (
        "What monthly insurance budget feels sustainable?",
        "This is used to exclude plans that may be unaffordable.",
    ),
    "product_preference": (
        "Do you prefer protection-only cover or plans with savings features?",
        "This helps filter plans according to your preference.",
    ),
}


def next_question(profile: VersionedProfile) -> FocusedQuestion | None:
    data = profile.data

    for field_name in QUESTION_ORDER:
        field: ProfileField[Any] = getattr(data, field_name)

        if field.state != "present":
            question, reason = QUESTION_DETAILS[field_name]
            return FocusedQuestion(
                field=field_name,
                question=question,
                reason=reason,
            )

    goal = classify_goal(str(data.goal.value or ""))
    if goal.vague:
        return FocusedQuestion(
            field="goal",
            question=(
                "What is your main priority: building savings, protecting "
                "family, reducing debt, or buying a home?"
            ),
            reason="A clearer goal allows the explanation to be personalised.",
        )

    return None


def build_context(profile: VersionedProfile) -> dict[str, Any]:
    goal = classify_goal(str(profile.data.goal.value or ""))

    return {
        "profile_version": profile.version,
        "goal_categories": list(goal.categories),
        "priorities": list(goal.priorities),
        "timeframe_years": goal.timeframe_years,
        "goal_is_vague": goal.vague,
        "dependant_count": profile.data.dependant_count.value,
        "unknown_fields": [
            name
            for name in profile.data.model_fields
            if getattr(profile.data, name).state != "present"
        ],
    }