# 04 Hosted Jev backend option

Status: resolved
Type: task

## Why
The Qwen 0.5B model was not as capable as Jev. The service needed an option to use the hosted Jev (TypeSafe) API instead.

## Built
- `JEV_BACKEND` = `hf` (default), `jev`, or `mock` (tests only). One place reads it: `infrastructure/backends.py::build_backend`.
- `JevBackend` (httpx) calls `POST /v1/systemone` with a Bearer key and has the same `decide()` / `load()` surface as OpenJev backends, so nothing upstream changed.
- Settings: `JEV_API_KEY` (or `TYPESAFE_API_KEY`), `JEV_BASE_URL`, `JEV_JEV_MODEL`, `JEV_JEV_TIMEOUT_S`. `build_backend` refuses to start without a non-empty key.
- Wire-format findings: a `Choice` needs `criteria` (an `options`-only choice is not accepted); a `Score` is sent as a `criteria` list; null token counts in `usage` are dropped.

## Verified by
`httpx.MockTransport` tests (wire format, 401/429/500 become `ClassifierUnavailable`) and a live call (`jev-1.13.0`, 241 ms for the first call).

## Files
`infrastructure/jev_backend.py`, `infrastructure/backends.py`, `tests/integration/modules/ticket_analysis/test_jev_backend.py`
