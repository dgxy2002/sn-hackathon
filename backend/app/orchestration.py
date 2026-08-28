from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic
from uuid import uuid4

from .config import CapabilityMode
from .contracts import (
    InvocationRequest,
    InvocationResponse,
    RunEvent,
    RunMetrics,
)
from .decision_support import DecisionService, InMemoryProfileRepository
from .extraction import FixtureExtractionService


class RunNotFoundError(LookupError):
    pass


class CoordinatorService:
    MAX_TOOL_CALLS = 3

    def __init__(
        self,
        profiles: InMemoryProfileRepository,
        extraction: FixtureExtractionService,
        decisions: DecisionService,
        mode: CapabilityMode = "simulated",
    ) -> None:
        self.mode = mode
        self._profiles = profiles
        self._extraction = extraction
        self._decisions = decisions
        self._runs: dict[str, InvocationResponse] = {}

    def invoke(self, request: InvocationRequest) -> InvocationResponse:
        started = monotonic()
        started_at = self._now()
        run_id = f"run-{uuid4()}"
        events: list[RunEvent] = []
        self._append(events, run_id, "validating", "profile", "started")
        self._profiles.save(request.profile)
        self._append(events, run_id, "validating", "profile", "completed")

        extraction = None
        policy_field = request.profile.data.has_current_policy
        if policy_field.state == "present" and policy_field.value is True:
            if request.extraction_id:
                extraction = self._extraction.get(request.extraction_id)
            elif request.fixture_id:
                self._append(events, run_id, "extracting", "extraction", "started")
                extraction = self._extraction.submit(request.fixture_id)
                self._append(events, run_id, "extracting", "extraction", "completed")
            if extraction is None or extraction.review_required:
                self._append(
                    events,
                    run_id,
                    "waiting_for_extraction_review",
                    "extraction",
                    "skipped",
                )
                return self._finish(
                    request,
                    run_id,
                    started,
                    started_at,
                    events,
                    "waiting_for_extraction_review",
                    extraction=extraction,
                    terminal_status="blocked",
                )
        else:
            self._append(
                events,
                run_id,
                "extracting",
                "extraction",
                "skipped",
                {"reason": "no_policy_or_unknown_policy_status"},
            )

        self._append(events, run_id, "deciding", "recommendation", "started")
        recommendation = self._decisions.evaluate(request.profile)
        self._append(events, run_id, "deciding", "recommendation", "completed")
        if recommendation.status == "insufficient_data":
            state = "insufficient_data"
            terminal_status = "blocked"
        elif recommendation.status == "no_eligible_plan":
            state = "no_eligible_plan"
            terminal_status = "completed"
        else:
            state = "completed"
            terminal_status = "completed"
        self._append(events, run_id, state if state != "no_eligible_plan" else "completed", "coordinator", "completed")
        return self._finish(
            request,
            run_id,
            started,
            started_at,
            events,
            state,
            extraction=extraction,
            recommendation=recommendation,
            terminal_status=terminal_status,
        )

    def get(self, run_id: str) -> InvocationResponse:
        try:
            return self._runs[run_id]
        except KeyError as error:
            raise RunNotFoundError(run_id) from error

    def _finish(
        self,
        request: InvocationRequest,
        run_id: str,
        started: float,
        started_at: datetime,
        events: list[RunEvent],
        state: str,
        *,
        extraction=None,
        recommendation=None,
        terminal_status: str,
    ) -> InvocationResponse:
        response = InvocationResponse(
            invocation_id=request.invocation_id,
            run_id=run_id,
            mode=self.mode,
            state=state,
            profile=request.profile,
            extraction=extraction,
            recommendation=recommendation,
            events=events,
            metrics=RunMetrics(
                run_id=run_id,
                started_at=started_at,
                completed_at=self._now(),
                duration_ms=max(0, round((monotonic() - started) * 1000)),
                tool_calls=sum(event.outcome == "started" for event in events),
                retries=0,
                terminal_status=terminal_status,
            ),
        )
        self._runs[run_id] = response
        return response

    @staticmethod
    def _append(
        events: list[RunEvent],
        run_id: str,
        state: str,
        capability: str,
        outcome: str,
        details: dict[str, str] | None = None,
    ) -> None:
        if sum(event.outcome == "started" for event in events) >= CoordinatorService.MAX_TOOL_CALLS and outcome == "started":
            raise RuntimeError("LOOP_LIMIT_REACHED")
        events.append(
            RunEvent(
                run_id=run_id,
                sequence=len(events) + 1,
                occurred_at=CoordinatorService._now(),
                state=state,
                capability=capability,
                outcome=outcome,
                safe_details=details or {},
            )
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)