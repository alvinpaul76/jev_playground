import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from evals.harness import (
    DatasetError,
    LabeledTicket,
    Split,
    coverage,
    evaluate,
    format_coverage,
    format_report,
    load_labeled_set,
)
from evals.run_eval import main
from jev_playground.modules.ticket_analysis.application.ports import (
    RawBatchClassification,
)
from jev_playground.modules.ticket_analysis.domain.entities import (
    Ticket,
    TicketAnalysis,
)
from jev_playground.modules.ticket_analysis.domain.errors import ClassifierUnavailable
from jev_playground.modules.ticket_analysis.domain.policies import MAX_BATCH_SIZE
from jev_playground.modules.ticket_analysis.domain.value_objects import (
    Category,
    Probability,
    Severity,
    Team,
)

SMOKE = Path(__file__).parents[2] / "evals" / "data" / "smoke.jsonl"


def line(id="A", split="tuning", expected=None, **extra):
    row = {
        "id": id,
        "title": "Stripe is down",
        "description": "Payments fail",
        "split": split,
        "expected": expected
        or {"severity": "high", "category": "incident", "assigned_team": "backend"},
        **extra,
    }
    return json.dumps(row)


def write(tmp_path: Path, *lines: str, name: str = "set.jsonl") -> Path:
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n")
    return path


class Scripted:
    """Classifier that answers from a table and records the batches it receives."""

    def __init__(self, answers=None, default=("high", "incident", "backend", 0.9)):
        self.answers = answers or {}
        self.default = default
        self.batches: list[int] = []

    def classify_many(self, tickets: Sequence[Ticket]) -> RawBatchClassification:
        self.batches.append(len(tickets))
        analyses = []
        for t in tickets:
            sev, cat, team, conf = self.answers.get(t.id, self.default)
            analyses.append(
                TicketAnalysis(
                    ticket_id=t.id,
                    severity=Severity(sev),
                    severity_confidence=Probability(conf),
                    category=Category(cat),
                    category_confidence=Probability(conf),
                    assigned_team=Team(team),
                    assigned_team_confidence=Probability(conf),
                )
            )
        return RawBatchClassification(tuple(analyses), model="scripted", latency_ms=1.0)


# --- loading --------------------------------------------------------------


def test_loads_a_valid_line_with_optional_fields(tmp_path):
    path = write(
        tmp_path,
        line(environment="production", evidence=["e1"], note="why", ambiguous=True),
    )
    [item] = load_labeled_set([path])
    assert item.ticket.id == "A"
    assert item.ticket.environment == "production"
    assert item.ticket.evidence == ("e1",)
    assert item.expected.assigned_team is Team.BACKEND
    assert item.split is Split.TUNING
    assert item.ambiguous is True and item.note == "why"


def test_blank_lines_are_skipped(tmp_path):
    path = write(tmp_path, line("A"), "", line("B"))
    assert [i.ticket.id for i in load_labeled_set([path])] == ["A", "B"]


def test_unknown_label_names_file_line_and_label(tmp_path):
    bad = line(
        "B",
        expected={"severity": "urgent", "category": "ui", "assigned_team": "backend"},
    )
    path = write(tmp_path, line("A"), bad)
    with pytest.raises(DatasetError, match=r"set\.jsonl:2.*urgent"):
        load_labeled_set([path])


def test_missing_expected_label_is_an_error(tmp_path):
    path = write(tmp_path, line("A", expected={"severity": "low"}))
    with pytest.raises(DatasetError, match=r"set\.jsonl:1.*category"):
        load_labeled_set([path])


def test_invalid_json_and_unknown_split_are_errors(tmp_path):
    with pytest.raises(DatasetError, match=r":1"):
        load_labeled_set([write(tmp_path, "{not json")])
    with pytest.raises(DatasetError, match="split"):
        load_labeled_set([write(tmp_path, line(split="holdout"), name="b.jsonl")])


def test_duplicate_ids_across_files_are_rejected(tmp_path):
    a = write(tmp_path, line("A"), name="a.jsonl")
    b = write(tmp_path, line("A"), name="b.jsonl")
    with pytest.raises(DatasetError, match="duplicate.*A"):
        load_labeled_set([a, b])


def test_invalid_ticket_fields_are_reported_with_location(tmp_path):
    path = write(tmp_path, line("A", title="   "))
    with pytest.raises(DatasetError, match=r"set\.jsonl:1.*title"):
        load_labeled_set([path])


def test_the_smoke_set_is_valid():
    items = load_labeled_set([SMOKE])
    assert [i.ticket.id for i in items] == [f"JEV-00{n}" for n in range(1, 9)]
    assert {i.split for i in items} == {Split.SMOKE}


# --- scoring --------------------------------------------------------------


def labeled(path: Path) -> list[LabeledTicket]:
    return load_labeled_set([path])


def test_accuracy_is_counted_per_question(tmp_path):
    path = write(
        tmp_path,
        line("A"),
        line(
            "B",
            expected={"severity": "low", "category": "ui", "assigned_team": "frontend"},
        ),
    )
    # A fully right; B right on severity only.
    answers = {
        "A": ("high", "incident", "backend", 0.9),
        "B": ("low", "incident", "backend", 0.8),
    }
    [report] = evaluate(labeled(path), Scripted(answers)).splits
    assert report.split is Split.TUNING and report.n_tickets == 2
    assert (report.scores["severity"].correct, report.scores["severity"].total) == (
        2,
        2,
    )
    assert (report.scores["category"].correct, report.scores["category"].total) == (
        1,
        2,
    )
    assert (
        report.scores["assigned_team"].correct,
        report.scores["assigned_team"].total,
    ) == (1, 2)
    assert report.scores["category"].accuracy == 0.5


def test_misses_record_expected_predicted_and_confidence(tmp_path):
    path = write(
        tmp_path,
        line(
            "B",
            expected={"severity": "low", "category": "ui", "assigned_team": "frontend"},
        ),
    )
    [report] = evaluate(
        labeled(path), Scripted({"B": ("low", "ui", "devops", 0.42)})
    ).splits
    [miss] = report.misses
    assert (miss.ticket_id, miss.question) == ("B", "assigned_team")
    assert (miss.expected, miss.predicted, miss.confidence) == (
        "frontend",
        "devops",
        0.42,
    )


def test_ambiguous_tickets_are_counted_but_excluded_from_accuracy(tmp_path):
    path = write(tmp_path, line("A"), line("B", ambiguous=True))
    answers = {"B": ("low", "ui", "frontend", 0.5)}  # wrong everywhere, but ambiguous
    [report] = evaluate(labeled(path), Scripted(answers)).splits
    assert report.n_tickets == 2 and report.n_ambiguous == 1
    assert report.scores["severity"].total == 1
    assert report.scores["severity"].correct == 1
    assert report.misses == ()


def test_splits_are_reported_separately_in_a_fixed_order(tmp_path):
    path = write(
        tmp_path,
        line("H", split="heldout"),
        line("T", split="tuning"),
        line("S", split="smoke"),
    )
    result = evaluate(labeled(path), Scripted())
    assert [r.split.value for r in result.splits] == ["smoke", "tuning", "heldout"]


def test_requests_are_chunked_to_the_batch_limit(tmp_path):
    n = MAX_BATCH_SIZE * 2 + 5
    path = write(tmp_path, *[line(f"T{i}") for i in range(n)])
    classifier = Scripted()
    evaluate(labeled(path), classifier)
    assert classifier.batches == [MAX_BATCH_SIZE, MAX_BATCH_SIZE, 5]


def test_an_empty_set_gives_an_empty_report():
    assert evaluate([], Scripted()).splits == ()


def test_result_carries_model_and_total_latency(tmp_path):
    path = write(tmp_path, *[line(f"T{i}") for i in range(MAX_BATCH_SIZE + 1)])
    result = evaluate(labeled(path), Scripted())
    assert result.model == "scripted"
    assert result.latency_ms == 2.0


# --- report text ----------------------------------------------------------


def make_items(tmp_path) -> list[LabeledTicket]:
    path = write(
        tmp_path,
        line(
            "T1",
            split="tuning",
            expected={"severity": "low", "category": "ui", "assigned_team": "frontend"},
        ),
        line(
            "H1",
            split="heldout",
            expected={"severity": "low", "category": "ui", "assigned_team": "frontend"},
        ),
    )
    return labeled(path)


def test_report_shows_accuracy_and_misses_for_tuning(tmp_path):
    result = evaluate(make_items(tmp_path), Scripted())
    text = format_report(result)
    assert "tuning" in text and "severity" in text and "0/1" in text
    assert "T1" in text and "expected=frontend" in text


def test_heldout_misses_are_hidden_unless_requested(tmp_path):
    result = evaluate(make_items(tmp_path), Scripted())
    hidden = format_report(result)
    assert "H1" not in hidden
    assert "do not tune" in hidden.lower()
    assert "H1" in format_report(result, show_heldout_misses=True)


# --- command line ---------------------------------------------------------


def test_cli_runs_the_production_classifier_on_the_mock_backend(tmp_path, capsys):
    path = write(tmp_path, line("A"), line("B"))
    code = main(["--data", str(path), "--backend", "mock"])
    out = capsys.readouterr().out
    assert code == 0
    assert "openjev-mock" in out
    assert "assigned_team" in out


def test_cli_json_output_is_machine_readable(tmp_path, capsys):
    path = write(tmp_path, line("A"))
    assert main(["--data", str(path), "--backend", "mock", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["model"] == "openjev-mock"
    assert data["splits"][0]["scores"]["severity"]["total"] == 1


def test_cli_reports_dataset_errors_without_a_traceback(tmp_path, capsys):
    path = write(tmp_path, "{broken")
    assert main(["--data", str(path), "--backend", "mock"]) == 2
    assert "set.jsonl:1" in capsys.readouterr().err


def test_cli_split_filter_limits_what_runs(tmp_path, capsys):
    path = write(tmp_path, line("A", split="tuning"), line("B", split="heldout"))
    main(["--data", str(path), "--backend", "mock", "--split", "tuning", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert [s["split"] for s in data["splits"]] == ["tuning"]


def test_json_keeps_one_type_for_misses_and_flags_hidden_heldout(tmp_path):
    result = evaluate(make_items(tmp_path), Scripted())
    tuning, heldout = result.to_dict()["splits"]
    assert isinstance(tuning["misses"], list) and tuning["misses_hidden"] is False
    assert heldout["misses"] == [] and heldout["misses_hidden"] is True


def test_json_shows_heldout_misses_when_requested(tmp_path):
    result = evaluate(make_items(tmp_path), Scripted())
    heldout = result.to_dict(show_heldout_misses=True)["splits"][1]
    assert heldout["misses_hidden"] is False
    assert [m["ticket_id"] for m in heldout["misses"]] == ["H1"] * 3


def test_cli_json_honours_show_heldout_misses(tmp_path, capsys):
    path = write(
        tmp_path,
        line(
            "H",
            split="heldout",
            expected={"severity": "low", "category": "ui", "assigned_team": "frontend"},
        ),
    )
    main(["--data", str(path), "--backend", "mock", "--json", "--show-heldout-misses"])
    data = json.loads(capsys.readouterr().out)
    assert data["splits"][0]["misses_hidden"] is False


# --- 08c: metrics the labeling guide requires -------------------------------


def sev(label: str) -> dict[str, str]:
    return {"severity": label, "category": "incident", "assigned_team": "backend"}


def severity_report(tmp_path, pairs):
    """pairs: (expected severity, predicted severity). Returns the severity score."""
    lines = [line(id=f"T{i}", expected=sev(e)) for i, (e, _) in enumerate(pairs)]
    answers = {
        f"T{i}": (p, "incident", "backend", 0.9) for i, (_, p) in enumerate(pairs)
    }
    result = evaluate(labeled(write(tmp_path, *lines)), Scripted(answers))
    return result.splits[0].scores["severity"]


def test_precision_recall_f1_and_macro_f1_match_a_hand_worked_example(tmp_path):
    # high: predicted 1x, right 1x, expected 2x -> P=1, R=1/2, F1=2/3
    # low:  predicted 3x, right 2x, expected 2x -> P=2/3, R=1, F1=4/5
    score = severity_report(
        tmp_path, [("high", "high"), ("high", "low"), ("low", "low"), ("low", "low")]
    )
    high, low = score.labels["high"], score.labels["low"]
    assert (high.precision, high.recall) == (1.0, 0.5)
    assert high.f1 == pytest.approx(2 / 3)
    assert low.precision == pytest.approx(2 / 3)
    assert low.recall == 1.0
    assert low.f1 == pytest.approx(0.8)
    assert score.macro_f1 == pytest.approx((2 / 3 + 0.8) / 2)
    assert score.macro_labels == 2


def test_a_label_nobody_expected_or_predicted_is_unavailable_not_zero(tmp_path):
    score = severity_report(tmp_path, [("high", "high"), ("low", "low")])
    critical = score.labels["critical"]
    assert (critical.precision, critical.recall, critical.f1) == (None, None, None)
    assert critical.support == 0


def test_a_label_predicted_but_never_expected_has_precision_zero_and_no_recall(
    tmp_path,
):
    score = severity_report(tmp_path, [("high", "critical"), ("high", "high")])
    critical = score.labels["critical"]
    assert critical.precision == 0.0
    assert critical.recall is None
    assert critical.f1 is None


def test_a_label_expected_but_never_predicted_has_no_precision(tmp_path):
    score = severity_report(tmp_path, [("high", "low"), ("low", "low")])
    high = score.labels["high"]
    assert high.precision is None
    assert high.recall == 0.0
    assert high.f1 is None
    assert score.macro_labels == 1  # only 'low' has an F1 to average


def test_macro_f1_is_unavailable_when_no_label_has_an_f1(tmp_path):
    score = severity_report(tmp_path, [("high", "low")])
    assert score.macro_f1 is None


def test_ambiguous_tickets_are_reported_as_a_percentage(tmp_path):
    lines = [line(id="A", ambiguous=True), line(id="B"), line(id="C"), line(id="D")]
    [report] = evaluate(labeled(write(tmp_path, *lines)), Scripted()).splits
    assert report.n_ambiguous == 1
    assert report.ambiguous_pct == 25.0


def test_distribution_counts_expected_labels_for_every_ticket(tmp_path):
    lines = [
        line(id="A", expected=sev("high")),
        line(id="B", expected=sev("high")),
        line(id="C", expected=sev("low"), ambiguous=True),
    ]
    [report] = evaluate(labeled(write(tmp_path, *lines)), Scripted()).splits
    assert report.distributions["severity"] == {"high": 2, "low": 1}
    assert report.distributions["assigned_team"] == {"backend": 3}


class FailsFirstBatch:
    """Raises ClassifierUnavailable for the first batch, then answers normally."""

    def __init__(self) -> None:
        self.inner = Scripted()
        self.calls = 0

    def classify_many(self, tickets: Sequence[Ticket]) -> RawBatchClassification:
        self.calls += 1
        if self.calls == 1:
            raise ClassifierUnavailable()
        return self.inner.classify_many(tickets)


def test_a_failed_batch_is_counted_as_missing_and_the_run_continues(tmp_path):
    n = MAX_BATCH_SIZE + 2
    lines = [line(id=f"T{i}") for i in range(n)]
    classifier = FailsFirstBatch()
    [report] = evaluate(labeled(write(tmp_path, *lines)), classifier).splits
    assert classifier.calls == 2
    assert report.n_missing == MAX_BATCH_SIZE
    # missing predictions count as wrong; they are never silently dropped
    assert report.scores["severity"].total == n
    assert report.scores["severity"].correct == 2
    assert {m.predicted for m in report.misses} == {"missing"}


def test_the_report_shows_the_new_figures(tmp_path):
    lines = [
        line(id="A", expected=sev("low")),  # the scripted classifier says "high"
        line(id="B", expected=sev("low"), ambiguous=True),
    ]
    result = evaluate(labeled(write(tmp_path, *lines)), Scripted())
    text = format_report(result)
    assert "1 ambiguous (50%)" in text
    assert "macro-F1" in text
    assert "unavailable" in text
    assert "missing predictions: 0" in text
    assert "expected labels" in text


def test_json_carries_metrics_distributions_and_missing_counts(tmp_path):
    result = evaluate(labeled(write(tmp_path, line(id="A"))), Scripted())
    split = result.to_dict()["splits"][0]
    assert split["n_missing"] == 0
    assert split["ambiguous_pct"] == 0.0
    assert split["distributions"]["severity"] == {"high": 1}
    severity = split["scores"]["severity"]
    assert severity["macro_f1"] == 1.0
    assert severity["labels"]["critical"]["f1"] is None  # unavailable -> null


# --- 08c: split must match the file name ------------------------------------


def test_a_ticket_in_the_wrong_split_file_is_a_dataset_error(tmp_path):
    path = write(tmp_path, line(split="heldout"), name="tuning.jsonl")
    with pytest.raises(DatasetError, match=r"tuning\.jsonl:1.*heldout.*tuning"):
        load_labeled_set([path])


def test_files_with_other_names_may_hold_any_split(tmp_path):
    [item] = load_labeled_set(
        [write(tmp_path, line(split="heldout"), name="mine.jsonl")]
    )
    assert item.split is Split.HELDOUT


def test_the_shipped_data_files_match_their_splits():
    paths = sorted((SMOKE.parent).glob("*.jsonl"))
    assert len(load_labeled_set(paths)) >= 8


# --- 08c: coverage against the guide's minimums -----------------------------


def test_coverage_lists_each_label_against_its_minimum(tmp_path):
    lines = [
        line(id="A", expected=sev("high")),
        line(id="B", expected=sev("high"), ambiguous=True),
        line(id="C", split="smoke", expected=sev("critical")),  # smoke is not counted
    ]
    rows = coverage(labeled(write(tmp_path, *lines)))
    by_key = {(r.dimension, r.label): r for r in rows}
    assert by_key[("severity", "high")].count == 2
    assert by_key[("severity", "high")].minimum == 2
    assert by_key[("severity", "high")].met
    assert by_key[("severity", "critical")].count == 0
    assert not by_key[("severity", "critical")].met
    assert by_key[("assigned_team", "backend")].minimum == 2
    assert by_key[("category", "incident")].minimum == 1
    assert by_key[("ambiguous", "difficult cases")].count == 1
    assert by_key[("total", "new tickets")].minimum == 30
    text = format_coverage(rows)
    assert "severity" in text and "critical" in text and "below minimum" in text


# --- 08c: saving and comparing runs -----------------------------------------


def test_cli_saves_a_named_run_with_date_backend_and_model(tmp_path, capsys):
    data = write(tmp_path, line(id="A"), line(id="B", split="heldout"))
    out = tmp_path / "results"
    code = main(
        [
            "--data",
            str(data),
            "--backend",
            "mock",
            "--save",
            "baseline",
            "--results-dir",
            str(out),
        ]
    )
    assert code == 0
    saved = json.loads((out / "baseline.json").read_text())
    assert saved["milestone"] == "baseline"
    assert saved["backend"] == "mock"
    assert saved["model"]
    assert saved["date"]
    held = next(s for s in saved["splits"] if s["split"] == "heldout")
    assert held["misses_hidden"] is True and held["misses"] == []  # never saved


def test_saving_over_an_existing_run_is_refused(tmp_path, capsys):
    data = write(tmp_path, line(id="A"))
    args = [
        "--data",
        str(data),
        "--backend",
        "mock",
        "--save",
        "m",
        "--results-dir",
        str(tmp_path),
    ]
    assert main(args) == 0
    assert main(args) == 2
    assert "already exists" in capsys.readouterr().err


def test_cli_compares_two_saved_runs(tmp_path, capsys):
    base = {
        "milestone": "baseline",
        "date": "2026-10-11",
        "backend": "jev",
        "model": "m1",
        "splits": [
            {
                "split": "tuning",
                "n_tickets": 12,
                "n_ambiguous": 0,
                "scores": {
                    "severity": {"accuracy": 0.5, "macro_f1": 0.4},
                    "category": {"accuracy": 0.6, "macro_f1": None},
                    "assigned_team": {"accuracy": 0.7, "macro_f1": 0.7},
                },
            }
        ],
    }
    new = json.loads(json.dumps(base))
    new["milestone"] = "tuned"
    new["splits"][0]["scores"]["severity"] = {"accuracy": 0.75, "macro_f1": 0.5}
    (tmp_path / "baseline.json").write_text(json.dumps(base))
    (tmp_path / "tuned.json").write_text(json.dumps(new))
    code = main(["--compare", "baseline", "tuned", "--results-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    assert "baseline -> tuned" in out
    assert "severity" in out and "+25" in out
    assert "unavailable" in out


def test_cli_coverage_prints_the_view_without_running_a_model(tmp_path, capsys):
    data = write(tmp_path, line(id="A"))
    assert main(["--data", str(data), "--coverage"]) == 0
    assert "below minimum" in capsys.readouterr().out
