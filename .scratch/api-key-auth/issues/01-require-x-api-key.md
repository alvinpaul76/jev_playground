# 01 Require X-API-Key on /api/v1/*

Status: resolved
Type: task

## Built
- `api/security.py`: `APIKeyHeader(name="X-API-Key", auto_error=False)`; `require_api_key` compares against every configured key with
  `secrets.compare_digest` and no early exit; rejections are logged with request id and client address, never the key.
- `api/errors.py`: `Unauthorized` (an API-layer exception, not a `DomainError`) maps to 401 problem+json `unauthorized` with `WWW-Authenticate: ApiKey`.
  A missing key and a wrong key get identical answers.
- `api/v1/router.py`: the key check is a router-level dependency, so new routes are protected without per-route code.
- `config.py`: `client_api_keys` parsed from a comma list (`NoDecode` plus a validator) with the 32-character minimum.
- `main.py`: `create_app` raises `RuntimeError` naming `JEV_CLIENT_API_KEYS` when no keys are set.
- `compose.yaml`, `.env.example` and the README were updated.

## Verified by
10 new tests in `tests/api/test_auth.py` (missing and wrong key, valid key, rotation, auth before validation, open health, OpenAPI scheme, startup refusal,
short key, comma parsing). Existing route tests were switched to a `make_settings()` helper and send the key. Total 52 passing. Docker check: 401 without a key, 200 with one, health open.
