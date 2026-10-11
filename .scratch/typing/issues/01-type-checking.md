# 01 Add a type checker

Status: resolved
Type: task

`pyproject.toml` has no ruff or type-checker configuration. Add a ruff section (current defaults are used implicitly) and mypy or Pyright, fix what it reports, and run it in CI (issue 02).

## Result
Commit `c0a7892`. Added `[tool.ruff]` and `[tool.mypy]` to `pyproject.toml`; mypy is a dev dependency, strict on `src`, relaxed on `tests` (no annotations required, bodies still checked). OpenJev has no `py.typed`, so `openjev.*` is ignored. Fixed the 18 findings and added `uv run mypy` to the CI test job. `mypy` clean on 45 files, 72 tests pass, ruff clean. Ruff rule selection is left at its defaults.
