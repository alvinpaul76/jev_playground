# 01 fastapi-docker: security scanning

Status: resolved
Type: task

New `references/security-scanning.md`: how to scan the built image (Trivy as a container, pinned to 0.75.0), a table that traces a finding to its source (OS package, lock file, pip's vendored copies),
standard fixes (remove pip, digest-pin bases, `apt-get upgrade`), CI gating (`--ignore-unfixed`, scheduled rebuilds) and a verify list. The example Dockerfile and `SKILL.md` checklist were updated, and
`compose.md` gained notes on re-reading `.env`, duplicate variables, and `:?` versus `:-`.

Incident: a placeholder in the new file was mangled once (`aquasec/trivy:yes d-version>`) in the repo copy; fixed and the two copies compared.
