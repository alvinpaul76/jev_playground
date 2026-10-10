---
name: fastapi-documentation
description: "Generate or update the docs structure for a FastAPI service: a lean README landing page, docs/architecture.md for shared design, and one docs/apis/<feature>.md per router. Use when asked to document a FastAPI codebase, write API docs, or split a bloated README into per-API docs."
---

# FastAPI documentation

Produce this layout for the FastAPI service in the current repo:

```
README.md                 — lean landing page (≤ ~50 lines)
docs/
├── architecture.md       — shared design: layers, pipeline, errors, config
├── deployment.md         — ops: keys/secrets, backend selection, docker (skip if nothing to say)
└── apis/
    └── <feature>.md      — one per router group: the endpoint contract
```

## Process

### 1. Inventory the app

Find, via search not guesswork: the app factory (`create_app` / `FastAPI(...)`),
every `APIRouter` and `include_router` prefix chain, middleware, exception
handlers, lifespan/startup hooks, auth dependencies, and the settings/env-var
surface. Group routes by router — each mounted router is one `apis/<feature>.md`
later. Completion: a list of `{router, prefix, endpoints, auth}` covering every
route; cross-check `grep -rn "include_router\|APIRouter"` finds no orphan.

### 2. Write `docs/architecture.md` — shared things only

Sections: one-paragraph what-it-is; directory map; request pipeline (the order
middleware → auth → schema → domain → use case → adapter runs in); error
contract as a status/`code` table; config as an env-var table; startup/health;
test commands; "rules for new APIs" — the conventions the next module must
follow. Completion: no sentence in this file is true of only one endpoint —
anything per-endpoint moves to step 3.

### 3. Write `docs/apis/<feature>.md` per router group

Name the file after the feature, not the path. Template:

- Heading: what the API does in one sentence; method + path; auth required;
  source dir.
- Request: example JSON + field table (required, limits, defaults). Reuse the
  real limits from the schema/domain — cite the file they come from.
- Response: example JSON + semantics notes (ordering, units, soft values).
- Internals: one short section on the pipeline for this API (adapters, locking,
  prompt/state construction) — mechanism the endpoint contract can't show.
- Errors: only codes this endpoint adds; shared codes get a link to
  `architecture.md`, not a restatement.
- Links back: `[architecture](../architecture.md)`.

Completion: every route on that router is documented; every field limit cited
exists in the code.

### 4. Write `docs/deployment.md` only if ops detail exists

Secrets workflow (key generation, rotation, disable flags), backend/mode
selection commands, Docker/compose notes (build contexts, volumes, hardening,
env-file gotchas). If running the service is just `uv run <cmd>`, skip the file
entirely.

### 5. Rewrite README.md as the landing page

One-line description, quickstart (env copy + run command + one minimal curl),
test commands, docker one-liner, and a `## Docs` link list. Move detail into
docs/ — the README keeps nothing the linked docs carry.

### 6. Verify

- Walk every markdown link in the new files; each resolves to an existing file.
- Each fact lives in exactly one file — everywhere else links to it.
- README and architecture.md carry no per-endpoint detail; api docs carry no
  restated shared mechanism.

## Rules

- Facts live once. A constant restated in docs names its source file; never
  copy a value the code owns without the citation.
- Updating beats rewriting: if the docs exist, extend the per-API file or add a
  new one — regenerate shared docs only where the code changed them.
- `docs/` belongs in `.dockerignore` if the project has one.
