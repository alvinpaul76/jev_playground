# jev_playground

A FastAPI playground for testing Jev and building Jev-powered APIs. Each API lives in its own feature folder and has its own page in the docs. The shared parts (key check, error format, health checks, settings) are reused by every API.

## What is it for?
- Try Jev behind a real web API, using a small local model or the hosted Jev service.
- Build a new Jev-powered API by adding a feature folder. [How it works](docs/architecture.md#rules-for-adding-a-new-api) lists the rules.
- Experiment safely: every API needs a key and has size limits.

## APIs
| API | What it does | Docs |
|---|---|---|
| Ticket analysis | Labels support tickets by severity and category. | [Ticket analysis API](docs/apis/ticket-analysis.md) |

Each API page has a step-by-step first request. Adding an API? Add a row here and a page in `docs/apis/`.

## Get it running
1. Create your settings file and a key:
   ```bash
   cp .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(32))"   # prints a new key
   ```
   Open `.env` and set `JEV_CLIENT_API_KEYS=` to that key.
2. Start the service. The first start downloads the model, so it can take a few minutes:
   ```bash
   uv run jev-playground
   ```
3. Check that it is ready (the answer should be `{"ready":true}`):
   ```bash
   curl localhost:8000/health/ready
   ```
4. Open `localhost:8000/docs` in a browser to explore the APIs (it is on while `JEV_EXPOSE_DOCS=true`, which `.env.example` sets). Then follow an API page above for a first request.

## Run the tests
```bash
uv run pytest                          # no model download needed
uv run python evals/triage_eval.py     # accuracy on 8 sample tickets (loads the local model)
```

## Run it in Docker
```bash
docker compose up --build    # serves on 127.0.0.1:8000
```

## Docs
- [How it works](docs/architecture.md): the big picture in plain words
- [Something went wrong?](docs/troubleshooting.md): errors and how to fix them
- [Running it for real](docs/deployment.md): keys, choosing the model, Docker
- [Word list](docs/glossary.md): what the technical words mean
