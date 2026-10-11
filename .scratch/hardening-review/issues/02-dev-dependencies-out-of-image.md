# 02 Keep test tooling out of the image

Status: resolved
Type: task

## Problem
`openjev[dev,hf]` is an extra, so `uv sync --no-dev` still installed `pytest`, `pluggy` and `iniconfig` into the production image.

## Fix
Depend on `openjev[hf]`; put `pytest` and `ruff` in `[dependency-groups] dev`. The project description placeholder was replaced.

## Verified by
The rebuilt image contains none of those packages.
