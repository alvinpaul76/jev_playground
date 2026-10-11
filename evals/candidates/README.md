# Candidate tickets (unlabeled)

`hand-written.jsonl` holds 15 drafted tickets, written to fill gaps that real tickets usually leave: critical outages, thin or vague reports, data exposure, payments and billing, and tickets that could go to two teams. They carry no labels on purpose. You decide every label.

The harness does not read this folder, so nothing here affects a run.

## How to use them

1. Read `../LABELING-GUIDE.md`; its rules and label definitions decide every label.
2. For each ticket you keep, decide its labels following the guide, without running the model.
3. Add `"split"` (`tuning` or `heldout`) and `"expected"` to the line, and move it into `../data/tuning.jsonl` or `../data/heldout.jsonl`.
4. Rewrite any ticket that reads too tidy to be real, or drop it.
5. Check the files load: `uv run python -m evals.run_eval --backend mock`.

Ids start with `HW-` so they never collide with real ticket ids.
