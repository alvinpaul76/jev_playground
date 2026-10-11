# 08 Larger labeled set to tune label descriptions

Status: needs-triage
Type: research

## Context
Severity, category and team descriptions in `infrastructure/openjev_classifier.py` steer the model, but they were checked on only 8 sample tickets, and two team descriptions were adjusted after seeing results.
JEV-001 is still assigned to `backend` (confidence about 0.4 to 0.96 across runs) instead of `devops`.

## Done when
There are at least 30 labeled tickets (kept separate from the ones used to write descriptions), accuracy per question is reported, and `evals/triage_eval.py` and `src/poc/ticket_analyis.py` are no longer two copies of the same script.
