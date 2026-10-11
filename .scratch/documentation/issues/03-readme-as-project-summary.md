# 03 README as the project summary

Status: resolved
Type: task

## Why
The README taught one API. The project is a FastAPI playground for testing Jev and building Jev-powered APIs.

## Built
README now has: purpose, "What is it for?", an **APIs** table (one row per `docs/apis/*.md`), get-running steps, tests, Docker, and doc links. No endpoint paths or request/response examples.
The skill and `check_docs.py` were updated so this cannot be missed: the checker fails if an API page is not linked from the README or if the README has no `## APIs` section, and warns about API examples in the README.
