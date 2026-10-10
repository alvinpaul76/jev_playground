# How it works

This page explains how the service handles a request, where the code lives, and which settings change its behavior. You do not need to read code to follow it.

New to a word? See the [word list](glossary.md).

## In plain words

You send the service a list of support tickets. For each ticket, it asks a language model two questions: "how severe is this?" and "what kind of problem is this?". It sends the answers back, in the same order. The service keeps no data: once it answers, it forgets the request.

```
 you ──send tickets──▶ service ──ask two questions per ticket──▶ model
 you ◀──labels back─── service ◀──────────── answers ─────────────┘
```

The model is one of three choices (the "backend"): a small model running on the same machine, the hosted Jev service, or a fake one used only in tests. See [the backends](#which-model-answers-the-questions).

## What happens to a request

Every request to `/api/v1/*` stops at these checkpoints, in this order. Each one exists to protect the service.

1. **Size check** (`api/limits.py`): a request larger than the size limit (see [settings](#settings)) is turned away straight away, before anything is read. This stops one huge request from using up the machine's memory.
2. **Request ID** (`api/errors.py`): the request gets a short code, so you can find it in the logs. If you send your own `X-Request-ID` it is used only when it is 1 to 64 letters, digits, `-` or `_`. Anything else is replaced, because the code ends up in log files.
3. **Key check** (`api/security.py`): the service checks the `X-API-Key` header against the allowed keys. A missing key and a wrong key get exactly the same answer, so an attacker learns nothing from the difference.
4. **Format check**: the request must have the right fields and no extra ones.
5. **Business rules** (`modules/ticket_analysis/domain/`): for example, a cap on tickets per request and no repeated ids. The exact limits are on the [API page](apis/ticket-analysis.md#what-do-i-send).
6. **The model is asked**: one ticket at a time.
7. **The answer is sent back** with the same order as the request.

The health checks (`/health/live` and `/health/ready`) need no key, so monitoring tools can use them.

## Where things live

```
src/jev_playground/
├── main.py            builds the app and stops with an error if it is set up unsafely
├── config.py          all settings, read from environment variables
├── lifespan.py        start-up: loads the model once, then marks the service ready
├── api/               things shared by every feature: key check, errors, size limit, health
└── modules/ticket_analysis/
    ├── api/             the web endpoint and its request and response shapes
    ├── application/     the steps of "analyze these tickets"
    ├── domain/          the business rules (limits, allowed labels), plain Python
    └── infrastructure/  the parts that talk to a model or the hosted service
evals/                 a script that measures accuracy; not part of the service
tests/                 automatic checks
```

The code is split so that each layer depends only on the ones closer to the rules. The business rules never mention web servers or models, so they can be tested alone and the model can be swapped without touching them.

## What errors look like

Every error has the same shape (the standard called RFC 9457, sent as `application/problem+json`). It always includes a `code` that stays the same over time, a plain `detail` sentence, and a `request_id`. Error answers never repeat the ticket text you sent, so private text is not echoed back.

For the list of codes and what to do about each, see [troubleshooting](troubleshooting.md).

## Settings

Settings are environment variables that all start with `JEV_`. They are read once, at start-up, from your environment or the `.env` file. The names and defaults below come from `config.py`. See [deployment](deployment.md) for how to use them safely.

| Setting | Default | What it changes |
|---|---|---|
| `JEV_BACKEND` | `hf` | Who answers: `hf` (small model on this machine), `jev` (hosted service), `mock` (fake, tests only). |
| `JEV_MODEL_ID` | `Qwen/Qwen2.5-0.5B-Instruct` | Which model the `hf` choice loads. |
| `JEV_API_KEY` | none | The key this service uses to call the hosted Jev service. Only for `JEV_BACKEND=jev`. `TYPESAFE_API_KEY` also works. |
| `JEV_BASE_URL` | `https://api.typesafe.ai` | Address of the hosted service. |
| `JEV_JEV_MODEL` | `jev-latest` | Which hosted model to ask. |
| `JEV_JEV_TIMEOUT_S` | `30` | Seconds to wait for the hosted service before giving up. |
| `JEV_CLIENT_API_KEYS` | none | The keys callers must send, separated by commas. [Deployment](deployment.md#how-do-i-create-and-use-api-keys) says how to make one. |
| `JEV_AUTH_ENABLED` | `true` | `false` turns the key check off. For your own computer only. |
| `JEV_EXPOSE_DOCS` | `false` | `true` shows the interactive docs at `/docs` and `/redoc`, and `/` redirects there. |
| `JEV_MAX_REQUEST_BYTES` | `2097152` (2 MiB) | Largest request the service accepts. |
| `JEV_HOST`, `JEV_PORT` | `127.0.0.1`, `8000` | Where the service listens. |
| `JEV_LOG_LEVEL` | `INFO` | How much it writes to the log. |

`JEV_CLIENT_API_KEYS` and `JEV_API_KEY` are different on purpose. The first is for people calling this service. The second is for this service calling someone else.

## Which model answers the questions

The choice is made in one place, `infrastructure/backends.py`:

- **`hf`** loads a small model on this machine when the service starts. The first start downloads it. It handles one ticket at a time, because the library is not safe to call from two places at once.
- **`jev`** sends each ticket to the hosted Jev service. It needs `JEV_API_KEY`.
- **`mock`** gives fixed, made-up answers so the tests run fast and offline.

Nothing else in the service knows which one is in use.

## Starting up and health

At start-up the service loads the model, then marks itself ready. Two health checks report on this, and neither needs a key:

| Address | While loading | When ready |
|---|---|---|
| `/health/live` | `{"status":"ok"}` (200) | `{"status":"ok"}` (200) |
| `/health/ready` | `{"ready":false}` (503) | `{"ready":true}` (200) |

Unsafe set-ups stop the service at start-up instead of letting it run. [Troubleshooting](troubleshooting.md#the-service-will-not-start) lists them.

## Running the tests

```bash
uv run pytest
```

The tests use the fake model, so nothing is downloaded and no key is needed.

## Rules for adding a new API

Each rule comes with its reason.

- **Put a new feature in `modules/<name>/` with the same four folders.** Keeping the layout the same makes every feature easy to find.
- **Mount its router in `api/v1/router.py`.** The key check and the documented errors then apply automatically.
- **Raise a business error with a stable `code`, and map it to a status in `api/errors.py`.** Clients rely on codes staying the same.
- **Reject unknown fields in requests, and take limits from the domain constants.** The web layer and the rules then cannot disagree.
- **Keep outside calls in `infrastructure/`.** That keeps the rules testable and the outside service swappable.
