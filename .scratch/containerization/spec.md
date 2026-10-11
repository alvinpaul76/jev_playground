# Containerization

Status: resolved
Period: 2026-10-09 to 2026-10-10

## Why
Run the service the same way everywhere: small image, non-root, no secrets in the image, reproducible builds. Followed the
`fastapi-docker` skill.

## Decisions
- `openjev` is a path dependency outside this repo (`../../tools/OpenJev`), so the build uses a **named build context** and mirrors the directory layout.
- Torch is the CPU build (smaller, enough for a 0.5B model).
- Docs are off in the image unless asked for (see 03 and hardening-review/03).
- Images are scanned with Trivy; findings with a fix are fixed (issue 04). Unfixed ones are accepted and watched by the weekly CI rescan (issue 05).

## Issues
01 multi-stage Dockerfile and compose · 02 CPU-only torch · 03 docs endpoints · 04 image vulnerability fixes · 05 unfixed Debian findings (accepted) · 06 deployment-only variables in .env.example (kept, commented)
