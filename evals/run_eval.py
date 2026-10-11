"""Run the evaluation: `uv run python -m evals.run_eval [--backend jev] [--split tuning]`."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from evals.harness import (
    DatasetError,
    Split,
    coverage,
    evaluate,
    format_coverage,
    format_report,
    load_labeled_set,
)
from evals.results import (
    RESULTS_DIR,
    ResultsError,
    compare_runs,
    load_run,
    save_run,
)
from jev_playground.config import Settings
from jev_playground.modules.ticket_analysis.infrastructure.backends import build_backend
from jev_playground.modules.ticket_analysis.infrastructure.openjev_classifier import (
    OpenJevTicketClassifier,
)

DATA_DIR = Path(__file__).parent / "data"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", nargs="+", type=Path, help="JSONL files (default: evals/data/*.jsonl)"
    )
    parser.add_argument(
        "--backend", choices=["hf", "jev", "mock"], help="override JEV_BACKEND"
    )
    parser.add_argument(
        "--split", nargs="+", choices=[s.value for s in Split], help="only these splits"
    )
    parser.add_argument(
        "--json", action="store_true", help="print machine-readable JSON"
    )
    parser.add_argument(
        "--show-heldout-misses", action="store_true", help="list held-out misses"
    )
    parser.add_argument(
        "--save", metavar="NAME", help="keep this run as a named milestone"
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("OLD", "NEW"),
        help="compare two saved milestones (runs no model)",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="check the labeled set against the guide's minimums (runs no model)",
    )
    parser.add_argument(
        "--results-dir", type=Path, default=RESULTS_DIR, help="where saved runs live"
    )
    args = parser.parse_args(argv)

    if args.compare:
        try:
            old, new = (load_run(name, args.results_dir) for name in args.compare)
        except ResultsError as exc:
            print(f"results error: {exc}", file=sys.stderr)
            return 2
        print(compare_runs(old, new), end="")
        return 0

    paths = args.data or sorted(DATA_DIR.glob("*.jsonl"))
    try:
        labeled = load_labeled_set(paths)
    except DatasetError as exc:
        print(f"dataset error: {exc}", file=sys.stderr)
        return 2
    if args.coverage:
        print(format_coverage(coverage(labeled)), end="")
        return 0
    if args.split:
        wanted = {Split(s) for s in args.split}
        labeled = [item for item in labeled if item.split in wanted]

    settings = Settings(backend=args.backend) if args.backend else Settings()
    if args.save and (args.results_dir / f"{args.save}.json").exists():
        print(f"results error: milestone '{args.save}' already exists", file=sys.stderr)
        return 2
    classifier = OpenJevTicketClassifier(build_backend(settings))
    result = evaluate(labeled, classifier)

    if args.json:
        print(json.dumps(result.to_dict(args.show_heldout_misses), indent=2))
    else:
        print(
            format_report(result, show_heldout_misses=args.show_heldout_misses), end=""
        )
    if args.save:
        try:
            path = save_run(result, args.save, settings.backend, args.results_dir)
        except ResultsError as exc:
            print(f"results error: {exc}", file=sys.stderr)
            return 2
        print(f"saved {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
