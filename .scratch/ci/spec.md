# CI

Status: resolved
Period: 2026-10-11

## Why
There was no CI. Tests, lint and the image scan only ran when someone remembered to run them, and new CVEs appear against unchanged images.

## Decisions
- One workflow, `.github/workflows/ci.yaml`, with a test-and-lint job and an image-scan job.
- `openjev` is a path dependency outside this repo, so CI checks it out at a pinned commit into `tools/OpenJev` and mirrors the layout.
- The scan gates on fixable HIGH and CRITICAL findings only. The unfixed backlog is tracked in containerization/05.
- A weekly scheduled run rebuilds without cache.

## Issues
01 CI for tests, lint and image scan
