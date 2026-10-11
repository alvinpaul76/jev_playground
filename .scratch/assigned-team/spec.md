# Assigned team in the ticket analysis API

Status: resolved
Period: 2026-10-11

## Why
`src/poc/ticket_analyis.py` gained a third question, `assigned_team` (which team should handle the ticket), a team label on each sample ticket, and an `unknown` category. The API had to follow.

## Decisions
- Team labels are **slugs** in the API (owner's choice): `backend`, `frontend`, `devops`, `security`, `product_management`, `tech_support`, `payments_financial_systems`. The script's exact strings ("product management", "payments & financial systems") are not used on the wire.
- `unknown` was **added to the categories** (owner's choice), giving the model a safe answer for vague tickets.
- `assigned_team` is an output with the same shape as the others (`{label, confidence}`), and is rejected as input (`extra="forbid"`), like `severity` and `category`.
- Adding a field to the response is not a breaking change for existing clients.

## Issues
01 assigned team in the API
