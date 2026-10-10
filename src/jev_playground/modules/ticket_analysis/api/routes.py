from fastapi import APIRouter

from jev_playground.api.problem import problem_response
from jev_playground.modules.ticket_analysis.api.dependencies import AnalyzeTicketsDep
from jev_playground.modules.ticket_analysis.api.schemas import (
    AnalyzeTicketsRequest,
    AnalyzeTicketsResponse,
)
from jev_playground.modules.ticket_analysis.application.dto import AnalyzeTicketsInput

router = APIRouter(prefix="/ticket-analyses", tags=["ticket-analyses"])


@router.post(
    "",
    responses={
        422: problem_response("Invalid batch, ticket, or request body."),
        503: problem_response("The classifier is unavailable."),
    },
)
def analyze_tickets(
    body: AnalyzeTicketsRequest, use_case: AnalyzeTicketsDep
) -> AnalyzeTicketsResponse:
    tickets = tuple(t.to_domain() for t in body.tickets)
    result = use_case.execute(AnalyzeTicketsInput(tickets=tickets))
    return AnalyzeTicketsResponse.from_result(result)
