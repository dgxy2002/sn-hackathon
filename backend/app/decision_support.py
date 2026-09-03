from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import CapabilityMode
from .contracts import (
    AffordabilityAssessment,
    FitComponent,
    GapCalculation,
    PlanEvaluation,
    PlanFixture,
    ProfileField,
    RecommendationResult,
    VersionedProfile,
)
from .personalization import classify_goal


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "decision"


class ProfileNotFoundError(LookupError):
    """Raised when a disposable POC profile cannot be found."""


class ProfileVersionConflictError(ValueError):
    """Raised when a profile version conflicts with an immutable stored version."""


class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._profiles: dict[str, dict[int, VersionedProfile]] = {}

    def save(self, profile: VersionedProfile) -> VersionedProfile:
        versions = self._profiles.setdefault(profile.profile_id, {})
        existing = versions.get(profile.version)
        if existing is not None:
            if existing != profile:
                raise ProfileVersionConflictError(profile.profile_id)
            return existing
        if versions and profile.version != max(versions) + 1:
            raise ProfileVersionConflictError(profile.profile_id)
        if not versions and profile.version != 1:
            raise ProfileVersionConflictError(profile.profile_id)
        versions[profile.version] = profile
        return profile

    def get(self, profile_id: str, version: int | None = None) -> VersionedProfile:
        versions = self._profiles.get(profile_id)
        if not versions:
            raise ProfileNotFoundError(profile_id)
        selected_version = max(versions) if version is None else version
        try:
            return versions[selected_version]
        except KeyError as error:
            raise ProfileNotFoundError(profile_id) from error


class DecisionService:
    def __init__(
        self,
        mode: CapabilityMode = "synthetic",
        fixture_root: Path = FIXTURE_ROOT,
    ) -> None:
        self.mode = mode
        self.rules = json.loads((fixture_root / "rules.json").read_text(encoding="utf-8"))
        self.plans = [
            PlanFixture.model_validate(item)
            for item in json.loads((fixture_root / "plans.json").read_text(encoding="utf-8"))
        ]

    def evaluate(self, profile: VersionedProfile) -> RecommendationResult:
        run_id = self._stable_id("run", profile)
        recommendation_id = self._stable_id("recommendation", profile)
        missing_fields = self._missing_critical_fields(profile)
        if missing_fields:
            return RecommendationResult(
                run_id=run_id,
                mode=self.mode,
                recommendation_id=recommendation_id,
                profile_id=profile.profile_id,
                profile_version=profile.version,
                formulation_version=self.rules["formulation_version"],
                ruleset_version=self.rules["version"],
                catalogue_version=self.plans[0].catalogue_version,
                status="insufficient_data",
                gaps=[],
                evaluations=[],
                assumptions=["No decision input was inferred from an unknown value."],
                missing_fields=missing_fields,
                focused_questions=[self._question(field) for field in missing_fields],
            )

        goal_context = classify_goal(str(profile.data.goal.value or ""))

        income = self._number(profile.data.monthly_income)
        budget = self._number(profile.data.monthly_budget)
        liabilities = self._number(profile.data.liabilities)
        policy_known = profile.data.has_current_policy.state == "present"
        has_policy = policy_known and profile.data.has_current_policy.value is True
        existing_death = self._number(profile.data.existing_death_cover) if has_policy else 0.0
        existing_ci = self._number(profile.data.existing_ci_cover) if has_policy else 0.0
        existing_tpd = self._optional_number(profile.data.existing_tpd_cover) if has_policy else 0.0
        current_premium = self._optional_number(profile.data.current_monthly_premium)
        annual_income = income * 12
        death_target = annual_income * self.rules["death_income_multiple"] + liabilities
        ci_target = annual_income * self.rules["critical_illness_income_multiple"]
        death_gap = max(0.0, death_target - existing_death)
        ci_gap = max(0.0, ci_target - existing_ci)
        gaps = [
            GapCalculation(
                gap_type="death",
                target_amount=round(death_target, 2),
                existing_amount=existing_death,
                gap_amount=round(death_gap, 2),
                reason_code="DEATH_TARGET_NINE_TIMES_INCOME_PLUS_LIABILITIES",
            ),
            GapCalculation(
                gap_type="critical_illness",
                target_amount=round(ci_target, 2),
                existing_amount=existing_ci,
                gap_amount=round(ci_gap, 2),
                reason_code="CI_TARGET_FOUR_TIMES_INCOME",
            ),
        ]
        if existing_tpd is not None:
            gaps.append(
                GapCalculation(
                    gap_type="total_permanent_disability",
                    target_amount=round(death_target, 2),
                    existing_amount=existing_tpd,
                    gap_amount=round(max(0.0, death_target - existing_tpd), 2),
                    reason_code="TPD_TARGET_NINE_TIMES_INCOME_PLUS_LIABILITIES",
                )
            )
        current_share = (
            self._income_share(current_premium, income)
            if current_premium is not None
            else None
        )
        budget_share = self._income_share(budget, income)
        comfort_share = float(self.rules["comfort_protection_income_share"])
        maximum_share = float(self.rules["maximum_protection_income_share"])
        affordability = AffordabilityAssessment(
            monthly_income=income,
            current_monthly_premium=current_premium,
            current_income_share=(round(current_share, 4) if current_share is not None else None),
            budget_income_share=round(budget_share, 4),
            comfort_reference_share=comfort_share,
            maximum_reference_share=maximum_share,
            band=(
                "within_comfort_reference"
                if current_share is not None and current_share <= comfort_share
                else "between_references"
                if current_share is not None and current_share <= maximum_share
                else "above_maximum_reference"
                if current_share is not None
                else "unknown"
            ),
            comfort_reference_note=(
                "The 5% marker is adviser-interview input for this demo, not official guidance."
            ),
        )
        evaluations = [
            self._evaluate_plan(
                plan,
                profile,
                budget,
                income,
                current_premium or 0.0,
                gaps,
            )
            for plan in self.plans
        ]
        eligible = sorted(
            (item for item in evaluations if item.eligible),
            key=lambda item: (-(item.score or 0), item.plan_id),
        )
        for rank, item in enumerate(eligible, start=1):
            item.rank = rank
        assumptions = [
            "MoneySense income multiples are educational reference points, not personal advice.",
            "Government and group cover are not deducted because benefit amounts were not provided.",
        ]
        if goal_context.vague:
            assumptions.append(
                "The stated goal was broad, so the result uses affordability as the default priority."
            )
        elif goal_context.categories:
            assumptions.append(
                "The explanation was tailored to: "
                + ", ".join(goal_context.categories)
                + "."
            )
        if not policy_known:
            assumptions.append(
                "Current private-policy status was unsure; no private cover was deducted from the gaps."
            )
        elif not has_policy:
            assumptions.append("No current private policy was declared; no private cover was invented.")
        elif profile.data.current_monthly_premium is None or profile.data.current_monthly_premium.state != "present":
            assumptions.append("Current private-policy premiums were unknown and were not added to projected cost.")
        if has_policy and existing_tpd is None:
            assumptions.append("TPD coverage was unknown, so no separate TPD gap was calculated.")
        if (
            profile.data.emergency_savings_months.state == "present"
            and self._number(profile.data.emergency_savings_months)
            < self.rules["minimum_emergency_fund_months"]
        ):
            assumptions.append("Emergency savings are below the three-month resilience reference.")
        if has_policy:
            assumptions.append("Do not cancel or surrender existing cover; replacement and underwriting risks require review.")
        return RecommendationResult(
            run_id=run_id,
            mode=self.mode,
            recommendation_id=recommendation_id,
            profile_id=profile.profile_id,
            profile_version=profile.version,
            formulation_version=self.rules["formulation_version"],
            ruleset_version=self.rules["version"],
            catalogue_version=self.plans[0].catalogue_version,
            status="ranked" if eligible else "no_eligible_plan",
            gaps=gaps,
            evaluations=evaluations,
            assumptions=assumptions,
            missing_fields=[],
            focused_questions=[],
            affordability=affordability,
        )

    def _evaluate_plan(
        self,
        plan: PlanFixture,
        profile: VersionedProfile,
        budget: float,
        income: float,
        current_premium: float,
        gaps: list[GapCalculation],
    ) -> PlanEvaluation:
        exclusions: list[str] = []
        projected_premium = current_premium + plan.monthly_premium
        projected_share = self._income_share(projected_premium, income)
        if plan.monthly_premium > budget:
            exclusions.append("BUDGET_EXCEEDED")
        if projected_share > self.rules["maximum_protection_income_share"]:
            exclusions.append("PROTECTION_SHARE_EXCEEDED")
        preference = str(profile.data.product_preference.value).casefold()
        if preference == "protection-only" and "protection-only" not in plan.preferences:
            exclusions.append("PREFERENCE_MISMATCH")
        support_years = int(profile.data.dependant_support_years.value or 0)
        death_terms = [benefit.term_years for benefit in plan.benefits if benefit.benefit_type == "death"]
        if support_years and death_terms and max(death_terms) < support_years:
            exclusions.append("DURATION_SHORTFALL")
        if exclusions:
            return PlanEvaluation(
                plan_id=plan.plan_id,
                eligible=False,
                reason_codes=["EXCLUDED_BEFORE_RANKING"],
                exclusions=exclusions,
                trade_offs=["This option was not scored because a hard constraint failed."],
                evidence_ids=plan.evidence_ids,
                projected_monthly_premium=projected_premium,
                projected_income_share=round(projected_share, 4),
            )

        gap_by_type = {gap.gap_type: gap.gap_amount for gap in gaps}
        priorities = self._protection_priorities(profile)
        coverage_ratios = {
            "death": 0.0,
            "critical_illness": 0.0,
            "total_permanent_disability": 0.0,
            "personal_accident": 0.0,
        }
        for benefit in plan.benefits:
            gap = gap_by_type.get(benefit.benefit_type)
            if gap is not None and gap > 0:
                coverage_ratios[benefit.benefit_type] = max(
                    coverage_ratios.get(benefit.benefit_type, 0.0),
                    min(1.0, benefit.amount / gap),
                )
            elif benefit.benefit_type == "disability_income":
                coverage_ratios["total_permanent_disability"] = max(
                    coverage_ratios["total_permanent_disability"],
                    min(1.0, benefit.amount / max(income, 1.0)),
                )
        priority_total = sum(priorities.values())
        coverage_score = (
            sum(coverage_ratios[key] * priorities[key] for key in priorities)
            / priority_total
            if priority_total > 0
            else 0.25
        )
        affordability_score = max(0.0, 1 - (plan.monthly_premium / budget))
        preference_score = 1.0 if preference in plan.preferences else 0.5
        component_values = {
            "coverage": coverage_score,
            "affordability": affordability_score,
            "preference": preference_score,
        }
        components = [
            FitComponent(
                component=name,
                score=round(score, 4),
                weight=self.rules["weights"][name],
                reason_code=f"{name.upper()}_FIT",
            )
            for name, score in component_values.items()
        ]
        total = sum(item.score * item.weight for item in components)
        return PlanEvaluation(
            plan_id=plan.plan_id,
            eligible=True,
            score=round(total, 4),
            fit_components=components,
            reason_codes=[
                "ELIGIBLE",
                "DETERMINISTIC_WEIGHTED_FIT",
                "USER_PROTECTION_PRIORITIES_APPLIED",
            ],
            trade_offs=["Illustrative premium and benefits use synthetic fixture data."],
            evidence_ids=plan.evidence_ids,
            projected_monthly_premium=projected_premium,
            projected_income_share=round(projected_share, 4),
        )

    def _missing_critical_fields(self, profile: VersionedProfile) -> list[str]:
        fields: dict[str, ProfileField[Any]] = {
            "monthly_income": profile.data.monthly_income,
            "monthly_expenses": profile.data.monthly_expenses,
            "monthly_budget": profile.data.monthly_budget,
            "product_preference": profile.data.product_preference,
            "goal": profile.data.goal,
        }
        if profile.data.has_current_policy.state == "present" and profile.data.has_current_policy.value is True:
            fields.update(
                existing_death_cover=profile.data.existing_death_cover,
                existing_ci_cover=profile.data.existing_ci_cover,
            )
        return [name for name, field in fields.items() if field.state != "present"]

    @staticmethod
    def _protection_priorities(profile: VersionedProfile) -> dict[str, float]:
        field = profile.data.protection_priorities
        if field is None or field.state != "present" or field.value is None:
            return {
                "death": 1.0,
                "critical_illness": 1.0,
                "total_permanent_disability": 1.0,
                "personal_accident": 1.0,
            }
        return {
            "death": field.value.death / 100,
            "critical_illness": field.value.critical_illness / 100,
            "total_permanent_disability": field.value.disability / 100,
            "personal_accident": field.value.personal_accident / 100,
        }

    @staticmethod
    def _number(field: ProfileField[Any]) -> float:
        return float(field.value or 0)

    @staticmethod
    def _optional_number(field: ProfileField[Any] | None) -> float | None:
        if field is None or field.state != "present":
            return None
        return float(field.value or 0)

    @staticmethod
    def _income_share(monthly_premium: float, monthly_income: float) -> float:
        if monthly_income > 0:
            return monthly_premium / monthly_income
        return 0.0 if monthly_premium == 0 else 1.0

    @staticmethod
    def _question(field: str) -> str:
        labels = {
            "monthly_income": "What is your monthly take-home income?",
            "monthly_expenses": "What are your monthly essential expenses?",
            "monthly_budget": "What monthly insurance budget feels sustainable?",
            "product_preference": "Do you prefer protection-only cover or savings features?",
            "has_current_policy": "Do you currently have a private insurance policy?",
            "existing_death_cover": "What death benefit does your current policy provide?",
            "existing_ci_cover": "What critical-illness benefit does your current policy provide?",
            "goal": "What is your primary insurance goal?",
        }
        return labels[field]

    def _stable_id(self, prefix: str, profile: VersionedProfile) -> str:
        payload = {
            "profile": profile.model_dump(mode="json"),
            "ruleset_version": self.rules["version"],
            "catalogue_version": self.plans[0].catalogue_version,
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
        return f"{prefix}-{digest}"