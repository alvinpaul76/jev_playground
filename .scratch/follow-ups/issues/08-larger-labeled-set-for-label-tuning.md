# 08 Larger labeled set to tune label descriptions

Status: resolved
Type: research

## Context
Severity, category and team descriptions in `infrastructure/openjev_classifier.py` steer the model, but they were checked on only 8 sample tickets, and two team descriptions were adjusted after seeing results.
Triage found (2026-10-11): the old eval scripts never ran the production classifier; JEV-001 is deterministic for identical input and its confidence depends on which fields are sent (0.96 with full fields, about 0.55 with title and description only).

## Split by grilling
- [08a Eval harness for the production classifier](08a-eval-harness-for-the-production-classifier.md): resolved
- [08b Labeled set and labeling guide](08b-labeled-set-and-labeling-guide.md): resolved

- [08c Report the metrics the labeling guide requires](08c-report-the-metrics-the-labeling-guide-requires.md): resolved

This parent closed when 08b and 08c did.

## Resolution (2026-10-11)
The harness (08a), the metrics (08c) and the labeled set (08b) exist. The severity descriptions were rewritten from the labeling guide using the tuning set only: tuning severity 44% -> 78% -> 89% (the last step is a relabel), held-out severity 38% -> 62%. Category and team descriptions were left alone (100% tuning, 94% held-out). The held-out set has been used once; a new one is needed before another tuning round. Choosing a better small model continues in 01.
