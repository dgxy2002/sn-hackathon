from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import re
from threading import Lock
from uuid import uuid4

from .decision_support import DecisionService, InMemoryProfileRepository
from .evidence import EvidenceDependencyError, EvidenceService
from .contracts import (
    ActionEvent,
    AssistantMessage,
    Citation,
    ConversationMessageRequest,
    ConversationMessageResponse,
    ConversationResponse,
    ChangeProposal,
    EvidenceSearchRequest,
    GapDelta,
    PatchField,
    ProfilePatch,
    ProposalDecisionRequest,
    ProposalDecisionResponse,
    ReplayEvent,
    ReplayResponse,
    SummaryDelta,
    SummaryRevision,
    SuggestedPrompt,
    UndoRequest,
    UndoResponse,
    ValueDelta,
    VersionedProfile,
    RecommendationResult,
    FieldProvenance,
)


class ConversationNotFoundError(LookupError):
    pass


class RevisionConflictError(ValueError):
    pass


class ProposalNotFoundError(LookupError):
    pass


class ProposalStateError(ValueError):
    pass


class UndoNotAvailableError(ValueError):
    pass


@dataclass
class ConversationRecord:
    conversation_id: str
    active_revision_id: str
    responses: dict[str, ConversationMessageResponse] = field(default_factory=dict)
    profile: VersionedProfile | None = None
    recommendation: RecommendationResult | None = None
    proposals: dict[str, ChangeProposal] = field(default_factory=dict)
    revisions: dict[str, SummaryRevision] = field(default_factory=dict)
    proposal_decisions: dict[str, ProposalDecisionResponse] = field(default_factory=dict)
    undo_responses: dict[str, UndoResponse] = field(default_factory=dict)
    events: list[ReplayEvent] = field(default_factory=list)


class ConversationService:
    def __init__(
        self,
        evidence_service: EvidenceService | None = None,
        profile_repository: InMemoryProfileRepository | None = None,
        decision_service: DecisionService | None = None,
    ) -> None:
        self._records: dict[str, ConversationRecord] = {}
        self._lock = Lock()
        self._evidence_service = evidence_service
        self._profiles = profile_repository
        self._decisions = decision_service

    def create(
        self,
        active_revision_id: str,
        profile: VersionedProfile | None = None,
        recommendation: RecommendationResult | None = None,
    ) -> ConversationResponse:
        conversation_id = f"conv-{uuid4()}"
        record = ConversationRecord(
            conversation_id=conversation_id,
            active_revision_id=active_revision_id,
            profile=profile,
            recommendation=recommendation,
        )
        if profile is not None and recommendation is not None:
            if self._profiles is not None:
                self._profiles.save(profile)
            record.revisions[active_revision_id] = SummaryRevision(
                revision_id=active_revision_id,
                created_at=self._now(),
                cause="initial",
                profile=profile,
                recommendation=recommendation,
            )
        self._event(record, "conversation_created", revision_id=active_revision_id)
        with self._lock:
            self._records[conversation_id] = record

        return ConversationResponse(
            conversation_id=conversation_id,
            active_revision_id=active_revision_id,
            suggested_prompts=[
                SuggestedPrompt(
                    id="why-ranked-first",
                    label="Why this ranks first",
                    message="Why does the first eligible option rank first?",
                ),
                SuggestedPrompt(
                    id="show-critical-illness",
                    label="Show critical illness",
                    message="Show only the critical illness option.",
                ),
                SuggestedPrompt(
                    id="show-unknowns",
                    label="Show assumptions",
                    message="What does the ranking still not know?",
                ),
                SuggestedPrompt(
                    id="explore-integrated-shield",
                    label="Explore hospital cover",
                    message="Which cached plans mention Integrated Shield hospital cover?",
                ),
            ],
            profile_id=profile.profile_id if profile else None,
            recommendation_id=(recommendation.recommendation_id if recommendation else None),
        )

    def respond(
        self, conversation_id: str, request: ConversationMessageRequest
    ) -> ConversationMessageResponse:
        with self._lock:
            record = self._records.get(conversation_id)
            if record is None:
                raise ConversationNotFoundError(conversation_id)
            if request.active_revision_id != record.active_revision_id:
                raise RevisionConflictError(record.active_revision_id)
            cached = record.responses.get(request.client_message_id)
            if cached is not None:
                return cached

            response = self._resolve(record, request)
            record.responses[request.client_message_id] = response
            self._event(
                record,
                "message_resolved",
                run_id=response.run_id,
                revision_id=record.active_revision_id,
                safe_details={"state": response.state},
            )
            return response

    def confirm_proposal(
        self,
        conversation_id: str,
        proposal_id: str,
        request: ProposalDecisionRequest,
    ) -> ProposalDecisionResponse:
        with self._lock:
            record = self._get_record(conversation_id)
            cached = record.proposal_decisions.get(request.client_request_id)
            if cached is not None:
                return cached
            self._require_revision(record, request.expected_revision_id)
            proposal = self._get_proposal(record, proposal_id)
            if proposal.status != "pending":
                raise ProposalStateError(proposal.status)
            if record.profile is None or record.recommendation is None or self._decisions is None:
                raise ProposalStateError("dependencies_unavailable")

            profile = self._apply_patch(record.profile, proposal.patch)
            recommendation = self._decisions.evaluate(profile)
            if self._profiles is not None:
                self._profiles.save(profile)
            revision_id = f"summary-{uuid4()}"
            delta = self._delta(record.recommendation, recommendation, proposal.patch)
            revision = SummaryRevision(
                revision_id=revision_id,
                parent_revision_id=record.active_revision_id,
                created_at=self._now(),
                cause="confirmed_profile_patch",
                profile=profile,
                recommendation=recommendation,
                delta=delta,
            )
            applied = proposal.model_copy(update={"status": "applied"})
            record.proposals[proposal_id] = applied
            record.revisions[revision_id] = revision
            record.profile = profile
            record.recommendation = recommendation
            record.active_revision_id = revision_id
            response = ProposalDecisionResponse(
                conversation_id=conversation_id,
                state="completed",
                active_revision_id=revision_id,
                proposal=applied,
                revision=revision,
            )
            record.proposal_decisions[request.client_request_id] = response
            self._event(record, "proposal_confirmed", proposal_id=proposal_id)
            self._event(record, "recommendation_rerun", run_id=recommendation.run_id)
            self._event(record, "revision_applied", revision_id=revision_id)
            return response

    def cancel_proposal(
        self,
        conversation_id: str,
        proposal_id: str,
        request: ProposalDecisionRequest,
    ) -> ProposalDecisionResponse:
        with self._lock:
            record = self._get_record(conversation_id)
            cached = record.proposal_decisions.get(request.client_request_id)
            if cached is not None:
                return cached
            self._require_revision(record, request.expected_revision_id)
            proposal = self._get_proposal(record, proposal_id)
            if proposal.status != "pending":
                raise ProposalStateError(proposal.status)
            cancelled = proposal.model_copy(update={"status": "cancelled"})
            record.proposals[proposal_id] = cancelled
            response = ProposalDecisionResponse(
                conversation_id=conversation_id,
                state="cancelled",
                active_revision_id=record.active_revision_id,
                proposal=cancelled,
            )
            record.proposal_decisions[request.client_request_id] = response
            self._event(record, "proposal_cancelled", proposal_id=proposal_id)
            return response

    def list_revisions(self, conversation_id: str) -> list[SummaryRevision]:
        with self._lock:
            return list(self._get_record(conversation_id).revisions.values())

    def replay(self, conversation_id: str) -> ReplayResponse:
        with self._lock:
            record = self._get_record(conversation_id)
            return ReplayResponse(
                conversation_id=conversation_id,
                active_revision_id=record.active_revision_id,
                events=record.events,
            )

    def undo(self, conversation_id: str, request: UndoRequest) -> UndoResponse:
        with self._lock:
            record = self._get_record(conversation_id)
            cached = record.undo_responses.get(request.client_request_id)
            if cached is not None:
                return cached
            self._require_revision(record, request.expected_revision_id)
            current = record.revisions.get(record.active_revision_id)
            if current is None or current.parent_revision_id is None:
                raise UndoNotAvailableError(record.active_revision_id)
            restored = record.revisions[current.parent_revision_id]
            record.active_revision_id = restored.revision_id
            record.profile = restored.profile
            record.recommendation = restored.recommendation
            response = UndoResponse(
                conversation_id=conversation_id,
                active_revision_id=restored.revision_id,
                undone_revision_id=current.revision_id,
                restored_revision=restored,
            )
            record.undo_responses[request.client_request_id] = response
            self._event(
                record,
                "revision_undone",
                revision_id=restored.revision_id,
                safe_details={"undone_revision_id": current.revision_id},
            )
            return response

    def _resolve(
        self, record: ConversationRecord, request: ConversationMessageRequest
    ) -> ConversationMessageResponse:
        text = " ".join(request.message.casefold().split())
        run_id = f"run-{uuid4()}"
        action_id = f"action-{uuid4()}"
        message_id = f"message-{uuid4()}"

        if (
            "critical illness" in text or "critical-illness" in text
        ) and ("show only" in text or "filter" in text):
            return ConversationMessageResponse(
                conversation_id=record.conversation_id,
                client_message_id=request.client_message_id,
                run_id=run_id,
                state="completed",
                active_revision_id=record.active_revision_id,
                assistant_message=AssistantMessage(
                    message_id=message_id,
                    content=(
                        "I filtered the table to the synthetic critical-illness option. "
                        "This changes presentation only; it does not change the ranking."
                    ),
                    citations=[
                        Citation(
                            evidence_id="SYN-HEC-02",
                            label="Harbour Essential CI synthetic fixture",
                            synthetic=True,
                        )
                    ],
                ),
                actions=[
                    ActionEvent(
                        action_id=action_id,
                        intent="FILTER_COMPARISON",
                        tool="FILTER_COMPARISON",
                        target="comparison:critical-illness",
                        status="completed",
                        evidence_count=1,
                        confirmation_required=False,
                        affected_regions=["comparison", "agent"],
                    )
                ],
            )

        if "not know" in text or "unknown" in text or "assumption" in text:
            return ConversationMessageResponse(
                conversation_id=record.conversation_id,
                client_message_id=request.client_message_id,
                run_id=run_id,
                state="completed",
                active_revision_id=record.active_revision_id,
                assistant_message=AssistantMessage(
                    message_id=message_id,
                    content=(
                        "The comparison still cannot verify whether declared benefits overlap, "
                        "the exact rider terms, or any insurer underwriting outcome. I opened "
                        "the assumptions section."
                    ),
                    citations=[],
                ),
                actions=[
                    ActionEvent(
                        action_id=action_id,
                        intent="FOCUS_SECTION",
                        tool="FOCUS_SECTION",
                        target="reasoning:assumptions",
                        status="completed",
                        evidence_count=0,
                        confirmation_required=False,
                        affected_regions=["assumptions", "agent"],
                    )
                ],
            )

        if any(
            term in text
            for term in ("budget", "dependant", "dependent", "goal", "premium")
        ):
            proposal = self._profile_proposal(record, text)
            if proposal is not None:
                field_label = proposal.patch.field_name.replace("_", " ")
                old_value = self._display_patch_value(
                    proposal.patch.field_name, proposal.patch.old_value
                )
                proposed_value = self._display_patch_value(
                    proposal.patch.field_name, proposal.patch.proposed_value
                )
                record.proposals[proposal.proposal_id] = proposal
                self._event(record, "proposal_created", proposal_id=proposal.proposal_id)
                return ConversationMessageResponse(
                    conversation_id=record.conversation_id,
                    client_message_id=request.client_message_id,
                    run_id=run_id,
                    state="waiting_for_confirmation",
                    active_revision_id=record.active_revision_id,
                    assistant_message=AssistantMessage(
                        message_id=message_id,
                        content=(
                            f"I can change your {field_label} from {old_value} "
                            f"to {proposed_value}. Confirm before I create "
                            "a new profile version and rerun the deterministic comparison."
                        ),
                        citations=[],
                    ),
                    actions=[
                        ActionEvent(
                            action_id=action_id,
                            intent="PROPOSE_PROFILE_PATCH",
                            tool="PROPOSE_PROFILE_PATCH",
                            target="profile:decision-input",
                            status="pending",
                            evidence_count=0,
                            confirmation_required=True,
                            affected_regions=["agent"],
                        )
                    ],
                    proposal=proposal,
                )
            return ConversationMessageResponse(
                conversation_id=record.conversation_id,
                client_message_id=request.client_message_id,
                run_id=run_id,
                state="unsupported",
                active_revision_id=record.active_revision_id,
                assistant_message=AssistantMessage(
                    message_id=message_id,
                    content=(
                        "That would change a decision input and requires confirmation plus a "
                        "fresh deterministic recommendation. Those dependencies are not ready, "
                        "so I left your summary unchanged."
                    ),
                    citations=[],
                ),
                actions=[
                    ActionEvent(
                        action_id=action_id,
                        intent="PROPOSE_PROFILE_PATCH",
                        tool="PROPOSE_PROFILE_PATCH",
                        target="profile:decision-input",
                        status="blocked",
                        evidence_count=0,
                        confirmation_required=True,
                        affected_regions=["agent"],
                        error_code="DEPENDENCY_UNAVAILABLE",
                    )
                ],
            )

        if "why" in text or "rank" in text:
            top_plan_id = (
                self._top_plan(record.recommendation) if record.recommendation else None
            )
            top_evaluation = next(
                (
                    item
                    for item in (
                        record.recommendation.evaluations if record.recommendation else []
                    )
                    if item.plan_id == top_plan_id
                ),
                None,
            )
            if top_evaluation is None:
                return self._unsupported_answer(
                    record,
                    request,
                    run_id,
                    action_id,
                    message_id,
                    "No eligible synthetic option is currently ranked first.",
                    "NO_ELIGIBLE_PLAN",
                )
            plan_name = self._plan_label(top_evaluation.plan_id)
            component_summary = ", ".join(
                f"{item.component} {item.score:.2f}"
                for item in top_evaluation.fit_components
            )
            return ConversationMessageResponse(
                conversation_id=record.conversation_id,
                client_message_id=request.client_message_id,
                run_id=run_id,
                state="completed",
                active_revision_id=record.active_revision_id,
                assistant_message=AssistantMessage(
                    message_id=message_id,
                    content=(
                        f"{plan_name} ranks first in this synthetic result because its "
                        "deterministic weighted fit is highest among eligible options"
                        f" ({component_summary}). The calculation applies your protection "
                        "priorities, premium ceiling, and product preference; it does not "
                        "establish suitability or guarantee complete coverage."
                    ),
                    citations=[
                        Citation(
                            evidence_id=evidence_id,
                            label=f"{plan_name} synthetic fixture",
                            synthetic=True,
                        )
                        for evidence_id in top_evaluation.evidence_ids
                    ],
                ),
                actions=[
                    ActionEvent(
                        action_id=action_id,
                        intent="FOCUS_SECTION",
                        tool="FOCUS_SECTION",
                        target="reasoning:ranking",
                        status="completed",
                        evidence_count=len(top_evaluation.evidence_ids),
                        confirmation_required=False,
                        affected_regions=["ranking_reason", "agent"],
                    )
                ],
            )

        if self._evidence_service is None:
            return self._unsupported_answer(
                record,
                request,
                run_id,
                action_id,
                message_id,
                "Evidence search is not available, so I left your summary unchanged.",
                "DEPENDENCY_UNAVAILABLE",
            )

        try:
            evidence_response = self._evidence_service.search(
                EvidenceSearchRequest(query=request.message, max_results=5)
            )
        except EvidenceDependencyError:
            return self._unsupported_answer(
                record,
                request,
                run_id,
                action_id,
                message_id,
                "The evidence service is temporarily unavailable. Your summary is unchanged.",
                "DEPENDENCY_UNAVAILABLE",
            )

        if not evidence_response.evidence:
            return self._unsupported_answer(
                record,
                request,
                run_id,
                action_id,
                message_id,
                (
                    "I could not find supporting brochure evidence in the cached catalogue. "
                    "I have not inferred an answer or changed your summary."
                ),
                "NO_EVIDENCE",
            )

        products = list(
            dict.fromkeys(
                f"{item.provider} {item.product}" for item in evidence_response.evidence
            )
        )
        product_summary = ", ".join(products[:3])
        if len(products) > 3:
            product_summary += f", and {len(products) - 3} more"
        citations = [
            Citation(
                evidence_id=item.evidence_id,
                label=f"{item.provider} · {item.product} · {item.section_title}",
                url=item.source_url,
                synthetic=item.synthetic,
                provider=item.provider,
                product=item.product,
                excerpt=item.value,
                source_file=item.source_file,
                source_approval=item.source_approval,
                evidence_state=item.evidence_state,
                freshness_status=item.freshness_status,
                document_as_of_date=item.document_as_of_date,
                product_effective_date=item.product_effective_date,
                document_version=item.document_version,
                similarity=item.similarity,
            )
            for item in evidence_response.evidence
        ]
        return ConversationMessageResponse(
            conversation_id=record.conversation_id,
            client_message_id=request.client_message_id,
            run_id=run_id,
            state="completed",
            active_revision_id=record.active_revision_id,
            assistant_message=AssistantMessage(
                message_id=message_id,
                content=(
                    f"I found {len(citations)} read-only brochure excerpts across "
                    f"{product_summary}. They are cached evidence, not recommendations; "
                    "approval, freshness, and unknown dates remain visible below."
                ),
                citations=citations,
            ),
            actions=[
                ActionEvent(
                    action_id=action_id,
                    intent="ANSWER_QUESTION",
                    tool="ANSWER_QUESTION",
                    target="evidence:cached-catalogue",
                    status="completed",
                    evidence_count=len(citations),
                    confirmation_required=False,
                    affected_regions=["agent"],
                )
            ],
        )

    def _profile_proposal(
        self, record: ConversationRecord, text: str
    ) -> ChangeProposal | None:
        if record.profile is None or record.recommendation is None or self._decisions is None:
            return None

        field_name: PatchField | None = None
        proposed_value: str | float | int | None = None
        reason = ""
        affected_calculations: list[str] = []
        budget_match = re.search(
            r"budget\s+(?:to\s+|is\s+)?(?:s\$|sgd|\$)?\s*(\d+(?:\.\d+)?)",
            text,
        )
        premium_match = re.search(
            r"(?:current\s+)?(?:monthly\s+)?premium\s+(?:to\s+|is\s+)?"
            r"(?:s\$|sgd|\$)?\s*(\d+(?:\.\d+)?)",
            text,
        )
        dependant_match = re.search(
            r"(?:dependants?|dependents?)\s+(?:to\s+|is\s+)?(\d+)", text
        )
        goal_match = re.search(r"goal\s+(?:to\s+|is\s+)(.+?)(?:[.!]|$)", text)
        if budget_match:
            field_name = "monthly_budget"
            proposed_value = float(budget_match.group(1))
            reason = "User requested a different sustainable monthly premium budget."
            affected_calculations = ["affordability", "eligibility", "weighted_fit", "ranking"]
        elif premium_match:
            field_name = "current_monthly_premium"
            proposed_value = float(premium_match.group(1))
            reason = "User corrected the total current monthly insurance premium."
            affected_calculations = ["affordability", "eligibility", "ranking"]
        elif dependant_match:
            field_name = "dependant_count"
            proposed_value = int(dependant_match.group(1))
            reason = "User corrected the number of people who depend on their income."
            affected_calculations = ["profile_context", "explanation"]
        elif goal_match:
            field_name = "goal"
            proposed_value = goal_match.group(1).strip()
            reason = "User clarified their primary protection goal."
            affected_calculations = ["personalization", "explanation"]
        if field_name is None or proposed_value is None:
            return None
        current = getattr(record.profile.data, field_name)
        if current is None:
            return None
        proposal_id = f"proposal-{uuid4()}"
        return ChangeProposal(
            proposal_id=proposal_id,
            conversation_id=record.conversation_id,
            base_revision_id=record.active_revision_id,
            status="pending",
            patch=ProfilePatch(
                base_profile_version=record.profile.version,
                field_name=field_name,
                old_state=current.state,
                old_value=current.value,
                proposed_state="present",
                proposed_value=proposed_value,
                reason=reason,
                affected_calculations=affected_calculations,
            ),
        )

    @staticmethod
    def _display_patch_value(field_name: str, value: str | float | int | bool | None) -> str:
        if field_name in {"monthly_budget", "current_monthly_premium"} and isinstance(
            value, (int, float)
        ):
            return f"S${value:g}"
        return str(value)

    @staticmethod
    def _apply_patch(profile: VersionedProfile, patch: ProfilePatch) -> VersionedProfile:
        current = getattr(profile.data, patch.field_name)
        updated_field = current.model_copy(
            update={
                "state": patch.proposed_state,
                "value": patch.proposed_value,
                "provenance": FieldProvenance(
                    source="user",
                    recorded_at=ConversationService._now(),
                    source_ref="confirmed-conversation-proposal",
                ),
            }
        )
        updated_data = profile.data.model_copy(update={patch.field_name: updated_field})
        return profile.model_copy(
            update={
                "version": profile.version + 1,
                "as_of_date": date.today(),
                "data": updated_data,
            }
        )

    @staticmethod
    def _delta(
        old: RecommendationResult,
        new: RecommendationResult,
        patch: ProfilePatch,
    ) -> SummaryDelta:
        old_gaps = {gap.gap_type: gap.gap_amount for gap in old.gaps}
        new_gaps = {gap.gap_type: gap.gap_amount for gap in new.gaps}
        gap_changes = [
            GapDelta(
                gap_type=gap_type,
                old_amount=old_gaps[gap_type],
                new_amount=new_gaps[gap_type],
            )
            for gap_type in old_gaps.keys() & new_gaps.keys()
            if old_gaps[gap_type] != new_gaps[gap_type]
        ]
        old_top = ConversationService._top_plan(old)
        new_top = ConversationService._top_plan(new)
        return SummaryDelta(
            changed_inputs=[
                ValueDelta(
                    field_name=patch.field_name,
                    old_value=patch.old_value,
                    new_value=patch.proposed_value,
                )
            ],
            changed_gaps=gap_changes,
            old_top_plan_id=old_top,
            new_top_plan_id=new_top,
            ranking_changed=old_top != new_top,
            affected_regions=["comparison", "ranking_reason", "assumptions", "agent"],
        )

    @staticmethod
    def _top_plan(result: RecommendationResult) -> str | None:
        return next((item.plan_id for item in result.evaluations if item.rank == 1), None)

    @staticmethod
    def _plan_label(plan_id: str) -> str:
        return {
            "synthetic-lioncity-term-flex": "LionCity Term Flex",
            "synthetic-harbour-essential-ci": "Harbour Essential CI",
            "synthetic-orchid-income-shield": "Orchid Income Shield",
            "synthetic-meridian-whole-life-plus": "Meridian Whole Life Plus",
        }.get(plan_id, plan_id)

    def _get_record(self, conversation_id: str) -> ConversationRecord:
        record = self._records.get(conversation_id)
        if record is None:
            raise ConversationNotFoundError(conversation_id)
        return record

    @staticmethod
    def _get_proposal(record: ConversationRecord, proposal_id: str) -> ChangeProposal:
        proposal = record.proposals.get(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(proposal_id)
        return proposal

    @staticmethod
    def _require_revision(record: ConversationRecord, expected_revision_id: str) -> None:
        if expected_revision_id != record.active_revision_id:
            raise RevisionConflictError(record.active_revision_id)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _event(
        record: ConversationRecord,
        event_type: str,
        *,
        run_id: str | None = None,
        proposal_id: str | None = None,
        revision_id: str | None = None,
        safe_details: dict[str, str] | None = None,
    ) -> None:
        record.events.append(
            ReplayEvent(
                sequence=len(record.events) + 1,
                occurred_at=ConversationService._now(),
                event_type=event_type,
                run_id=run_id,
                proposal_id=proposal_id,
                revision_id=revision_id,
                safe_details=safe_details or {},
            )
        )

    @staticmethod
    def _unsupported_answer(
        record: ConversationRecord,
        request: ConversationMessageRequest,
        run_id: str,
        action_id: str,
        message_id: str,
        content: str,
        error_code: str,
    ) -> ConversationMessageResponse:
        return ConversationMessageResponse(
            conversation_id=record.conversation_id,
            client_message_id=request.client_message_id,
            run_id=run_id,
            state="unsupported",
            active_revision_id=record.active_revision_id,
            assistant_message=AssistantMessage(
                message_id=message_id,
                content=content,
                citations=[],
            ),
            actions=[
                ActionEvent(
                    action_id=action_id,
                    intent="ANSWER_QUESTION",
                    tool="ANSWER_QUESTION",
                    target="evidence:cached-catalogue",
                    status="blocked",
                    evidence_count=0,
                    confirmation_required=False,
                    affected_regions=["agent"],
                    error_code=error_code,
                )
            ],
        )