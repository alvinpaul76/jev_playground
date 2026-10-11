# 02 OpenJev adapter

Status: resolved
Type: task

## What
Infrastructure adapter that turns a ticket into an OpenJev `SystemOneRequest` and maps the answer back to domain types.

## Built
- `infrastructure/openjev_classifier.py`: `Choice` / `Noul` / `Score` questions, answers clamped to valid ranges, a `threading.Lock`
  around `backend.decide()` (HF inference is not thread-safe and sync routes run in a thread pool), vendor errors translated to `ClassifierUnavailable`.
- Facts learned: the HF backend scores only the first token of each label, and runs float32 on CPU.
- Tests use OpenJev's deterministic `mock` backend, so no model is downloaded.

## Files
`modules/ticket_analysis/infrastructure/openjev_classifier.py`, `tests/integration/modules/ticket_analysis/test_openjev_classifier.py`
