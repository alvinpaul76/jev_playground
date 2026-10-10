# jev_playground

Stateless FastAPI service that classifies a batch of support tickets by severity and
category through OpenJev, using either a local model (`Qwen/Qwen2.5-0.5B-Instruct`) or the hosted Jev API.

## Run

```bash
cp .env.example .env   # then set JEV_CLIENT_API_KEYS (see Authentication)
uv run jev-playground
```

The model is loaded at startup (first run downloads it). `GET /health/ready`
returns 503 until loading finishes.

```bash
curl -X POST localhost:8000/api/v1/ticket-analyses \
  -H 'X-API-Key: <your key>' \
  -H 'Content-Type: application/json' \
  -d '{"tickets":[
        {"id":"JEV-001","title":"API returns HTTP 500 for all users",
         "description":"After deploying 2.4.1 every request returns 500.",
         "environment":"production",
         "business_impact":"All customers are unable to access the service.",
         "evidence":["Error rate went from 0.1% to 100% after deployment."]},
        {"id":"JEV-003","title":"Dashboard button is misaligned",
         "description":"Export CSV is 8px lower than Refresh in Chrome."}
      ]}'
```

Each ticket needs `id`, `title` and `description`; `environment`, `business_impact` and
`evidence` (a list of strings) are optional. `severity` and `category` are outputs, so
sending them is rejected with a 422.

Response:

```json
{"results": [{"id": "JEV-001",
              "severity": {"label": "critical", "confidence": 1.0},
              "category": {"label": "incident", "confidence": 0.93}}],
 "model": "jev-1.13.0", "latency_ms": 484.5}
```

- Severity is one of `critical|high|medium|low|unknown`. Category is one of `incident|security|ui|performance|financial_integrity|feature_request|regression|authentication`.
- `results` are in the same order as `tickets`. `latency_ms` covers the whole batch.
- A batch holds 1 to 20 tickets with unique ids. Text fields have length limits (description 10,000 characters).
- The batch is all or nothing: invalid input gets a 422 before any model call, and a classifier failure gets a 503 for the whole request. Tickets are classified one at a time, so a full batch on the local model takes a few seconds.

Errors are RFC 9457 `application/problem+json` with a stable `code`
(401 `unauthorized`, 422 `invalid_ticket` / `invalid_batch`, 503 `classifier_unavailable`, 500 `internal_error`).

## Authentication

Everything under `/api/v1/*` needs an `X-API-Key` header. `/health/*` stays open for probes, and `/` redirects to `/docs` while `JEV_EXPOSE_DOCS=true`.

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"   # generate a key
echo 'JEV_CLIENT_API_KEYS=<key1>,<key2>' >> .env               # comma-separated, 32+ chars each
```

- The app **refuses to start** with no keys configured, so a misconfigured deploy never runs open.
- To turn auth off for local development, set `JEV_AUTH_ENABLED=false`. Keys are then optional, `/api/v1/*` accepts any request, and a warning is logged at startup. The default is `true`; never disable it on a reachable host. `/docs` still shows the Authorize button, but the key is ignored.
- Rotate by adding the new key next to the old one, moving callers over, then removing the old one.
- `JEV_CLIENT_API_KEYS` are the keys *callers* use to reach this service. `JEV_API_KEY` is the unrelated key this service uses to reach the hosted Jev API.
- Wrong and missing keys get the identical 401 response. Rejections are logged without the key.
- Still not covered: rate limiting and per-key quotas.

## Choosing the backend

`JEV_BACKEND` selects what classifies tickets:

- `hf` (default): local `Qwen/Qwen2.5-0.5B-Instruct`, set by `JEV_MODEL_ID`.
- `jev`: the hosted Jev API at `JEV_BASE_URL`, authenticated with `JEV_API_KEY` (or `TYPESAFE_API_KEY`). The model is `JEV_JEV_MODEL` (default `jev-latest`). The app refuses to start without a key.

```bash
JEV_BACKEND=jev JEV_API_KEY=... uv run jev-playground
JEV_BACKEND=jev JEV_API_KEY=... docker compose up -d --force-recreate
```

The response `model` field shows which one answered. Keep the key in `.env` (git-ignored) or your shell, never in the image.

## Test

```bash
uv run pytest        # uses a fake classifier and OpenJev's mock backend; no model download
uv run ruff check . && uv run ruff format --check .
```

## Notes

- Layout: `modules/ticket_analysis/{domain,application,infrastructure,api}`; OpenJev is imported only in `infrastructure/`.
- Batch size (20) and the per-field length limits are domain constants in `domain/policies.py` and `domain/entities.py`.
- No rate limiting; `/docs` is on by default (`JEV_EXPOSE_DOCS=false` to disable). Fine for a PoC, not for exposure.
- `openjev` is a local path dependency (`../../tools/OpenJev`), which will break Docker builds.
- Small model: confidences can be low; callers should check them.

## Docker

```bash
docker compose up --build     # serves on 127.0.0.1:8000
```

- `compose.yaml` passes `../../tools/OpenJev` as a named build context (`openjev`), because the path dependency lives outside this repo. A plain `docker build` needs `--build-context openjev=../../tools/OpenJev`.
- Runs as uid 10001 with a read-only root filesystem, all capabilities dropped, and `/docs` disabled (`JEV_EXPOSE_DOCS=false`).
- Model weights are cached in the `hf-cache` volume (`HF_HOME=/models`), so only the first start downloads them. Set `FORWARDED_ALLOW_IPS` when behind a proxy.
- The image is about 6 GB because the lock file resolves CUDA builds of torch.
