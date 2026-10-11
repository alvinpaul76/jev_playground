# API key authentication

Status: resolved
Period: 2026-10-10

## Why
The service ran open. Anyone who could reach port 8000 could use the CPU or the hosted Jev quota.

## Decisions (from the planning questions)
- **Scope:** everything under `/api/v1/*`; `/health/*` stays open for probes.
- **Keys:** a comma-separated list, so one can be rotated or each caller can have its own.
- **Header:** `X-API-Key`.
- **Names:** `JEV_CLIENT_API_KEYS` (callers to this service) is different from `JEV_API_KEY` (this service to hosted Jev).
- **Strength:** each client key is at least 32 characters.
- **Fail closed:** with auth on and no keys, the app refuses to start.
- **Out of scope:** rate limiting, per-key quotas, hashed key storage.

The approved plan is `/home/alvinpaul/.claude/plans/shimmying-popping-liskov.md` (outside the repo).

## Issues
01 require X-API-Key · 02 AUTH_ENABLED switch · 03 duplicate key in .env
04 rate limiting: handled by Cloudflare at the edge (abuse protection only), no per-key quotas
