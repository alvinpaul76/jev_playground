# Measuring label accuracy

Use this page to check how often the service's labels match what a person decided. It is for whoever tunes the label descriptions or compares models.

New to a word? See the [word list](glossary.md).

## Why measure?

The service labels each ticket with a severity, a category and a team. Without a check, a change to a label description might make some answers better and others worse, and nobody would know. The check runs the same code path the API uses and compares its answers with labels a person chose.

## What do I need?

A set of tickets with **expected labels**: the answers a person decided are right. They live in `evals/data/*.jsonl`, one ticket per line. The rules for deciding those labels are in the [labeling guide](../evals/LABELING-GUIDE.md), which also covers the file format, the number of tickets, and how they are spread.

## How do I run it?

1. Check the files without calling any model:
   ```bash
   uv run python -m evals.run_eval --backend mock
   ```
   A mistake is reported with the file and line, for example `set.jsonl:2: severity 'urgent' is not one of: critical, high, medium, low, unknown`.
2. Run it against a real model. It uses the backend set in `JEV_BACKEND` (see [the backends](architecture.md#which-model-answers-the-questions)):
   ```bash
   uv run python -m evals.run_eval
   ```
3. Read the report. This one is from a real run against the hosted service:
   ```
   model: jev-1.13.0   classification time: 1994.17 ms

   == smoke (8 tickets)
      severity       7/8  88%
      category       8/8  100%
      assigned_team  8/8  100%
      misses:
        JEV-007 severity: expected=medium predicted=high (confidence 0.75)
   ```
   Each line shows how many tickets got the expected label. Each miss shows the expected label, the model's label, and how sure the model was.

   Newer reports also show, for each set:
   - how many tickets are ambiguous, and what percentage that is (they are left out of accuracy);
   - how many predictions are missing (a failed batch counts as wrong, it is never dropped);
   - **macro-F1**, a single score per question that treats every label equally, so a rare label counts as much as a common one;
   - for each label, **precision** (when the model says this label, how often is it right), **recall** (of the tickets that should have it, how many did it find) and **F1** (one number combining the two);
   - how many tickets carry each expected label.

   A figure shows as `unavailable` when it cannot be worked out, for example precision for a label the model never gave. It is never shown as 0% or 100%.

Options you may need:

| Option | What it does |
|---|---|
| `--backend hf`, `jev` or `mock` | Choose who answers, instead of `JEV_BACKEND`. |
| `--split smoke tuning heldout` | Run only some of the sets. |
| `--data FILE...` | Use other files instead of everything in `evals/data/`. |
| `--json` | Print the report as JSON, for saving or comparing. |
| `--show-heldout-misses` | List the held-out set's misses (see below). |
| `--save NAME` | Keep the run in `evals/results/NAME.json` with its date, backend and model. Held-out misses are never saved. A name can be used once. |
| `--compare OLD NEW` | Compare two saved runs. No model runs. |
| `--coverage` | Check how many tickets each team, category and severity has against the [labeling guide](../evals/LABELING-GUIDE.md)'s minimums. No model runs. |

## What are the three sets?

- **Smoke set:** the first 8 tickets. Their label descriptions were adjusted after seeing the results, so they only catch breakage. They do not measure accuracy.
- **Tuning set:** tickets you may look at while editing label descriptions.
- **Held-out set:** tickets you never use while editing descriptions. Their accuracy is the fair number to report. The report hides their misses unless you ask, so you do not tune on them by accident. If you do tune on them, they stop being a fair test and you need a new held-out set.

The [labeling guide](../evals/LABELING-GUIDE.md) says how many tickets each set needs.

## How do I keep results from different stages?

Run with `--save` at each milestone, for example `--save baseline`, then `--save after-new-descriptions`. Later, `--compare baseline after-new-descriptions` shows the change in accuracy and macro-F1 for each question. It warns when the model or the set of tickets differs, because then the comparison is not fair.

Back to [how it works](architecture.md).
