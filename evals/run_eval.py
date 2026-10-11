"""Run the evaluation: `uv run python -m evals.run_eval [--backend jev] [--split tuning]`."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from evals.harness import (
    DatasetError,
    Split,
    evaluate,
    format_report,
    load_labeled_set,
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
    args = parser.parse_args(argv)

    paths = args.data or sorted(DATA_DIR.glob("*.jsonl"))
    try:
        labeled = load_labeled_set(paths)
    except DatasetError as exc:
        print(f"dataset error: {exc}", file=sys.stderr)
        return 2
    if args.split:
        wanted = {Split(s) for s in args.split}
        labeled = [item for item in labeled if item.split in wanted]

    settings = Settings(backend=args.backend) if args.backend else Settings()
    classifier = OpenJevTicketClassifier(build_backend(settings))
    result = evaluate(labeled, classifier)

    if args.json:
        print(json.dumps(result.to_dict(args.show_heldout_misses), indent=2))
    else:
        print(
            format_report(result, show_heldout_misses=args.show_heldout_misses), end=""
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
