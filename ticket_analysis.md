---
agent: devin-local
session: malleable-dormouse
created: 2026-10-09T04:15:20Z
---
# Ticket analysis FastAPI service (fastapi-standards, full layered)

Turn the `ticket_analyis.py` script into a stateless, full-layered FastAPI service that classifies a support ticket (department, urgency, frustration) via the OpenJev HF backend, following the `fastapi-standards` skill.

## Decisions (from your answers: c / a / a / b)
Interpreted as the lettered options in order:
- **Structure: full layered** (domain / application / infrastructure / api split in a feature module).
- **Persistence: none** (stateless, no SQLAlchemy/Alembic).
- **API: single POST** + health endpoints (no client-configurable questions).
- **Backend: hardcoded HF `Qwen/Qwen2.5-0.5B-Instruct`** (no backend switch). The model id is a plain default in `Settings`. Tests never load it because they use a fake classifier port and OpenJev's `mock` backend.

Tell me if I misread any letter.

## Layout (`src/jev_playground/`)
```
main.py                  # create_app(settings) + app = create_app()
config.py                # Settings (pydantic-settings): model_id, expose_docs, log_level
lifespan.py              # builds OpenJev HFBackend once, warms with backend.load(), stores on app.state
api/
  router.py              # root router, mounts /api and health
  health.py              # GET /health/live, /health/ready (ready = model loaded)
  dependencies.py        # shared Annotated aliases
  errors.py              # DomainError -> RFC 9457 problem+json, generic 500 handler, request-id middleware
  v1/router.py
modules/ticket_analysis/
  domain/
    value_objects.py     # TicketText (non-empty, max 10_000 chars), Department enum (billing/technical/sales), Probability, FrustrationScore
    entities.py          # TicketAnalysis (department + confidence, urgency probability, frustration score)
    policies.py          # EscalationPolicy (urgent prob >= threshold), FrustrationLevel mapping (calm/annoyed/furious)
    errors.py            # DomainError base (code/title/public_message), InvalidTicket, ClassifierUnavailable
  application/
    dto.py               # AnalyzeTicketInput / AnalyzeTicketResult
    ports.py             # TicketClassifier Protocol (classify(TicketText) -> RawClassification)
    use_cases/analyze_ticket.py   # validates via domain, calls port, applies policies, returns result
  infrastructure/
    openjev_classifier.py         # adapter: builds SystemOneRequest with Choice/Noul/Score, maps response -> domain types, threading.Lock, translates vendor errors -> ClassifierUnavailable
  api/
    schemas.py           # AnalyzeTicketRequest (extra="forbid", 1..10_000 chars), TicketAnalysisResponse.from_result
    routes.py            # POST /ticket-analyses (sync def, thin, no try/except)
    dependencies.py      # get_classifier (from app.state), get_analyze_ticket_use_case
tests/
  unit/modules/ticket_analysis/   # test_policies.py, test_value_objects.py, test_analyze_ticket.py (fake classifier)
  integration/modules/ticket_analysis/test_openjev_classifier.py  # adapter + openjev mock backend
  api/test_ticket_analyses_routes.py  # TestClient, dependency_overrides, error mapping, health
  conftest.py
```
Domain imports no FastAPI/OpenJev/Pydantic transport types (rule 2). OpenJev is imported only in `infrastructure/`.

## Behaviour
- `POST /api/v1/ticket-analyses` body `{"ticket": "..."}` -> 200 with:
  `department {name, confidence}`, `urgent {probability, requires_escalation}`, `frustration {score, level, confidence}`, `model`, `latency_ms`.
- Error mapping: empty/oversized ticket -> 422 (FastAPI validation + `InvalidTicket` domain check); classifier failure -> 503 problem+json with stable `code`; unexpected -> generic 500 logged with request id.
- Sync `def` route and sync adapter (`backend.decide` blocks); FastAPI runs it in the thread pool. A lock in the adapter serializes model calls since HF inference is not guaranteed thread-safe.
- Model loaded once in lifespan (not at import); `/health/ready` reports false until loaded.
- Escalation threshold and frustration level mapping are domain constants, not env vars (section 13).

## Dependencies / config
- `uv add fastapi "uvicorn[standard]" pydantic-settings` (pick versions published >= 7 days ago); `httpx` and `pytest` are already present (via openjev `dev` extra / transitive).
- Add `.env.example` (placeholders only), ruff config reuse from existing project.
- `pyproject.toml`: point `jev-playground` script at a `main()` in `jev_playground/__init__.py` that runs `uvicorn.run("jev_playground.main:app")`; add pytest `testpaths`.
- Keep `ticket_analyis.py` untouched as a scratch script (can delete later on request).
- README: how to run (`uv run jev-playground`), test, and sample curl.

## Implementation order (standards section 25)
1. Domain value objects, entities, policies, errors + unit tests.
2. Application DTOs, port, use case + unit tests with a fake classifier.
3. OpenJev adapter + integration test with `get_backend("mock")`.
4. Settings, lifespan, app factory, error handlers, health.
5. Schemas, route, dependency wiring + API tests.
6. Add deps, script entry, README, `.env.example`.

## Verification
- `uv run pytest` (unit, integration with mock backend, API with overrides; none download the model).
- `uv run ruff check . && uv run ruff format --check .`
- Manual: `uv run jev-playground`, then `curl -X POST localhost:8000/api/v1/ticket-analyses -H 'Content-Type: application/json' -d '{"ticket":"Stripe integration failed for 3 days, payments down"}'` (downloads/loads Qwen on first start); check `/health/ready`.

## Risks / notes
- **Model quality:** the earlier script run classified the Stripe ticket as `billing 0.07`, i.e. low confidence; Qwen 0.5B is weak. The API will surface confidence so callers can judge.
- **Startup time / memory:** loading torch + Qwen at startup is slow; readiness endpoint covers this.
- **No auth/rate limiting** was requested; section 14 recommends them for anything beyond a PoC. I will leave `/docs` enabled by default via `expose_docs` and note this in the README.
- **Local path dependency** on `../../tools/OpenJev` remains (from the earlier fix), which breaks Docker builds; out of scope here but relevant if `fastapi-docker` is applied later.
- If a standard conflicts with your preference (e.g. hardcoded backend vs settings-driven), I follow you and note the trade-off.
