# 02 fastapi-standards: auth, settings, batch, adapters

Status: resolved
Type: task

`references/operations.md`: settings patterns (`SecretStr`, comma-list with `NoDecode`, strength checks, fail-closed in `create_app`, secure-default switches, `make_settings` helper); a static API-key
authentication pattern with the `CLIENT_API_KEYS` and `AUTH_ENABLED` table; batch endpoint rules; testing hosted adapters with `httpx.MockTransport`; entry points without a module-level `app`; root redirect.
`boundaries-and-data.md`: in-process model rules (lifespan, per-call lock, mock backend). `architecture.md`: hosted-vendor adapter rules. `review-checklist.md`: fail-closed and secure-default check.
