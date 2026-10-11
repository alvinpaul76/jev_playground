# 04 Keep the scratch script as an eval

Status: resolved
Type: task

## What
`src/jev_playground/ticket_analyis.py` shipped in the package and loaded a model on import. It moved to `evals/triage_eval.py` (typo fixed): 8 labeled sample tickets, labels stripped before prompting,
prints PASS or FAIL per ticket and an accuracy line. (Replaced later by `evals/run_eval.py`, follow-ups/08a.) Run it with `uv run python evals/triage_eval.py`. `evals/` is in `.dockerignore`.
