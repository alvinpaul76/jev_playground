import pytest

from jev_playground.modules.ticket_analysis.domain.entities import (
    MAX_EVIDENCE_ITEMS,
    Ticket,
)
from jev_playground.modules.ticket_analysis.domain.errors import (
    InvalidBatch,
    InvalidTicket,
)
from jev_playground.modules.ticket_analysis.domain.policies import (
    MAX_BATCH_SIZE,
    ensure_valid_batch,
)
from jev_playground.modules.ticket_analysis.domain.value_objects import Probability


def ticket(id="T-1", **kw):
    return Ticket(id=id, title="Title", description="Something broke", **kw)


def test_minimal_ticket_is_valid():
    assert ticket().evidence == ()


@pytest.mark.parametrize("field", ["id", "title", "description"])
def test_required_text_must_not_be_blank(field):
    values = {"id": "T-1", "title": "t", "description": "d", field: "   "}
    with pytest.raises(InvalidTicket):
        Ticket(**values)


def test_blank_optional_field_is_rejected():
    with pytest.raises(InvalidTicket):
        ticket(environment=" ")


def test_oversized_description_is_rejected():
    with pytest.raises(InvalidTicket):
        Ticket(id="T", title="t", description="x" * 10_001)


def test_too_much_evidence_is_rejected():
    with pytest.raises(InvalidTicket):
        ticket(evidence=("e",) * (MAX_EVIDENCE_ITEMS + 1))


def test_valid_batch_passes():
    ensure_valid_batch([ticket("A"), ticket("B")])


def test_empty_batch_is_rejected():
    with pytest.raises(InvalidBatch):
        ensure_valid_batch([])


def test_oversized_batch_is_rejected():
    with pytest.raises(InvalidBatch):
        ensure_valid_batch([ticket(str(i)) for i in range(MAX_BATCH_SIZE + 1)])


def test_duplicate_ids_are_rejected_and_named():
    with pytest.raises(InvalidBatch, match="A"):
        ensure_valid_batch([ticket("A"), ticket("B"), ticket("A")])


def test_probability_bounds():
    Probability(0.0)
    Probability(1.0)
    with pytest.raises(ValueError):
        Probability(1.1)
