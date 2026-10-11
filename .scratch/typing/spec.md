# Typing

Status: resolved
Period: 2026-10-11

## Why
No type checker and no explicit ruff config; backends were typed only by convention.

## Decisions
- mypy (strict on `src`, relaxed on `tests`) plus an explicit ruff section at default rules.
- OpenJev is untyped, so its imports are ignored rather than stubbed.
- The classifier depends on `Decider`; `Backend` is for code that also loads and names it.

## Issues
01 type checking · 02 backend protocol typing
