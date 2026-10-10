from jev_playground.modules.ticket_analysis.application.dto import (
    AnalyzeTicketsInput,
    AnalyzeTicketsResult,
)
from jev_playground.modules.ticket_analysis.application.ports import TicketClassifier
from jev_playground.modules.ticket_analysis.domain.policies import ensure_valid_batch


class AnalyzeTickets:
    def __init__(self, classifier: TicketClassifier) -> None:
        self._classifier = classifier

    def execute(self, data: AnalyzeTicketsInput) -> AnalyzeTicketsResult:
        ensure_valid_batch(data.tickets)
        raw = self._classifier.classify_many(data.tickets)
        return AnalyzeTicketsResult(
            analyses=raw.analyses, model=raw.model, latency_ms=raw.latency_ms
        )
