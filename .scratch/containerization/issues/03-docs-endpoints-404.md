# 03 /docs and /redoc returned 404 in Docker

Status: resolved
Type: bug

## Cause
The image sets `JEV_EXPOSE_DOCS=false`, and `/redoc` was not following the setting.

## Fix
`docs_url`, `redoc_url` and `openapi_url` all follow `expose_docs`. Compose passes the setting through. Later the code default became `false` and
`compose.override.yaml` turns docs on for local development (hardening-review/03).

## Verified by
API tests for docs on and docs off; live check in the container.
