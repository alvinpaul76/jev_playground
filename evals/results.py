"""Saved milestone runs: write one, read one, and compare two.

Held-out misses are never saved, so a saved file can be shared without leaking the held-out set.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evals.harness import QUESTIONS, EvalResult, percent

RESULTS_DIR = Path(__file__).parent / "results"


class ResultsError(Exception):
    """A saved run cannot be written or read."""


def save_run(
    result: EvalResult, milestone: str, backend: str, directory: Path = RESULTS_DIR
) -> Path:
    if not milestone.replace("-", "").replace("_", "").isalnum():
        raise ResultsError(
            f"milestone name '{milestone}' may only use letters, digits, - and _"
        )
    path = directory / f"{milestone}.json"
    if path.exists():
        raise ResultsError(f"{path} already exists; pick a new milestone name")
    payload = {
        "milestone": milestone,
        "date": datetime.now(UTC).date().isoformat(),
        "backend": backend,
        **result.to_dict(show_heldout_misses=False),
    }
    directory.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def load_run(milestone: str, directory: Path = RESULTS_DIR) -> dict[str, Any]:
    path = directory / f"{milestone}.json"
    try:
        loaded: dict[str, Any] = json.loads(path.read_text())
    except FileNotFoundError:
        raise ResultsError(f"no saved run named '{milestone}' in {directory}") from None
    except json.JSONDecodeError as exc:
        raise ResultsError(f"{path}: invalid JSON ({exc.msg})") from exc
    return loaded


def _delta(old: float | None, new: float | None) -> str:
    if old is None or new is None:
        return "n/a"
    return f"{(new - old) * 100:+.0f} pts"


def compare_runs(old: dict[str, Any], new: dict[str, Any]) -> str:
    lines = [
        f"{old['milestone']} -> {new['milestone']}",
        f"  {old['milestone']}: {old['date']}, backend {old['backend']}, model {old['model']}",
        f"  {new['milestone']}: {new['date']}, backend {new['backend']}, model {new['model']}",
    ]
    if old["model"] != new["model"] or old["backend"] != new["backend"]:
        lines.append(
            "  note: the model or backend changed, so this is not a like-for-like test"
        )
    old_splits = {s["split"]: s for s in old["splits"]}
    for split in new["splits"]:
        before = old_splits.get(split["split"])
        if before is None:
            continue
        if before["n_tickets"] != split["n_tickets"]:
            lines.append(
                f"  note: {split['split']} had {before['n_tickets']} tickets and now has "
                f"{split['n_tickets']}; the sets differ"
            )
        lines += ["", f"== {split['split']}"]
        for question in QUESTIONS:
            was, now = before["scores"][question], split["scores"][question]
            lines.append(
                f"   {question:<14} accuracy {percent(was['accuracy'])} -> {percent(now['accuracy'])} "
                f"({_delta(was['accuracy'], now['accuracy'])})   "
                f"macro-F1 {percent(was['macro_f1'])} -> {percent(now['macro_f1'])} "
                f"({_delta(was['macro_f1'], now['macro_f1'])})"
            )
        lines.append(
            f"   missing predictions {before.get('n_missing', 0)} -> {split.get('n_missing', 0)}"
        )
        for question in QUESTIONS:
            was_labels = before["scores"][question].get("labels", {})
            now_labels = split["scores"][question].get("labels", {})
            for label, now_label in now_labels.items():
                was_f1 = was_labels.get(label, {}).get("f1")
                if was_f1 != now_label["f1"]:
                    lines.append(
                        f"   {question}.{label} F1 {percent(was_f1)} -> {percent(now_label['f1'])}"
                    )
    return "\n".join(lines) + "\n"
