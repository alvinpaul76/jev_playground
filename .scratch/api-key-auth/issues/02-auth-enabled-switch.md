# 02 JEV_AUTH_ENABLED switch

Status: resolved
Type: task

## Why
Request: a way to turn the API-key check on or off with an environment variable.

## Built
- `auth_enabled: bool = True`. Off: `require_api_key` returns immediately, keys become optional, and `create_app` logs a WARNING that `/api/v1/*` is open.
  On: unchanged, including the startup refusal with no keys.
- `compose.yaml`: `${JEV_AUTH_ENABLED:-true}` and `${JEV_CLIENT_API_KEYS:-}`. The old `:?` on the keys was removed because it would block a deliberate `false`;
  the app's own startup check enforces the keys instead.
- Known limit: with auth off, `/docs` still shows the Authorize button (the key is ignored).

## Verified by
5 new tests (open without key, starts without keys and logs the warning, body still validated, default is true, parsed from env). Total 57 passing.
