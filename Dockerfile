# syntax=docker/dockerfile:1.7
#
# Build (OpenJev is a local path dependency outside this directory, so it is
# supplied as a named build context; compose.yaml does this for you):
#   docker build --build-context openjev=../../tools/OpenJev -t jev-playground:$(git rev-parse --short HEAD) .

# Refresh the pinned digests periodically (and rebuild to pick up patches):
#   docker buildx imagetools inspect python:3.14-slim-trixie

# ---- builder -------------------------------------------------------------
FROM python:3.14-slim-trixie@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

COPY --from=ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 /uv /usr/local/bin/uv

# pyproject.toml resolves openjev at ../../tools/OpenJev; mirror that layout.
WORKDIR /build/tools/OpenJev
COPY --from=openjev pyproject.toml README.md ./
COPY --from=openjev src ./src

WORKDIR /build/poc/jev_playground

# Dependencies first so code changes do not invalidate this layer.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-install-project --no-dev

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

# ---- runtime -------------------------------------------------------------
FROM python:3.14-slim-trixie@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/models \
    JEV_EXPOSE_DOCS=false

# The digest pins the base image, so OS patches since then are applied here. pip is removed
# because nothing installs packages at runtime and its vendored libraries trigger CVE scanners.
RUN apt-get update \
 && apt-get upgrade --yes --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* \
 && rm -rf /usr/local/lib/python3.14/site-packages/pip* /usr/local/bin/pip* \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
 && install -d -o 10001 -g 10001 /models

# The project is installed into the venv (--no-editable), so only the venv is needed.
COPY --from=builder /opt/venv /opt/venv

WORKDIR /srv
USER 10001:10001

EXPOSE 8000

# Model loading at startup is slow, hence the long start period. Liveness only.
HEALTHCHECK --interval=30s --timeout=3s --start-period=180s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status == 200 else 1)"]

CMD ["sh", "-c", "exec uvicorn jev_playground.main:create_app --factory --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=\"${FORWARDED_ALLOW_IPS:-127.0.0.1}\" --timeout-graceful-shutdown 20"]
