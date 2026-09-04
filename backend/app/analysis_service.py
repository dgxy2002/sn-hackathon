from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from threading import RLock
from uuid import uuid4

from .contracts_v2 import AnalysisSession, AnalysisStage, CreateAnalysisRequest


class AnalysisNotFoundError(LookupError):
    pass


class AnalysisSessionService:
    def __init__(
        self,
        *,
        ttl: timedelta = timedelta(hours=24),
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if ttl <= timedelta(0):
            raise ValueError("ttl must be positive")
        self._ttl = ttl
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sessions: dict[str, AnalysisSession] = {}
        self._lock = RLock()

    def create(self, request: CreateAnalysisRequest) -> AnalysisSession:
        now = self._clock()
        session = AnalysisSession(
            analysis_id=str(uuid4()),
            purpose=request.purpose,
            decision_date=request.decision_date,
            model_consent=request.model_consent,
            created_at=now,
            expires_at=now + self._ttl,
        )
        with self._lock:
            self._sessions[session.analysis_id] = session
        return session

    def get(self, analysis_id: str) -> AnalysisSession:
        with self._lock:
            session = self._sessions.get(analysis_id)
            if session is None:
                raise AnalysisNotFoundError(analysis_id)
            if session.expires_at <= self._clock():
                del self._sessions[analysis_id]
                raise AnalysisNotFoundError(analysis_id)
            return session


    def set_stage(
        self,
        analysis_id: str,
        stage: AnalysisStage,
    ) -> AnalysisSession:
        with self._lock:
            session = self.get(analysis_id)
            updated = session.model_copy(update={"stage": stage})
            self._sessions[analysis_id] = updated
            return updated

    def delete(self, analysis_id: str) -> None:
        with self._lock:
            if self._sessions.pop(analysis_id, None) is None:
                raise AnalysisNotFoundError(analysis_id)