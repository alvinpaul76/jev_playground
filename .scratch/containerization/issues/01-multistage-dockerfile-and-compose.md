# 01 Multi-stage Dockerfile and compose file

Status: resolved
Type: task

## Built
- `Dockerfile`: builder and runtime stages on `python:3.14-slim-trixie`; `uv sync --locked --no-editable`; OpenJev supplied as build context `openjev`
  at `/build/tools/OpenJev` (project at `/build/poc/jev_playground`); runtime copies only the venv.
- Runtime: non-root uid/gid 10001, `EXPOSE 8000`, liveness `HEALTHCHECK` using the standard library, exec-form uvicorn with `--proxy-headers`,
  `--forwarded-allow-ips` (default `127.0.0.1`), and `--timeout-graceful-shutdown 20`.
- `compose.yaml`: port bound to `127.0.0.1:8000`, `read_only`, `tmpfs /tmp`, `cap_drop: ALL`, `no-new-privileges`, `mem_limit: 4g`, `cpus: 4`,
  volume `hf-cache` at `/models` for model weights.
- `.dockerignore` keeps `.env`, `.git`, tests and docs out of the build.

## Files
`Dockerfile`, `compose.yaml`, `.dockerignore`
