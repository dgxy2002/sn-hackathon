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
        "protect dependants",
        "protect my dependants",
        "protect my parents",
        "protect my family",
        "support my family",
    ),
    "income_protection": ("protect my income", "replace my income"),
    "cashflow_control": ("stop overspending", "manage spending", "budget better"),
    "debt_reduction": ("pay off debt", "clear my loan", "pay off my loan"),
    "wealth_building": ("start investing", "grow my wealth", "invest"),
}

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def classify_goal(text: str) -> GoalContext:
    normalized = " ".join(text.casefold().split())
    categories = [
        category
        for category, phrases in GOAL_PATTERNS.items()
        if any(phrase in normalized for phrase in phrases)
    ]

    timeframe_match = re.search(
        r"\b(?:in|within|over)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+years?\b",
        normalized,
    )
    timeframe_value = timeframe_match.group(1) if timeframe_match else None
    timeframe_years = (
        int(timeframe_value)
        if timeframe_value and timeframe_value.isdigit()
        else NUMBER_WORDS.get(timeframe_value or "")
    )

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
    "age",
    "occupation",
    "monthly_income",
    "monthly_expenses",
    "dependant_count",
    "has_current_policy",
    "monthly_budget",
)


QUESTION_DETAILS = {
    "age": (
        "What is your age?",
        "Age helps keep the profile and policy review relevant.",
    ),
    "occupation": (
        "What is your occupation or current student status?",
        "Occupation provides context without assuming employer coverage.",
    ),
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
    "has_current_policy": (
        "Do you currently have a private insurance policy?",
        "This determines whether existing private cover needs to be reviewed.",
    ),
    "existing_death_cover": (
        "What death or permanent-disability coverage do you already have?",
        "This prevents the system from overstating your protection gap.",
    ),
    "existing_ci_cover": (
        "What critical-illness coverage do you already have?",
        "This prevents duplicate or unnecessary cover assumptions.",
    ),
    "existing_tpd_cover": (
        "What total permanent disability coverage do you already have?",
        "This allows a separate TPD gap to be shown without inferring cover.",
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

    question_order = list(QUESTION_ORDER)
    if data.has_current_policy.state == "present" and data.has_current_policy.value:
        policy_index = question_order.index("has_current_policy") + 1
        question_order[policy_index:policy_index] = [
            "existing_death_cover",
            "existing_ci_cover",
            "existing_tpd_cover",
        ]

    for field_name in question_order:
        field: ProfileField[Any] | None = getattr(data, field_name)

        if field is not None and field.state != "present":
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
    priorities_field = profile.data.protection_priorities
    explicit_priorities = (
        priorities_field.value.model_dump()
        if priorities_field is not None
        and priorities_field.state == "present"
        and priorities_field.value is not None
        else None
    )

    return {
        "profile_version": profile.version,
        "age": profile.data.age.value if profile.data.age else None,
        "gender": profile.data.gender.value if profile.data.gender else None,
        "occupation": profile.data.occupation.value if profile.data.occupation else None,
        "goal_categories": list(goal.categories),
        "priorities": explicit_priorities or list(goal.priorities),
        "timeframe_years": goal.timeframe_years,
        "goal_is_vague": goal.vague,
        "dependant_count": profile.data.dependant_count.value,
        "current_monthly_premium": (
            profile.data.current_monthly_premium.value
            if profile.data.current_monthly_premium
            else None
        ),
        "unknown_fields": [
            name
            for name in type(profile.data).model_fields
            if getattr(profile.data, name) is None
            or getattr(profile.data, name).state != "present"
        ],
    }