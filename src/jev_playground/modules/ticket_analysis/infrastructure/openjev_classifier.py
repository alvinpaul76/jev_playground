import threading
import time
from collections.abc import Sequence
from typing import Any

from openjev import Choice, SystemOneRequest

from jev_playground.modules.ticket_analysis.application.ports import (
    RawBatchClassification,
)
from jev_playground.modules.ticket_analysis.domain.entities import (
    Ticket,
    TicketAnalysis,
)
from jev_playground.modules.ticket_analysis.domain.errors import ClassifierUnavailable
from jev_playground.modules.ticket_analysis.domain.value_objects import (
    Category,
    Probability,
    Severity,
)
from jev_playground.modules.ticket_analysis.infrastructure.backend import Decider

_QUESTIONS = {
    "severity": Choice(
        instructions="What is the severity of this ticket?",
        criteria={
            Severity.CRITICAL.value: "Widespread outage or data exposure affecting many users",
            Severity.HIGH.value: "Serious defect or risk with a significant business impact",
            Severity.MEDIUM.value: "Real defect with limited impact or a workaround",
            Severity.LOW.value: "Cosmetic, minor, or expected behavior with no real impact",
            Severity.UNKNOWN.value: "Too little information to judge the severity",
        },
    ),
    "category": Choice(
        instructions="Which category best describes this ticket?",
        criteria={
            Category.INCIDENT.value: "Service outage or errors affecting a running system",
            Category.SECURITY.value: "Vulnerability, unauthorized access, or data exposure",
            Category.UI.value: "Visual or layout problem in the interface",
            Category.PERFORMANCE.value: "Slowness, freezing, or resource problems",
            Category.FINANCIAL_INTEGRITY.value: "Payments, charges, or money records are wrong",
            Category.FEATURE_REQUEST.value: "A request for new functionality",
            Category.REGRESSION.value: "Something that worked in an earlier version now fails",
            Category.AUTHENTICATION.value: "Login, session, or credential behavior",
        },
    ),
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _state(ticket: Ticket) -> dict[str, Any]:
    state: dict[str, Any] = {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
    }
    if ticket.environment is not None:
        state["environment"] = ticket.environment
    if ticket.business_impact is not None:
        state["business_impact"] = ticket.business_impact
    if ticket.evidence:
        state["evidence"] = list(ticket.evidence)
    return state


class OpenJevTicketClassifier:
    def __init__(self, backend: Decider) -> None:
        self._backend = backend
        # HF inference is not guaranteed thread-safe; FastAPI runs sync routes in a thread pool.
        # The lock is per ticket, so concurrent requests interleave instead of queueing whole batches.
        self._lock = threading.Lock()

    def classify_many(self, tickets: Sequence[Ticket]) -> RawBatchClassification:
        started = time.perf_counter()
        analyses: list[TicketAnalysis] = []
        model = ""
        try:
            for ticket in tickets:
                request = SystemOneRequest(state=_state(ticket), questions=_QUESTIONS)
                with self._lock:
                    response = self._backend.decide(request)
                severity = response.answers["severity"]
                category = response.answers["category"]
                model = response.model
                analyses.append(
                    TicketAnalysis(
                        ticket_id=ticket.id,
                        severity=Severity(severity.choice),
                        severity_confidence=Probability(
                            _clamp(severity.confidence, 0.0, 1.0)
                        ),
                        category=Category(category.choice),
                        category_confidence=Probability(
                            _clamp(category.confidence, 0.0, 1.0)
                        ),
                    )
                )
        except Exception as exc:
            raise ClassifierUnavailable() from exc
        return RawBatchClassification(
            analyses=tuple(analyses),
            model=model,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )
