"""Measures the production classifier against tickets whose expected labels a person decided.

Runs the same use case the API runs (`AnalyzeTickets`), so what it scores is what clients get.
"""

import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
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


MISSING = "missing"
LABELS: dict[str, type[StrEnum]] = {
    "severity": Severity,
    "category": Category,
    "assigned_team": Team,
}


@dataclass(frozen=True, slots=True)
class LabelMetrics:
    """One label's scores. `None` means unavailable: no examples or no predictions."""

    support: int  # tickets that should have this label
    predicted: int  # tickets the classifier gave this label
    precision: float | None
    recall: float | None
    f1: float | None


@dataclass(slots=True)
class QuestionScore:
    correct: int = 0
    total: int = 0
    labels: dict[str, LabelMetrics] = field(default_factory=dict)
    macro_f1: float | None = None
    macro_labels: int = 0  # how many labels had an F1 to average

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
    distributions: dict[str, dict[str, int]] = field(default_factory=dict)
    n_missing: int = 0

    @property
    def ambiguous_pct(self) -> float:
        return (
            round(100 * self.n_ambiguous / self.n_tickets, 1) if self.n_tickets else 0.0
        )


def _label_metrics(
    kind: type[StrEnum], pairs: Sequence[tuple[str, str]]
) -> tuple[dict[str, LabelMetrics], float | None, int]:
    labels: dict[str, LabelMetrics] = {}
    for member in kind:
        label = str(member.value)
        support = sum(1 for e, _ in pairs if e == label)
        predicted = sum(1 for _, p in pairs if p == label)
        true_pos = sum(1 for e, p in pairs if e == label and p == label)
        precision = true_pos / predicted if predicted else None
        recall = true_pos / support if support else None
        f1: float | None = None
        if precision is not None and recall is not None:
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall
                else 0.0
            )
        labels[label] = LabelMetrics(support, predicted, precision, recall, f1)
    f1s = [m.f1 for m in labels.values() if m.f1 is not None]
    return labels, (sum(f1s) / len(f1s) if f1s else None), len(f1s)


def _score_dict(v: QuestionScore) -> dict[str, Any]:
    return {
        "correct": v.correct,
        "total": v.total,
        "accuracy": v.accuracy,
        "macro_f1": v.macro_f1,
        "macro_f1_labels": v.macro_labels,
        "labels": {label: asdict(m) for label, m in v.labels.items()},
    }


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
                    "ambiguous_pct": s.ambiguous_pct,
                    "n_missing": s.n_missing,
                    "distributions": s.distributions,
                    "scores": {q: _score_dict(v) for q, v in s.scores.items()},
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
            if path.stem in {m.value for m in Split} and item.split.value != path.stem:
                raise DatasetError(
                    f"{where}: split is '{item.split.value}' but the file is {path.name}; "
                    f"move the ticket or fix its split"
                )
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
    """Tickets in a batch that fails are left out of the result; they are counted as missing."""
    use_case = AnalyzeTickets(classifier)
    predictions: dict[str, TicketAnalysis] = {}
    model, latency = "", 0.0
    for start in range(0, len(tickets), MAX_BATCH_SIZE):
        chunk = tuple(tickets[start : start + MAX_BATCH_SIZE])
        try:
            result = use_case.execute(AnalyzeTicketsInput(tickets=chunk))
        except DomainError:
            continue
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
        pairs: dict[str, list[tuple[str, str]]] = {q: [] for q in QUESTIONS}
        misses: list[Miss] = []
        n_missing = 0
        for item in items:
            analysis = predictions.get(item.ticket.id)
            n_missing += analysis is None
            if item.ambiguous:
                continue
            for question in QUESTIONS:
                expected = item.expected.label(question)
                predicted = (
                    str(getattr(analysis, question).value) if analysis else MISSING
                )
                pairs[question].append((expected, predicted))
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
                            _confidence(analysis, question) if analysis else 0.0,
                        )
                    )
        for question in QUESTIONS:
            score = scores[question]
            score.labels, score.macro_f1, score.macro_labels = _label_metrics(
                LABELS[question], pairs[question]
            )
        reports.append(
            SplitReport(
                split=split,
                n_tickets=len(items),
                n_ambiguous=sum(i.ambiguous for i in items),
                scores=scores,
                misses=tuple(misses),
                distributions={
                    q: dict(Counter(i.expected.label(q) for i in items))
                    for q in QUESTIONS
                },
                n_missing=n_missing,
            )
        )
    return EvalResult(splits=tuple(reports), model=model, latency_ms=round(latency, 2))


# --- report -----------------------------------------------------------------

_HELDOUT_NOTICE = (
    "Held-out set: report these numbers only. Do not tune descriptions on them.\n"
    "Its misses are hidden; pass --show-heldout-misses to see them."
)


def _pct(value: float | None) -> str:
    return "unavailable" if value is None else f"{value:.0%}"


def format_report(result: EvalResult, show_heldout_misses: bool = False) -> str:
    lines = [f"model: {result.model}   classification time: {result.latency_ms} ms", ""]
    for s in result.splits:
        ambiguous = (
            f", {s.n_ambiguous} ambiguous ({s.ambiguous_pct:g}%) excluded"
            if s.n_ambiguous
            else ""
        )
        lines.append(f"== {s.split.value} ({s.n_tickets} tickets{ambiguous})")
        lines.append(f"   missing predictions: {s.n_missing}")
        for question in QUESTIONS:
            score = s.scores[question]
            lines.append(
                f"   {question:<14} {score.correct}/{score.total}  "
                f"{score.accuracy:.0%}   macro-F1 {_pct(score.macro_f1)}"
                + (
                    f" ({score.macro_labels} labels)"
                    if score.macro_f1 is not None
                    else ""
                )
            )
        lines.append("   expected labels:")
        for question in QUESTIONS:
            counts = ", ".join(
                f"{label} {n}" for label, n in sorted(s.distributions[question].items())
            )
            lines.append(f"     {question}: {counts}")
        lines.append("   per label (precision / recall / F1 / expected):")
        for question in QUESTIONS:
            for label, lm in s.scores[question].labels.items():
                if lm.support == 0 and lm.predicted == 0:
                    continue
                lines.append(
                    f"     {question}.{label}: {_pct(lm.precision)} / {_pct(lm.recall)} / "
                    f"{_pct(lm.f1)} / {lm.support}"
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


# --- coverage ---------------------------------------------------------------

MIN_PER_TEAM, MIN_PER_CATEGORY, MIN_PER_SEVERITY = 2, 1, 2
MIN_DIFFICULT, MIN_TOTAL = (
    5,
    30,
)  # guide section 10: "approximately 5" and "at least 30"


@dataclass(frozen=True, slots=True)
class CoverageRow:
    dimension: str
    label: str
    count: int
    minimum: int

    @property
    def met(self) -> bool:
        return self.count >= self.minimum


def coverage(labeled: Sequence[LabeledTicket]) -> list[CoverageRow]:
    """Counts the new tickets (tuning and held-out; smoke is not counted) against the guide."""
    items = [i for i in labeled if i.split is not Split.SMOKE]
    minimums = {
        "assigned_team": MIN_PER_TEAM,
        "category": MIN_PER_CATEGORY,
        "severity": MIN_PER_SEVERITY,
    }
    rows: list[CoverageRow] = []
    for dimension, minimum in minimums.items():
        counts = Counter(i.expected.label(dimension) for i in items)
        rows += [
            CoverageRow(dimension, str(m.value), counts[str(m.value)], minimum)
            for m in LABELS[dimension]
        ]
    rows.append(
        CoverageRow(
            "ambiguous",
            "difficult cases",
            sum(i.ambiguous for i in items),
            MIN_DIFFICULT,
        )
    )
    rows.append(CoverageRow("total", "new tickets", len(items), MIN_TOTAL))
    return rows


def format_coverage(rows: Sequence[CoverageRow]) -> str:
    lines = ["coverage of the labeled set against the labeling guide (section 10)", ""]
    for r in rows:
        flag = "" if r.met else "   <- below minimum"
        lines.append(
            f"  {r.dimension:<14} {r.label:<28} {r.count:>3} / {r.minimum}{flag}"
        )
    short = sum(not r.met for r in rows)
    lines += [
        "",
        f"{short} of {len(rows)} targets below minimum" if short else "all targets met",
    ]
    return "\n".join(lines) + "\n"
