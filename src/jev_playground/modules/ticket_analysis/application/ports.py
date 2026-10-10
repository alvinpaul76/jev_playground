from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from jev_playground.modules.ticket_analysis.domain.entities import (
    Ticket,
    TicketAnalysis,
)


@dataclass(frozen=True, slots=True)
class RawBatchClassification:
    analyses: tuple[TicketAnalysis, ...]  # same order as the input tickets
    model: str
    latency_ms: float | None


class TicketClassifier(Protocol):
    def classify_many(self, tickets: Sequence[Ticket]) -> RawBatchClassification:
        """Raises ClassifierUnavailable when the backend cannot classify the batch."""
        ...
