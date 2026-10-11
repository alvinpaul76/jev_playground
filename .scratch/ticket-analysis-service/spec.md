# Ticket analysis service

Status: resolved
Period: 2026-10-09 to 2026-10-10

## Why
`src/jev_playground/ticket_analyis.py` (now `evals/triage_eval.py`) was a scratch script that
classified tickets with OpenJev. The goal was to turn it into a stateless, fully layered FastAPI
service that follows the `fastapi-standards` skill. The original plan was written in
`ticket_analysis.md`.

## Decisions
Answers given to the planning questions (c / a / a / b):
- **Structure:** full layered (domain, application, infrastructure, api) inside `modules/ticket_analysis/`.
- **Persistence:** none. The service is stateless; no SQLAlchemy or Alembic.
- **API:** one `POST` plus health endpoints; clients cannot configure questions.
- **Backend:** Hugging Face `Qwen/Qwen2.5-0.5B-Instruct` first. A backend switch was added later (issue 04).

The first version classified department, urgency and frustration. That output was replaced by
severity and category in [batch-ticket-analysis](../batch-ticket-analysis/spec.md).

## Layout (after all work)
`api/` shared transport (router, security, errors, limits, health) · `modules/ticket_analysis/{domain,application,infrastructure,api}` ·
`config.py` · `lifespan.py` · `main.py` (`create_app`) · `tests/{unit,integration,api}`. See `docs/architecture.md`.

## Issues
01 domain and application · 02 OpenJev adapter · 03 app factory, errors, health · 04 hosted Jev backend · 05 root redirect
