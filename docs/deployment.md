# Running it for real

How to set up keys, choose which model answers, and run the service in Docker. For what each setting does, see the [settings table](architecture.md#settings).

New to a word? See the [word list](glossary.md).

## How do I create and use API keys?

Callers need a key. You make one and give it to them.

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"   # prints a new key
```

Put one or more keys in `.env`, separated by commas. Each must be at least 32 characters (the service checks this in `config.py` and refuses shorter ones):

```
JEV_CLIENT_API_KEYS=<first-key>,<second-key>
```

Keep keys only in `.env` (which is never committed) or in your shell. Never put them in the Docker image, in a chat, or in these docs.

- **Rotating a key:** add the new key next to the old one, restart, move callers to the new key, then remove the old one. Callers never lose access.
- **Safe by design:** with authentication on and no keys, the service stops at start-up, so it can never run open by accident. [Troubleshooting](troubleshooting.md#the-service-will-not-start) lists the other cases.
- **Two different keys:** `JEV_CLIENT_API_KEYS` are for people calling this service. `JEV_API_KEY` is for this service calling the hosted Jev service. They are unrelated.

## How do I turn the key check off?

Only on your own computer, for experiments:

```
JEV_AUTH_ENABLED=false
```

Keys become optional, anyone who can reach the service can use it, and the service writes a warning in its log at start-up. The default is `true`. Do not turn it off on any machine others can reach. The interactive docs still show an "Authorize" button, but the key is ignored.

## How do I choose which model answers?

Set `JEV_BACKEND` (see [the backends](architecture.md#which-model-answers-the-questions)):

```bash
uv run jev-playground                          # default: local model
JEV_BACKEND=jev uv run jev-playground          # hosted service; needs JEV_API_KEY in .env
```

With Docker, put `JEV_BACKEND=jev` and `JEV_API_KEY=<your-hosted-key>` in `.env` and recreate the container. Each answer's `model` field tells you which one replied.

## How do I run it in Docker?

```bash
docker compose up --build                      # for your computer: interactive docs on, at 127.0.0.1:8000
docker compose -f compose.yaml up -d --build   # production-like: docs off
```

What to know:

- **After editing `.env`:** run `docker compose up -d --force-recreate`. Docker reads `.env` only when it creates the container.
- **One line per setting:** if a setting appears twice in `.env`, the last one wins and the first is ignored.
- **Local build files:** `compose.yaml` hands Docker the folder `../../tools/OpenJev` as an extra build input, because that library lives outside this project. A plain `docker build` needs `--build-context openjev=../../tools/OpenJev`.
- **Safety defaults:** the container runs as an ordinary user (id 10001), cannot write to its own files, and has all special privileges removed.
- **Model downloads:** the model is stored in a Docker volume called `hf-cache`, so only the first start downloads it.
- **Behind a proxy:** set `FORWARDED_ALLOW_IPS` to the proxy's address, never `*`.
- **Size and updates:** the image is about 1.2 GB. Its base images are fixed to exact versions; refresh and rebuild now and then to get security patches.
- **Not included:** limits on how many requests a caller can make, and per-key quotas.

## Which settings matter for production?

| Setting | Safe value | Risk of the other value |
|---|---|---|
| `JEV_AUTH_ENABLED` | `true` | `false` lets anyone who can reach the service use it. |
| `JEV_CLIENT_API_KEYS` | at least one long, random key per caller | A short or shared key is easy to guess or leak. |
| `JEV_EXPOSE_DOCS` | `false` | `true` shows the full list of endpoints to anyone who can reach the service. |
| `JEV_MAX_REQUEST_BYTES` | keep the default, or lower | A large value lets one request use a lot of memory. |
| `FORWARDED_ALLOW_IPS` | the proxy's address | `*` lets any caller pretend to be someone else. |
| `JEV_LOG_LEVEL` | `INFO` | `DEBUG` can write more detail than you want to store. |

## How do I check which key the service is using?

You can compare keys without printing them. These two commands print a short fingerprint; if they match, the container has the key from `.env`:

```bash
printf %s "$(grep '^JEV_CLIENT_API_KEYS=' .env | tail -1 | cut -d= -f2-)" | sha256sum | cut -c1-8
docker compose exec -T api printenv JEV_CLIENT_API_KEYS | tr -d '\n' | sha256sum | cut -c1-8
```

If they differ, recreate the container (see above). With several keys, compare the full comma-separated value.
