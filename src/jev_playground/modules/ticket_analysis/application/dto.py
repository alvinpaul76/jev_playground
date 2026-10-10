from dataclasses import dataclass

from jev_playground.modules.ticket_analysis.domain.entities import (
    Ticket,
    TicketAnalysis,
)


@dataclass(frozen=True, slots=True)
class AnalyzeTicketsInput:
    tickets: tuple[Ticket, ...]


@dataclass(frozen=True, slots=True)
class AnalyzeTicketsResult:
    analyses: tuple[TicketAnalysis, ...]
    model: str
    latency_ms: float | None
