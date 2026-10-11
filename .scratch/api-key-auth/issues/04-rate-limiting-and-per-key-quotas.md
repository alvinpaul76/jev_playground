# 04 Rate limiting and per-key quotas

Status: resolved
Type: feature

Explicitly out of scope of the API-key work. Decide whether it is needed, and where it should live (proxy, middleware, or per-key counters). Per-key quotas would also need keys to be named (today they are anonymous
strings in a list) and probably hashed storage.

## Answer
2026-10-11: abuse protection only, handled at the edge by Cloudflare rate limiting rules. No code change, no per-key quotas.
- The API is exposed through Cloudflare, so a rate limiting rule on `/api/v1/*` (per IP, or per `X-API-Key` header if the plan allows) is enough.
- Lock the origin to Cloudflare (firewall to Cloudflare IP ranges, or a Cloudflare Tunnel), otherwise callers can bypass the limits.
- Set `FORWARDED_ALLOW_IPS` to the proxy's address (never `*`), so logs show the real client rather than the proxy (`docs/deployment.md`).
- Revisit if per-customer or per-period quotas are needed: that needs named keys, hashed storage and counters in the app.
