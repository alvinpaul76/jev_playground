import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from evals.harness import (
    DatasetError,
    LabeledTicket,
    Split,
    evaluate,
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
