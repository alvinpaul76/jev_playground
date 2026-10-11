# Hardening review

Status: resolved
Period: 2026-10-10

## Why
Review of the app against the updated `fastapi-standards` and `fastapi-docker` skills. No blockers among the seven non-negotiable rules; seven "should fix" findings, each verified by running it
before it was fixed. Layering was confirmed clean (domain and application import no framework or vendor code).

## Result
All seven fixed. 72 tests passing, ruff clean, image scan clean, image 1.19 GB. Suggestions that were not done became [label-evaluation](../label-evaluation/spec.md).

## Issues
01 single classifier instance · 02 dev dependencies out of the image · 03 docs off by default · 04 documented errors · 05 request size limit · 06 request id validation
