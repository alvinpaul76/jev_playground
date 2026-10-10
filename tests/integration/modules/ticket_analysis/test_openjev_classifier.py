import pytest
from openjev.backends import get_backend

from jev_playground.modules.ticket_analysis.domain.entities import Ticket
from jev_playground.modules.ticket_analysis.domain.errors import ClassifierUnavailable
from jev_playground.modules.ticket_analysis.domain.value_objects import (
    Category,
    Severity,
)
from jev_playground.modules.ticket_analysis.infrastructure.openjev_classifier import (
    OpenJevTicketClassifier,
)


def ticket(id="T-1", **kw):
    return Ticket(id=id, title="Stripe is down", description="Payments fail", **kw)


def test_maps_mock_backend_response_to_domain_in_input_order():
    raw = OpenJevTicketClassifier(get_backend("mock")).classify_many(
        [ticket("B"), ticket("A")]
    )
    assert [a.ticket_id for a in raw.analyses] == ["B", "A"]
    for a in raw.analyses:
        assert a.severity in set(Severity)
        assert a.category in set(Category)
        assert 0 <= a.severity_confidence.value <= 1
    assert raw.model == "openjev-mock"
    assert raw.latency_ms is not None


def test_is_deterministic_with_mock():
    c = OpenJevTicketClassifier(get_backend("mock"))
    assert c.classify_many([ticket()]).analyses == c.classify_many([ticket()]).analyses


def test_one_decision_per_ticket_without_labels_in_state():
    seen = []

    class Spy:
        def decide(self, request):
            seen.append(request)
            return get_backend("mock").decide(request)

    OpenJevTicketClassifier(Spy()).classify_many(
        [ticket("A", environment="production", evidence=("e1",)), ticket("B")]
    )
    assert len(seen) == 2
    assert seen[0].state == {
        "id": "A",
        "title": "Stripe is down",
        "description": "Payments fail",
        "environment": "production",
        "evidence": ["e1"],
    }
    assert set(seen[1].state) == {"id", "title", "description"}
    assert set(seen[0].questions) == {"severity", "category"}


def test_vendor_errors_become_classifier_unavailable():
    class Broken:
        def decide(self, request):
            raise RuntimeError("cuda oom")

    with pytest.raises(ClassifierUnavailable):
        OpenJevTicketClassifier(Broken()).classify_many([ticket()])
