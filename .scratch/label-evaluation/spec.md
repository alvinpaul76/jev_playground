# Label evaluation

Status: resolved
Period: 2026-10-11

## Why
The severity, category and team descriptions steer the model, but they were checked on only 8 sample tickets, and some were adjusted after seeing the results. Accuracy could not be reported fairly.

## What was built
- An eval harness that runs the production classifier on labeled tickets, with a tuning set and a held-out set kept apart (08a).
- A labeling guide and 30 hand-labeled tickets: 12 tuning, 18 held-out (08b).
- The metrics the guide asks for, saved milestone runs and a coverage view (08c).
- Severity descriptions rewritten from the guide, using the tuning set only (08, parent).

## Results
Saved in `evals/results/`, hosted Jev model `jev-1.13.0`:
- Tuning severity 44% -> 78%, then 89% after the owner relabeled HW-024.
- Held-out severity 38% -> 62%; category and team 94%, unchanged.

## Decisions
- A person decides every expected label; a model never labels its own test set.
- Held-out results are never used to edit descriptions. The held-out set has been used once, so another tuning round needs a fresh one.
- Issue numbers keep their original `08` prefix (they appear in commits and tests).

## Issues
See `issues/`. Choosing a better small model continues in [follow-ups 01](../follow-ups/issues/01-pick-a-better-small-model.md).
