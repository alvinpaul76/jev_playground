# Batch ticket analysis (severity and category)

Status: resolved
Period: 2026-10-10

## Why
The scratch script changed: it now takes several tickets (id, title, description, environment, severity, category, business_impact, evidence) and classifies **severity** and
**category**. The API had to follow.

## Decisions
- **Replace** the old single-ticket department/urgency/frustration endpoint in v1 (no consumer depended on it).
- Optional free-form fields: `environment`, `business_impact`, `evidence`. Required: `id`, `title`, `description`.
- `severity` and `category` are **outputs**; sending them is rejected (`extra="forbid"`), so a label cannot leak into the prompt.
- **All or nothing:** invalid input is a 422 before any model call; a classifier failure is a 503 for the whole request.
- Batch of 1 to 20 tickets, unique ids, results in input order.
- Sync route; the model is called one ticket at a time under the lock.

## Contract
`POST /api/v1/ticket-analyses` with `{"tickets": [...]}` returns `{"results": [{id, severity{label,confidence}, category{label,confidence}}], model, latency_ms}`. Full detail: `docs/apis/ticket-analysis.md`.

## Issues
01 domain and use case · 02 API and schemas · 03 classifier questions · 04 eval script
