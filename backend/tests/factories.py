from datetime import date, datetime, timezone
from typing import Any

from app.contracts import FieldProvenance, ProfileData, ProfileField, VersionedProfile


NOW = datetime(2026, 8, 28, tzinfo=timezone.utc)


def field(value: Any, *, state: str = "present") -> ProfileField:
    return ProfileField(
        state=state,
        value=value,
        provenance=FieldProvenance(source="fixture", recorded_at=NOW),
    )


def make_profile(
    *,
    profile_id: str = "profile-fixture-001",
    version: int = 1,
    monthly_income: float | None = 4200.0,
    monthly_income_state: str = "present",
    monthly_budget: float = 180.0,
    has_current_policy: bool | None = False,
    policy_state: str = "present",
    existing_death_cover: float | None = None,
    existing_ci_cover: float | None = None,
) -> VersionedProfile:
    cover_state = "present" if has_current_policy else "unknown"
    return VersionedProfile(
        profile_id=profile_id,
        version=version,
        as_of_date=date(2026, 8, 28),
        consent=True,
        data=ProfileData(
            life_stage=field("first-job"),
            employment_status=field("full-time"),
            goal=field("protect dependants"),
            target_amount=field(500_000.0),
            target_date=field(date(2046, 8, 28)),
            monthly_income=field(monthly_income, state=monthly_income_state),
            monthly_expenses=field(2_400.0),
            emergency_savings_months=field(6.0),
            dependant_count=field(0),
            dependant_support_years=field(0),
            liabilities=field(0.0),
            has_current_policy=field(has_current_policy, state=policy_state),
            existing_death_cover=field(existing_death_cover, state=cover_state),
            existing_ci_cover=field(existing_ci_cover, state=cover_state),
            government_cover=field(["MediShield Life"]),
            employer_cover=field(True),
            monthly_budget=field(monthly_budget),
            product_preference=field("protection-only"),
        ),
    )