# 08a Eval harness for the production classifier

Status: resolved
Type: task
Parent: 08

## What
A repeatable command that runs the same use case the API runs over a labeled set and reports accuracy per question, with the misses listed. Split out of 08 during grilling (Q1).

## Built
- `evals/harness.py`: loader for JSONL labeled sets (errors name `file:line`; duplicate ids rejected), `evaluate()` (runs `AnalyzeTickets`, chunked to the batch limit, accuracy per question and per split, `ambiguous` tickets counted but excluded), `format_report()`.
- `evals/run_eval.py`: `uv run python -m evals.run_eval [--data FILE...] [--backend hf|jev|mock] [--split smoke tuning heldout] [--json] [--show-heldout-misses]`. Backend defaults to `JEV_BACKEND`.
- Held-out set rule (grilling Q6): its misses are hidden unless `--show-heldout-misses`, and the report says not to tune on them.
- `evals/data/smoke.jsonl`: the 8 sample tickets (team labels as slugs). JEV-001 keeps the owner's `devops` label with a note that the rule is still open (grilling Q4).
- `evals/triage_eval.py` removed (superseded). `src/poc/ticket_analyis.py` is left alone; it is the owner's scratch script (grilling Q8: owner decides whether to delete it).
- `GLOSSARY.md` created with the agreed terms (grilling Q9). `evals/` added to mypy.

## Update (2026-10-11)
Grilling Q4 settled the team rule (assign the team that can fix the cause), so JEV-001 was relabeled `devops` to `backend` in the smoke set. Team accuracy on the smoke set is now 8/8, but only because the label changed, not the model. The smoke set measures breakage, not accuracy.

## Verified by
21 tests in `tests/evals/` (loader errors, scoring, ambiguous handling, chunking, held-out hiding, CLI on the mock backend). Live, hosted Jev, production classifier: severity 7/8, category 8/8, assigned_team 7/8, the same numbers as the earlier ad-hoc run. Misses: JEV-001 team (expected devops, predicted backend 0.96), JEV-007 severity (expected medium, predicted high 0.76).
