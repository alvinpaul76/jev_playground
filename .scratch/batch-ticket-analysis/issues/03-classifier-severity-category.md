# 03 Classifier for severity and category

Status: resolved
Type: task

## Built
`OpenJevTicketClassifier.classify_many`: for each ticket, two `Choice` questions (severity, category). Every label has a one-line `criteria` description, which the hosted API requires and which also
helps a small model. The prompt state contains only `id`, `title`, `description` and the optional fields, never labels. One `decide()` per ticket under the lock; `latency_ms` is wall time for the batch.

## Verified by
Mock-backend tests (order, state contents, error translation) and `httpx.MockTransport` tests (wire format). Live hosted run: JEV-001 critical / incident, JEV-003 low / ui.
