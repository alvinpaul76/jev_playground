# 08b Labeled set and labeling guide

Status: ready-for-human
Type: research
Parent: 08

## Why a human has to do this
Deciding the expected label of each ticket is a judgment call about your own teams and priorities. It cannot be delegated to a model: a model-labeled set would only measure how much the model agrees with itself.

## Agent Brief

**Category:** enhancement
**Summary:** Write the label definitions, then label at least 30 new tickets into a tuning set and a held-out set.

**Current behavior:**
The only labeled tickets are the 8 in the smoke set, and their label descriptions were adjusted after seeing results. Accuracy cannot be reported fairly.

**Desired behavior:**
The owner writes one-sentence definitions for each severity, category and team in the labeling guide, then labels at least 30 new tickets by hand, following the guide. A draft guide with all the agreed rules exists (decisions below). The harness loads the new files without errors and reports the first held-out accuracy.

**Decisions (grilling, settled 2026-10-11):**
- Tickets are a mix of real (anonymized) and hand-written ones; a person always decides the expected label (Q2).
- One person labels, following the written guide; tickets they cannot decide are marked `ambiguous` and left out of accuracy (Q3).
- `assigned_team` is the team that can fix the cause (Q4). `JEV-001` was relabeled from `devops` to `backend` on this rule.
- Severity is `unknown` when impact cannot be judged; category is `unknown` only when no other fits; there is no `unknown` team, and a vague ticket goes to `tech_support` (Q5).
- Spread: at least 2 tickets per team, 1 per category, 2 per severity, plus about 5 hard cases (Q7).
- Split: about 12 tuning, at least 18 held-out; the split is chosen when a ticket is added (Q6).

**Key interfaces:**
- Labeled-set files: JSONL, one ticket per line, `split` of `tuning` or `heldout`, `expected` with `severity`, `category` and `assigned_team`.
- `uv run python -m evals.run_eval`: loads all files and reports accuracy per question and split; with `--backend mock` it only checks the files.
- The labeling guide (draft) holds the rules, the coverage table, and the empty definitions section to fill in.

**Baseline (2026-10-11), saved as `evals/results/baseline-2.json` (backend jev, model jev-1.13.0). This replaces `baseline.json`, which scored the held-out set before HW-005 was swapped for a vague ticket (to meet the two-`unknown`-severity minimum).**
- tuning (9 scored, 3 ambiguous): severity 44%, category 100%, assigned_team 100%.
- held-out (16 scored, 2 ambiguous): severity 38%, category 94%, assigned_team 94%; macro-F1 46%, 96%, 95%.
- Severity is the weak spot in both sets: the model often says `high` or `medium` where `low` or `medium` was expected (tuning misses HW-016, 018, 021, 023, 025).
- Coverage: all targets in the guide's section 10 are met.

**After tuning the severity descriptions (2026-10-11), saved as `evals/results/after-tuning.json`:**
- The severity descriptions in `openjev_classifier.py` were rewritten from section 6 of the guide (business impact and workarounds; established risk, not possible risk), using the tuning set only, in two rounds.
- tuning severity 44% -> 78%, macro-F1 27% -> 76%.
- held-out (run once) severity 38% -> 62%, macro-F1 46% -> 66%; category and team unchanged at 94%.
- After a code review the severity wording was moved closer to the guide's section 6.1 phrases (critical now says corruption and "generally unavailable" workaround; high says significant business function and the workaround note). Tuning stayed at 78%. Held-out was not re-run, so `after-tuning.json` reflects the wording before this touch-up.
- Remaining tuning misses: HW-024 (predicted medium, expected high) and HW-025 (predicted medium, expected low). The held-out misses were not inspected.
- Because held-out was run once for this milestone, a future tuning round should use a fresh held-out set.

**Progress (2026-10-11):** the owner's labeling guide (version 1.1) is written, including the label definitions. 15 unlabeled hand-written candidates are drafted in `evals/candidates/`. Still to do: label them, pull and label about 15 real tickets, and create `evals/data/tuning.jsonl` and `evals/data/heldout.jsonl`.

**Acceptance criteria:**
- [x] Label definitions are written in the guide, in the owner's words, without copying the classifier's descriptions.
- [x] At least 30 labeled tickets exist: about 12 tuning, at least 18 held-out, ids unique across files.
- [x] Coverage table met: at least 2 per team, 1 per category, 2 per severity, about 5 hard cases.
- [x] `uv run python -m evals.run_eval --backend mock` loads every file without errors.
- [x] A first held-out accuracy per question is recorded in this issue.

**Out of scope:**
- Editing the classifier's label descriptions (that comes after a baseline is recorded).
- Choosing a different model (follow-up 01).
- Deleting `src/poc/ticket_analyis.py` (the owner's call).
