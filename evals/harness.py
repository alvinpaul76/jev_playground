"""Measures the production classifier against tickets whose expected labels a person decided.

Runs the same use case the API runs (`AnalyzeTickets`), so what it scores is what clients get.
"""

import json
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from jev_playground.modules.ticket_analysis.application.dto import AnalyzeTicketsInput
from jev_playground.modules.ticket_analysis.application.ports import TicketClassifier
from jev_playground.modules.ticket_analysis.application.use_cases.analyze_tickets import (
    AnalyzeTickets,
)
from jev_playground.modules.ticket_analysis.domain.entities import (
    Ticket,
    TicketAnalysis,
)
from jev_playground.modules.ticket_analysis.domain.errors import DomainError
from jev_playground.modules.ticket_analysis.domain.policies import MAX_BATCH_SIZE
from jev_playground.modules.ticket_analysis.domain.value_objects import (
    Category,
    Severity,
    Team,
)

QUESTIONS = ("severity", "category", "assigned_team")


class Split(StrEnum):
    """Which part of the labeled set a ticket belongs to (see GLOSSARY.md)."""

    SMOKE = "smoke"
    TUNING = "tuning"
    HELDOUT = "heldout"


class DatasetError(Exception):
    """The labeled set on disk is not valid. The message names the file and line."""


@dataclass(frozen=True, slots=True)
class Expected:
    severity: Severity
    category: Category
    assigned_team: Team

    def label(self, question: str) -> str:
        return str(getattr(self, question).value)


@dataclass(frozen=True, slots=True)
class LabeledTicket:
    ticket: Ticket
    expected: Expected
    split: Split
    ambiguous: bool = False
    note: str = ""


@dataclass(frozen=True, slots=True)
class Miss:
    ticket_id: str
    question: str
    expected: str
    predicted: str
    confidence: float


@dataclass(slots=True)
class QuestionScore:
    correct: int = 0
    total: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


@dataclass(frozen=True, slots=True)
class SplitReport:
    split: Split
    n_tickets: int
    n_ambiguous: int
    scores: dict[str, QuestionScore]
    misses: tuple[Miss, ...]


@dataclass(frozen=True, slots=True)
class EvalResult:
    splits: tuple[SplitReport, ...]
    model: str
    latency_ms: float

    def to_dict(self, show_heldout_misses: bool = False) -> dict[str, Any]:
        def hidden_for(s: SplitReport) -> bool:
            return s.split is Split.HELDOUT and not show_heldout_misses

        return {
            "model": self.model,
            "latency_ms": self.latency_ms,
            "splits": [
                {
                    "split": s.split.value,
                    "n_tickets": s.n_tickets,
                    "n_ambiguous": s.n_ambiguous,
                    "scores": {
                        q: {
                            "correct": v.correct,
                            "total": v.total,
                            "accuracy": v.accuracy,
                        }
                        for q, v in s.scores.items()
                    },
                    "misses_hidden": hidden_for(s),
                    "misses": [] if hidden_for(s) else [asdict(m) for m in s.misses],
                }
                for s in self.splits
            ],
        }


# --- loading ----------------------------------------------------------------


def _enum[E: StrEnum](kind: type[E], value: Any, where: str, what: str) -> E:
    try:
        return kind(value)
    except ValueError:
        allowed = ", ".join(m.value for m in kind)
        raise DatasetError(
            f"{where}: {what} '{value}' is not one of: {allowed}"
        ) from None


def _parse(row: Any, where: str) -> LabeledTicket:
    if not isinstance(row, dict):
        raise DatasetError(f"{where}: each line must be a JSON object")
    expected_row = row.get("expected")
    if not isinstance(expected_row, dict):
        raise DatasetError(f"{where}: missing 'expected' labels")
    for question in QUESTIONS:
        if question not in expected_row:
            raise DatasetError(f"{where}: expected is missing '{question}'")
    expected = Expected(
        severity=_enum(Severity, expected_row["severity"], where, "severity"),
        category=_enum(Category, expected_row["category"], where, "category"),
        assigned_team=_enum(
            Team, expected_row["assigned_team"], where, "assigned_team"
        ),
    )
    split = _enum(Split, row.get("split"), where, "split")
    try:
        ticket = Ticket(
            id=row.get("id", ""),
            title=row.get("title", ""),
            description=row.get("description", ""),
            environment=row.get("environment"),
            business_impact=row.get("business_impact"),
            evidence=tuple(row.get("evidence", ())),
        )
    except DomainError as exc:
        raise DatasetError(f"{where}: {exc.public_message}") from exc
    return LabeledTicket(
        ticket=ticket,
        expected=expected,
        split=split,
        ambiguous=bool(row.get("ambiguous", False)),
        note=str(row.get("note", "")),
    )


def load_labeled_set(paths: Iterable[Path]) -> list[LabeledTicket]:
    items: list[LabeledTicket] = []
    seen: dict[str, str] = {}
    for path in paths:
        for number, raw in enumerate(path.read_text().splitlines(), start=1):
            if not raw.strip():
                continue
            where = f"{path.name}:{number}"
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise DatasetError(f"{where}: invalid JSON ({exc.msg})") from exc
            item = _parse(row, where)
            if item.ticket.id in seen:
                raise DatasetError(
                    f"{where}: duplicate ticket id '{item.ticket.id}' (first seen at {seen[item.ticket.id]})"
                )
            seen[item.ticket.id] = where
            items.append(item)
    return items


# --- scoring ----------------------------------------------------------------

_ORDER = (Split.SMOKE, Split.TUNING, Split.HELDOUT)


def _predict(
    classifier: TicketClassifier, tickets: Sequence[Ticket]
) -> tuple[dict[str, TicketAnalysis], str, float]:
    use_case = AnalyzeTickets(classifier)
    predictions: dict[str, TicketAnalysis] = {}
    model, latency = "", 0.0
    for start in range(0, len(tickets), MAX_BATCH_SIZE):
        chunk = tuple(tickets[start : start + MAX_BATCH_SIZE])
        result = use_case.execute(AnalyzeTicketsInput(tickets=chunk))
        model = result.model
        latency += result.latency_ms or 0.0
        predictions.update({a.ticket_id: a for a in result.analyses})
    return predictions, model, latency


def _confidence(analysis: TicketAnalysis, question: str) -> float:
    return float(getattr(analysis, f"{question}_confidence").value)


def evaluate(
    labeled: Sequence[LabeledTicket], classifier: TicketClassifier
) -> EvalResult:
    predictions, model, latency = _predict(classifier, [i.ticket for i in labeled])
    by_split: dict[Split, list[LabeledTicket]] = defaultdict(list)
    for item in labeled:
        by_split[item.split].append(item)

    reports: list[SplitReport] = []
    for split in _ORDER:
        items = by_split.get(split)
        if not items:
            continue
        scores = {q: QuestionScore() for q in QUESTIONS}
        misses: list[Miss] = []
        for item in items:
            if item.ambiguous:
                continue
            analysis = predictions[item.ticket.id]
            for question in QUESTIONS:
                predicted = str(getattr(analysis, question).value)
                expected = item.expected.label(question)
                scores[question].total += 1
                if predicted == expected:
                    scores[question].correct += 1
                else:
                    misses.append(
                        Miss(
                            item.ticket.id,
                            question,
                            expected,
                            predicted,
                            _confidence(analysis, question),
                        )
                    )
        reports.append(
            SplitReport(
                split=split,
                n_tickets=len(items),
                n_ambiguous=sum(i.ambiguous for i in items),
                scores=scores,
                misses=tuple(misses),
            )
        )
    return EvalResult(splits=tuple(reports), model=model, latency_ms=round(latency, 2))


# --- report -----------------------------------------------------------------

_HELDOUT_NOTICE = (
    "Held-out set: report these numbers only. Do not tune descriptions on them.\n"
    "Its misses are hidden; pass --show-heldout-misses to see them."
)


def format_report(result: EvalResult, show_heldout_misses: bool = False) -> str:
    lines = [f"model: {result.model}   classification time: {result.latency_ms} ms", ""]
    for s in result.splits:
        excluded = f", {s.n_ambiguous} ambiguous excluded" if s.n_ambiguous else ""
        lines.append(f"== {s.split.value} ({s.n_tickets} tickets{excluded})")
        for question in QUESTIONS:
            score = s.scores[question]
            lines.append(
                f"   {question:<14} {score.correct}/{score.total}  {score.accuracy:.0%}"
            )
        if s.split is Split.HELDOUT and not show_heldout_misses:
            lines.append("   " + _HELDOUT_NOTICE.replace("\n", "\n   "))
        elif s.misses:
            lines.append("   misses:")
            for m in s.misses:
                lines.append(
                    f"     {m.ticket_id} {m.question}: expected={m.expected} "
                    f"predicted={m.predicted} (confidence {m.confidence:.2f})"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
