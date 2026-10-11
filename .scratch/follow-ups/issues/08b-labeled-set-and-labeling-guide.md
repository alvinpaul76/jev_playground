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

**Acceptance criteria:**
- [ ] Label definitions are written in the guide, in the owner's words, without copying the classifier's descriptions.
- [ ] At least 30 labeled tickets exist: about 12 tuning, at least 18 held-out, ids unique across files.
- [ ] Coverage table met: at least 2 per team, 1 per category, 2 per severity, about 5 hard cases.
- [ ] `uv run python -m evals.run_eval --backend mock` loads every file without errors.
- [ ] A first held-out accuracy per question is recorded in this issue.

**Out of scope:**
- Editing the classifier's label descriptions (that comes after a baseline is recorded).
- Choosing a different model (follow-up 01).
- Deleting `src/poc/ticket_analyis.py` (the owner's call).
