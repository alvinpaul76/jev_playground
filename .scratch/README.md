# Work log and open items

Local issue tracker (see `docs/agents/issue-tracker.md`). Each folder is one feature: `spec.md` records the why and the decisions, `issues/NN-*.md` are the pieces of work.
`Status: resolved` means done and verified; other statuses are triage roles from `docs/agents/triage-labels.md`.

Period covered: 2026-10-09 to 2026-10-11. State at the end: 123 tests passing, ruff clean, image scan clean. Committed in this repo as `df15350`, `34ecf10`, `7e235fe` and `c0a7892`.

| Feature | What it covers | Status |
|---|---|---|
| [ticket-analysis-service](ticket-analysis-service/spec.md) | Layered FastAPI service, OpenJev adapter, errors and health, hosted Jev backend | resolved |
| [containerization](containerization/spec.md) | Dockerfile, compose, CPU torch, docs 404, image vulnerability fixes | resolved |
| [api-key-auth](api-key-auth/spec.md) | `X-API-Key` on `/api/v1/*`, `JEV_AUTH_ENABLED`, duplicate-key diagnosis | resolved |
| [batch-ticket-analysis](batch-ticket-analysis/spec.md) | Several tickets per request, severity and category | resolved |
| [assigned-team](assigned-team/spec.md) | Third question: which team should handle the ticket; `unknown` category | resolved |
| [hardening-review](hardening-review/spec.md) | Seven review findings fixed | resolved |
| [documentation](documentation/spec.md) | Plain-language docs, README as project summary | resolved |
| [agent-skills](agent-skills/spec.md) | Skill updates in the separate skills repo | resolved |
| [ci](ci/spec.md) | GitHub Actions: pytest, ruff, image build and Trivy scan, weekly rescan | resolved |
| [label-evaluation](label-evaluation/spec.md) | Eval harness, labeling guide, 30 labeled tickets, metrics, tuned severity descriptions, model choice (stay hosted) | resolved |
| [typing](typing/spec.md) | mypy, explicit ruff config, `Backend` Protocol | resolved |

## Open items
None.
