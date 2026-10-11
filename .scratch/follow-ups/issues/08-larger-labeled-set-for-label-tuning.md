# 08 Larger labeled set to tune label descriptions

Status: needs-info
Type: research

## Context
Severity, category and team descriptions in `infrastructure/openjev_classifier.py` steer the model, but they were checked on only 8 sample tickets, and two team descriptions were adjusted after seeing results.
Triage found (2026-10-11): the old eval scripts never ran the production classifier; JEV-001 is deterministic for identical input and its confidence depends on which fields are sent (0.96 with full fields, about 0.55 with title and description only).

## Split by grilling
- [08a Eval harness for the production classifier](08a-eval-harness-for-the-production-classifier.md): resolved
- [08b Labeled set and labeling guide](08b-labeled-set-and-labeling-guide.md): needs-info (open questions Q2 to Q5, Q7)

This parent closes when 08b does.
