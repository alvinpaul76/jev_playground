# Measuring label accuracy

Use this page to check how often the service's labels match what a person decided. It is for whoever tunes the label descriptions or compares models.

New to a word? See the [word list](glossary.md).

## Why measure?

The service labels each ticket with a severity, a category and a team. Without a check, a change to a label description might make some answers better and others worse, and nobody would know. The check runs the same code path the API uses and compares its answers with labels a person chose.

## What do I need?

A set of tickets with **expected labels**: the answers a person decided are right. They live in the files `evals/data/*.jsonl`, which hold one ticket per line, written as JSON (see the [word list](glossary.md)). The rules for deciding those labels are in the [labeling guide](../evals/LABELING-GUIDE.md), which also covers the file format, the number of tickets, and how they are spread.

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
3. Read the report. This one is from a real run against the hosted service, shortened to the parts that matter:
   ```
   model: jev-1.13.0   classification time: 2934.31 ms

   == tuning (12 tickets, 3 ambiguous (25%) excluded)
      missing predictions: 0 (failed 0, absent 0)
      severity       7/9  78%   macro-F1 76% (3 of 3 labels)
      category       9/9  100%   macro-F1 100% (6 of 8 labels)
      assigned_team  9/9  100%   macro-F1 100% (5 of 6 labels)
      expected labels:
        severity: high 6, low 2, medium 4
      unknown expected: severity 0%, category 0%
      per label (precision / recall / F1 / expected):
        severity.high: 100% / 75% / 86% / 4
        severity.low: 100% / 50% / 67% / 2
      misses:
        HW-024 severity: expected=high predicted=medium (confidence 0.46)
   ```
   Read it from the top:
   - **Tickets and ambiguous:** how many tickets are in the set, and how many are *ambiguous* (the person labeling could not decide). Ambiguous tickets are left out of every score below.
   - **Missing predictions:** tickets the model gave no answer for. *Failed* means the service rejected the ticket even when sent on its own. *Absent* means it answered but left the ticket out. A missing prediction counts as wrong. It is never dropped.
   - **Unknown expected:** the share of tickets whose correct label is `unknown`. A set with none cannot show whether the model admits when it does not know.
   - **Accuracy:** each question line shows how many tickets got the expected label, then the percentage.
   - **Macro-F1:** one score per question that treats every label equally, so a rare label counts as much as a common one. It is worked out from the per-label *precision*, *recall* and *F1*, and it only averages labels that have an F1. The brackets say how many labels that was, out of how many labels have tickets. A model that never gives a hard label is left out of the average, so read macro-F1 together with the per-label lines.
   - **Per label:** *precision* is how often the model is right when it says this label. *Recall* is how many of the tickets that should have this label it found. *F1* combines the two. The last number is how many tickets should have the label.
   - **Misses:** the expected label, the model's label, and how sure the model was.

   A figure shows as `unavailable` when it cannot be worked out, for example precision for a label the model never gave. It is never shown as 0% or 100%.

Options you may need:

| Option | What it does |
|---|---|
| `--backend hf`, `jev` or `mock` | Choose who answers, instead of `JEV_BACKEND`. |
| `--split smoke tuning heldout` | Run only some of the sets. |
| `--data FILE...` | Use other files instead of everything in `evals/data/`. |
| `--json` | Print the report as JSON, for saving or comparing. |
| `--show-heldout-misses` | List the held-out set's misses (see below). |
| `--save NAME` | Keep the run as a *milestone*: `evals/results/NAME.json`, with its date, backend and model. Held-out misses are never saved. A name can be used once. |
| `--compare OLD NEW` | Compare two saved runs: accuracy, macro-F1, missing predictions, and every label whose F1 changed. No model runs. |
| `--coverage` | Check how many tickets each team, category and severity has against the [labeling guide](../evals/LABELING-GUIDE.md)'s minimums. The guide asks for "about 5" difficult cases, so 4 passes. No model runs. |

## What are the three sets?

- **Smoke set:** the first 8 tickets. Their label descriptions were adjusted after seeing the results, so they only catch breakage. They do not measure accuracy.
- **Tuning set:** tickets you may look at while editing label descriptions.
- **Held-out set:** tickets you never use while editing descriptions. Their accuracy is the fair number to report. The report hides their misses unless you ask, so you do not tune on them by accident. If you do tune on them, they stop being a fair test and you need a new held-out set.

The [labeling guide](../evals/LABELING-GUIDE.md) says how many tickets each set needs.

## How do I keep results from different stages?

Run with `--save` at each milestone, for example `--save baseline`, then `--save after-new-descriptions`. Later, `--compare baseline after-new-descriptions` shows the change in accuracy and macro-F1 for each question. It warns when the model or the set of tickets differs, because then the comparison is not fair.

Back to [how it works](architecture.md).
