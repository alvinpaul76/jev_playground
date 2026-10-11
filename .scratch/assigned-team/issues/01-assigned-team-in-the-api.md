# 01 Assigned team in the API

Status: resolved
Type: task

## Built
- Domain: `Team` enum; `Category.UNKNOWN`; `TicketAnalysis` gained `assigned_team` and `assigned_team_confidence`.
- Classifier: a third `Choice` question `assigned_team` with a one-line `criteria` description per team (the hosted API requires `criteria`). Category `unknown` has a description too.
- API: `TicketAnalysisOut.assigned_team`; input field rejected with 422.
- `evals/triage_eval.py` re-synced from `src/poc/ticket_analyis.py` (the owner's script, left untouched).
- Docs: API page (example answer from the running container, label table, three questions), architecture, README APIs row, glossary entry.

## Verified by
75 tests passing (72 before): team slugs, `unknown` category, wire format with the third question, `assigned_team` rejected as input, field present in answers. Live, hosted backend, 8 sample tickets with labels stripped:
severity 7/8, category 8/8, team 7/8. The one team miss is JEV-001 (backend instead of devops).

## Caveat
Two team descriptions (devops, product_management) were reworded after the first run (team 6/8 to 7/8). With only 8 samples, treat these numbers as a smoke test, not a benchmark. See label-evaluation/08.

## Files
`domain/value_objects.py`, `domain/entities.py`, `infrastructure/openjev_classifier.py`, `api/schemas.py`, matching tests, `evals/triage_eval.py`, `docs/`.
