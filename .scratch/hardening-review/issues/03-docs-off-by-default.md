# 03 Interactive docs off by default

Status: resolved
Type: task

## Fix
`expose_docs` defaults to `False`. Base `compose.yaml` uses `${JEV_EXPOSE_DOCS:-false}`; new `compose.override.yaml` sets it to `true` for local development (`docker compose up` merges it;
`docker compose -f compose.yaml up` does not). `.env.example` keeps `true` for development. Test settings turn docs on explicitly.

## Note
A `.env` that sets `JEV_EXPOSE_DOCS=true` still turns docs on, which is expected.
