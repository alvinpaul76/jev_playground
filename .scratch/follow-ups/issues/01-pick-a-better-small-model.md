# 01 Pick a better small model than Qwen 0.5B

Status: needs-triage
Type: research

## Context
Qwen2.5-0.5B is much weaker than Jev (low and unstable confidences). Recommendations were given in conversation but no decision was made.

## Options
- Write a comparison script over the 8 labeled sample tickets (`evals/triage_eval.py` is the base) and run several candidate models.
- Try Qwen3-1.7B, which needs a higher `mem_limit` than 4 GB in `compose.yaml`.
- Keep Qwen for tests and use `JEV_BACKEND=jev` for real use.

## Done when
A model is chosen with accuracy numbers, or the decision is recorded to stay with the hosted backend.
