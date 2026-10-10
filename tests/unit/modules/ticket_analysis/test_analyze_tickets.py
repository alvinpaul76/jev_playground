import pytest

from jev_playground.modules.ticket_analysis.application.dto import AnalyzeTicketsInput
from jev_playground.modules.ticket_analysis.application.ports import (
    RawBatchClassification,
)
from jev_playground.modules.ticket_analysis.application.use_cases.analyze_tickets import (
    AnalyzeTickets,
)
from jev_playground.modules.ticket_analysis.domain.entities import (
    Ticket,
    TicketAnalysis,
)
from jev_playground.modules.ticket_analysis.domain.errors import (
    ClassifierUnavailable,
    InvalidBatch,
)
from jev_playground.modules.ticket_analysis.domain.value_objects import (
    Category,
    Probability,
    Severity,
)


class FakeClassifier:
    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def classify_many(self, tickets):
        self.calls += 1
        if self.error:
            raise self.error
        return RawBatchClassification(
            analyses=tuple(
                TicketAnalysis(
                    ticket_id=t.id,
                    severity=Severity.HIGH,
                    severity_confidence=Probability(0.8),
                    category=Category.SECURITY,
                    category_confidence=Probability(0.7),
                )
                for t in tickets
            ),
            model="fake",
            latency_ms=1.0,
        )


def tickets(*ids):
    return tuple(Ticket(id=i, title="t", description="d") for i in ids)


def test_returns_one_analysis_per_ticket_in_order():
    result = AnalyzeTickets(FakeClassifier()).execute(
        AnalyzeTicketsInput(tickets("B", "A", "C"))
    )
    assert [a.ticket_id for a in result.analyses] == ["B", "A", "C"]
    assert result.model == "fake"


def test_invalid_batch_never_reaches_classifier():
    fake = FakeClassifier()
    with pytest.raises(InvalidBatch):
        AnalyzeTickets(fake).execute(AnalyzeTicketsInput(tickets("A", "A")))
    assert fake.calls == 0


def test_classifier_error_propagates():
    with pytest.raises(ClassifierUnavailable):
        AnalyzeTickets(FakeClassifier(error=ClassifierUnavailable())).execute(
            AnalyzeTicketsInput(tickets("A"))
        )
