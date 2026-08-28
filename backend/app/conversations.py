from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from uuid import uuid4

from .contracts import (
    ActionEvent,
    AssistantMessage,
    Citation,
    ConversationMessageRequest,
    ConversationMessageResponse,
    ConversationResponse,
    SuggestedPrompt,
)


class ConversationNotFoundError(LookupError):
    pass


class RevisionConflictError(ValueError):
    pass


@dataclass
class ConversationRecord:
    conversation_id: str
    active_revision_id: str
    responses: dict[str, ConversationMessageResponse] = field(default_factory=dict)


class ConversationService:
    def __init__(self) -> None:
        self._records: dict[str, ConversationRecord] = {}
        self._lock = Lock()

    def create(self, active_revision_id: str) -> ConversationResponse:
        conversation_id = f"conv-{uuid4()}"
        record = ConversationRecord(
            conversation_id=conversation_id,
            active_revision_id=active_revision_id,
        )
        with self._lock:
            self._records[conversation_id] = record

        return ConversationResponse(
            conversation_id=conversation_id,
            active_revision_id=active_revision_id,
            suggested_prompts=[
                SuggestedPrompt(
                    id="why-ranked-first",
                    label="Why this ranks first",
                    message="Why does LionCity Term Flex rank first?",
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
            ],
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
            return response

    def _resolve(
        self, record: ConversationRecord, request: ConversationMessageRequest
    ) -> ConversationMessageResponse:
        text = " ".join(request.message.casefold().split())
        run_id = f"run-{uuid4()}"
        action_id = f"action-{uuid4()}"
        message_id = f"message-{uuid4()}"

        if "critical illness" in text or "critical-illness" in text:
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
                        "The comparison still lacks your full work cover, existing illness "
                        "add-on terms, and insurer underwriting outcome. I opened that section."
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

        if "budget" in text or "dependant" in text or "goal" in text:
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

        if "why" in text or "rank" in text or "lioncity" in text:
            return ConversationMessageResponse(
                conversation_id=record.conversation_id,
                client_message_id=request.client_message_id,
                run_id=run_id,
                state="completed",
                active_revision_id=record.active_revision_id,
                assistant_message=AssistantMessage(
                    message_id=message_id,
                    content=(
                        "LionCity Term Flex ranks first in this synthetic result because it "
                        "addresses the largest known gap, stays inside the stated monthly "
                        "budget, and matches the protection-only preference. It does not fill "
                        "the whole illustrative gap."
                    ),
                    citations=[
                        Citation(
                            evidence_id="SYN-LTF-01",
                            label="LionCity Term Flex synthetic fixture",
                            synthetic=True,
                        ),
                        Citation(
                            evidence_id="MONEYSENSE-LIFE-INSURANCE",
                            label="MoneySense life insurance guidance",
                            url="https://www.moneysense.gov.sg/life-insurance/",
                            synthetic=False,
                        ),
                    ],
                ),
                actions=[
                    ActionEvent(
                        action_id=action_id,
                        intent="FOCUS_SECTION",
                        tool="FOCUS_SECTION",
                        target="reasoning:ranking",
                        status="completed",
                        evidence_count=2,
                        confirmation_required=False,
                        affected_regions=["ranking_reason", "agent"],
                    )
                ],
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
                    "I can currently explain the synthetic ranking, focus its assumptions, "
                    "or filter to the critical-illness option. Your summary is unchanged."
                ),
                citations=[],
            ),
            actions=[
                ActionEvent(
                    action_id=action_id,
                    intent="ANSWER_QUESTION",
                    tool="ANSWER_QUESTION",
                    target="summary:current",
                    status="blocked",
                    evidence_count=0,
                    confirmation_required=False,
                    affected_regions=["agent"],
                    error_code="ACTION_NOT_ALLOWED",
                )
            ],
        )