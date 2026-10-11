# 05 Redirect / to /docs

Status: resolved
Type: task

## Why
Opening `localhost:8000` showed `{"detail":"Not Found"}`, which looked like a failure.

## Built
`GET /` redirects (307) to `/docs` while `JEV_EXPOSE_DOCS=true`, needs no key, and is left out of the schema. With docs off, `/` is 404.

## Verified by
Two API tests (redirect target and no key; 404 when docs are off).
