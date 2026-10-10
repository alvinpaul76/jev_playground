from dataclasses import dataclass

from jev_playground.modules.ticket_analysis.domain.errors import InvalidTicket
from jev_playground.modules.ticket_analysis.domain.value_objects import (
    Category,
    Probability,
    Severity,
)

MAX_ID_LENGTH = 64
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 10_000
MAX_ENVIRONMENT_LENGTH = 100
MAX_BUSINESS_IMPACT_LENGTH = 2_000
MAX_EVIDENCE_ITEMS = 20
MAX_EVIDENCE_LENGTH = 1_000


def _require(name: str, value: str, max_length: int) -> None:
    if not value.strip():
        raise InvalidTicket(f"Ticket {name} must not be empty.")
    if len(value) > max_length:
        raise InvalidTicket(f"Ticket {name} must be at most {max_length} characters.")


@dataclass(frozen=True, slots=True)
class Ticket:
    id: str
    title: str
    description: str
    environment: str | None = None
    business_impact: str | None = None
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require("id", self.id, MAX_ID_LENGTH)
        _require("title", self.title, MAX_TITLE_LENGTH)
        _require("description", self.description, MAX_DESCRIPTION_LENGTH)
        if self.environment is not None:
            _require("environment", self.environment, MAX_ENVIRONMENT_LENGTH)
        if self.business_impact is not None:
            _require(
                "business_impact", self.business_impact, MAX_BUSINESS_IMPACT_LENGTH
            )
        if len(self.evidence) > MAX_EVIDENCE_ITEMS:
            raise InvalidTicket(
                f"Ticket evidence must have at most {MAX_EVIDENCE_ITEMS} items."
            )
        for item in self.evidence:
            _require("evidence item", item, MAX_EVIDENCE_LENGTH)


@dataclass(frozen=True, slots=True)
class TicketAnalysis:
    ticket_id: str
    severity: Severity
    severity_confidence: Probability
    category: Category
    category_confidence: Probability
