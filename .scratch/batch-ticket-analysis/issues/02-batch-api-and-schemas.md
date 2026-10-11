# 02 Batch API and schemas

Status: resolved
Type: task

## Built
- `AnalyzeTicketsRequest` (`tickets`, 1 to 20) and `TicketIn` with `extra="forbid"`, limits taken from the domain constants. Response built by `AnalyzeTicketsResponse.from_result`.
- Thin route `analyze_tickets` (later with `TicketIn.to_domain()` instead of mapping in the route).
- README and tests rewritten for the batch contract.

## Verified by
API tests: order preserved, empty and oversized batches, duplicate ids, blank title (`invalid_ticket`), labels rejected as input, old `{"ticket": ...}` shape rejected, 503, generic 500. Total 59 passing.
