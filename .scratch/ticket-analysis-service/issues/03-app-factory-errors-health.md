# 03 App factory, error contract and health

Status: resolved
Type: task

## Built
- `create_app(settings)` (no module-level `app`, because startup validates configuration and would crash on import). `main()` runs
  `uvicorn.run("jev_playground.main:create_app", factory=True, ...)`.
- `lifespan.py`: build the backend once, `backend.load()`, set `model_ready`. `/health/live` is always 200; `/health/ready` is 503 until loaded.
- Errors are RFC 9457 `application/problem+json` with a stable `code` and a `request_id`; `RequestIdMiddleware` also turns unhandled
  exceptions into a generic, logged 500. Domain errors carry no HTTP status; `api/errors.py` maps them (`InvalidTicket` 422, `ClassifierUnavailable` 503).
- Settings in `config.py` (`pydantic-settings`, prefix `JEV_`).

## Files
`main.py`, `lifespan.py`, `config.py`, `api/errors.py`, `api/health.py`, `api/router.py`
