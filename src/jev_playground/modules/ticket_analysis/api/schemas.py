from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from jev_playground.modules.ticket_analysis.application.dto import (
    AnalyzeTicketsResult,
)
from jev_playground.modules.ticket_analysis.domain import entities as limits
from jev_playground.modules.ticket_analysis.domain.entities import Ticket
from jev_playground.modules.ticket_analysis.domain.policies import MAX_BATCH_SIZE


class TicketIn(BaseModel):
    # severity/category are outputs; sending them is rejected so they cannot leak into the prompt.
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=limits.MAX_ID_LENGTH)
    title: str = Field(min_length=1, max_length=limits.MAX_TITLE_LENGTH)
    description: str = Field(min_length=1, max_length=limits.MAX_DESCRIPTION_LENGTH)
    environment: str | None = Field(
        default=None, max_length=limits.MAX_ENVIRONMENT_LENGTH
    )
    business_impact: str | None = Field(
        default=None, max_length=limits.MAX_BUSINESS_IMPACT_LENGTH
    )
    evidence: list[Annotated[str, Field(max_length=limits.MAX_EVIDENCE_LENGTH)]] = (
        Field(default_factory=list, max_length=limits.MAX_EVIDENCE_ITEMS)
    )

    def to_domain(self) -> Ticket:
        return Ticket(
            id=self.id,
            title=self.title,
            description=self.description,
            environment=self.environment,
            business_impact=self.business_impact,
            evidence=tuple(self.evidence),
        )


class AnalyzeTicketsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tickets: list[TicketIn] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


class LabelOut(BaseModel):
    label: str
    confidence: float


class TicketAnalysisOut(BaseModel):
    id: str
    severity: LabelOut
    category: LabelOut


class AnalyzeTicketsResponse(BaseModel):
    results: list[TicketAnalysisOut]
    model: str
    latency_ms: float | None

    @classmethod
    def from_result(cls, result: AnalyzeTicketsResult) -> AnalyzeTicketsResponse:
        return cls(
            results=[
                TicketAnalysisOut(
                    id=a.ticket_id,
                    severity=LabelOut(
                        label=a.severity.value, confidence=a.severity_confidence.value
                    ),
                    category=LabelOut(
                        label=a.category.value, confidence=a.category_confidence.value
                    ),
                )
                for a in result.analyses
            ],
            model=result.model,
            latency_ms=result.latency_ms,
        )
