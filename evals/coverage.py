"""Checks the labeled set against the minimums in section 10 of the labeling guide."""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from evals.harness import LABELS, LabeledTicket, Split

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
    approximate: bool = False  # the guide says "approximately"; one short still counts

    @property
    def met(self) -> bool:
        return self.count >= self.minimum - (1 if self.approximate else 0)

    @property
    def target_text(self) -> str:
        return f"about {self.minimum}" if self.approximate else str(self.minimum)


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
            "difficult",
            "difficult cases",
            sum(i.ambiguous for i in items),
            MIN_DIFFICULT,
            approximate=True,
        )
    )
    rows.append(CoverageRow("total", "new tickets", len(items), MIN_TOTAL))
    return rows


def format_coverage(rows: Sequence[CoverageRow]) -> str:
    lines = ["coverage of the labeled set against the labeling guide (section 10)", ""]
    for r in rows:
        flag = "" if r.met else "   <- below minimum"
        lines.append(
            f"  {r.dimension:<14} {r.label:<28} {r.count:>3} / {r.target_text}{flag}"
        )
    short = sum(not r.met for r in rows)
    lines += [
        "",
        f"{short} of {len(rows)} targets below minimum" if short else "all targets met",
    ]
    return "\n".join(lines) + "\n"
