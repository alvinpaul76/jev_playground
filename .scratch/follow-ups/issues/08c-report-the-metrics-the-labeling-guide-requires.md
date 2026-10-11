# 08c Report the metrics the labeling guide requires

Status: resolved
Type: task
Parent: 08

## Agent Brief

**Category:** enhancement
**Summary:** Extend the eval harness so its report meets section 14 of the labeling guide, and so milestone results can be saved and compared.

**Current behavior:**
The harness reports, per split, the ticket count, the ambiguous count, accuracy per question and the misses. A classifier failure aborts the whole run. Nothing is saved between runs.

**Desired behavior:**
For each split the report also gives:
- the ambiguous count as a percentage of the split;
- the label distribution for severity, category and assigned team (expected labels);
- per-label precision, recall and F1 for each question, and macro-F1;
- a metric reported as "unavailable" (never 0 or 100%) when a label has no examples or no predictions;
- the number of invalid or missing predictions, counted instead of aborting the run.

Runs can be saved under a milestone name (for example `--save baseline`) with the date, backend and model, and the results of two saved runs can be compared. A ticket whose `split` does not match its file name (`tuning.jsonl`, `heldout.jsonl`) is a dataset error. A coverage view compares the labeled set's counts per team, category and severity with the minimums in the guide.

**Key interfaces:**
- `evaluate()` result type: gains per-question label metrics, distributions and an invalid-prediction count.
- `format_report()` and `to_dict()`: both show the new fields; held-out misses stay hidden unless requested.
- `uv run python -m evals.run_eval`: new options for saving and comparing results and for the coverage view.

**Acceptance criteria:**
- [x] Per-label precision, recall, F1 and macro-F1 are computed per question and checked against a hand-worked example.
- [x] A label with no examples or no predictions shows "unavailable", not 0 or 100%.
- [x] An invalid or missing prediction is counted and the run continues.
- [x] Ambiguous tickets are excluded from accuracy and reported as a count and a percentage.
- [x] A saved run records milestone name, date, backend and model, and two saved runs can be compared.
- [x] A split/file-name mismatch is reported as a dataset error naming the file and line.
- [x] The coverage view lists each team, category and severity against its minimum.
- [x] Tests, `ruff`, and `mypy` pass; `docs/evaluation.md` no longer lists these as missing.

**Out of scope:**
- Labeling tickets or changing the labeling guide (08b).
- Editing classifier label descriptions or choosing another model.

## Resolution (2026-10-11)
Done test-first. `evals/harness.py` now computes per-label precision, recall, F1 and macro-F1 (unavailable as `None`), distributions, ambiguous percentage and missing predictions (a failed batch is counted as wrong). `evals/results.py` saves and compares milestones (`--save`, `--compare`); `--coverage` checks the set against the guide. A split that does not match its file name is a dataset error. 117 tests, ruff and mypy pass.

Decisions made while building:
- A missing prediction counts as wrong in accuracy and recall; it does not count toward any label's precision.
- Macro-F1 averages only labels whose F1 exists, and the report says how many labels that was. A label the model never gave has no F1 and is left out of the average, so read macro-F1 together with the per-label lines.
- Saved runs never contain held-out misses.
- Review follow-up: missing predictions are split into *failed* (rejected even when sent alone) and *absent* (left out of a successful reply). A failed batch is retried one ticket at a time, so one bad ticket no longer blanks its batch. A missing prediction has no confidence (shown as "no prediction").
- Not done, by choice: `--compare` still shows only accuracy and macro-F1; the unknown-ticket percentage is not reported; the difficult-case minimum is enforced as exactly 5.
