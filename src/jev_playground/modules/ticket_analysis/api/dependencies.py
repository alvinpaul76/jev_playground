from typing import Annotated

from fastapi import Depends, Request

from jev_playground.modules.ticket_analysis.application.ports import TicketClassifier
from jev_playground.modules.ticket_analysis.application.use_cases.analyze_tickets import (
    AnalyzeTickets,
)
from jev_playground.modules.ticket_analysis.domain.errors import ClassifierUnavailable
from jev_playground.modules.ticket_analysis.infrastructure.openjev_classifier import (
    OpenJevTicketClassifier,
)


def get_classifier(request: Request) -> TicketClassifier:
    backend = getattr(request.app.state, "backend", None)
    if backend is None:
        raise ClassifierUnavailable("The model is not loaded yet.")
    classifier = getattr(request.app.state, "classifier", None)
    if classifier is None:
        classifier = OpenJevTicketClassifier(backend)
        request.app.state.classifier = classifier
    return classifier


ClassifierDep = Annotated[TicketClassifier, Depends(get_classifier)]


def get_analyze_tickets_use_case(classifier: ClassifierDep) -> AnalyzeTickets:
    return AnalyzeTickets(classifier)


AnalyzeTicketsDep = Annotated[AnalyzeTickets, Depends(get_analyze_tickets_use_case)]
