from fastapi import APIRouter

from jev_playground.modules.ticket_analysis.api.dependencies import AnalyzeTicketsDep
from jev_playground.modules.ticket_analysis.api.schemas import (
    AnalyzeTicketsRequest,
    AnalyzeTicketsResponse,
)
from jev_playground.modules.ticket_analysis.application.dto import AnalyzeTicketsInput
from jev_playground.modules.ticket_analysis.domain.entities import Ticket

router = APIRouter(prefix="/ticket-analyses", tags=["ticket-analyses"])


@router.post("")
def analyze_tickets(
    body: AnalyzeTicketsRequest, use_case: AnalyzeTicketsDep
) -> AnalyzeTicketsResponse:
    tickets = tuple(
        Ticket(
            id=t.id,
            title=t.title,
            description=t.description,
            environment=t.environment,
            business_impact=t.business_impact,
            evidence=tuple(t.evidence),
        )
        for t in body.tickets
    )
    result = use_case.execute(AnalyzeTicketsInput(tickets=tickets))
    return AnalyzeTicketsResponse.from_result(result)
