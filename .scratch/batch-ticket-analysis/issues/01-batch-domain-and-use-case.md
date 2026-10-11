# 01 Batch domain and use case

Status: resolved
Type: task

## Built
- `Severity` (critical, high, medium, low, unknown) and `Category` (incident, security, ui, performance, financial_integrity, feature_request, regression, authentication) enums.
- `Ticket` value object with limits: id 64, title 200, description 10,000, environment 100, business_impact 2,000, evidence 20 items of 1,000 characters (`domain/entities.py`).
- `ensure_valid_batch`: 1 to 20 tickets, unique ids (`domain/policies.py`). New `InvalidBatch` error (`invalid_batch`, 422).
- Port `classify_many(tickets)`; use case `AnalyzeTickets`. Old escalation and frustration code was removed.

## Verified by
Unit tests for the domain and the use case (invalid batches never reach the classifier).
