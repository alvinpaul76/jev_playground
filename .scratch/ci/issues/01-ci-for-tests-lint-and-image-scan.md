# 01 CI for tests, lint and image scan

Status: resolved
Type: task

There is no CI. Add a pipeline that runs `uv run pytest`, `ruff check` and `ruff format --check`, builds the image (named build context `openjev`), and scans it with Trivy `--ignore-unfixed --exit-code 1`
for HIGH and CRITICAL. Add a weekly scheduled rebuild and scan, because new CVEs appear against unchanged images. The `fastapi-docker` skill's `security-scanning.md` has the commands.

## Done when
A pull request runs all four checks and the scheduled job exists.

## Result
Added `.github/workflows/ci.yaml` (commit `7e235fe`). Pull requests, pushes to `main` and `develop`, and a weekly cron (Mondays 06:00 UTC) run two jobs:
- `test-and-lint`: `uv run pytest`, `ruff check`, `ruff format --check`.
- `image-scan`: builds with `--build-context openjev=...`, then Trivy v0.75.0 (`--ignore-unfixed --exit-code 1`, HIGH and CRITICAL, vuln only). The scheduled run builds with `no-cache` and `pull` so it picks up new base-image patches.

Locally verified: 72 tests pass, ruff clean, workflow YAML parses. Not yet verified: the first run on GitHub (OpenJev checkout from `GPT-AGI/OpenJev`, assumed public, and the image build and scan).
Not done, by choice: a second non-gating scan for the unfixed backlog (see containerization/05); actions are tag-pinned, not SHA-pinned.
