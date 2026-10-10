# Troubleshooting

Start here when something does not work. Find what you see, check the cause, and apply the fix.

New to a word? See the [word list](glossary.md).

## What do the answer numbers mean?

Every answer has a status code. Codes starting with 2 mean it worked, 4 means something is wrong with your request, and 5 means the service had a problem.

| Status | `code` in the answer | What it means | What to do |
|---|---|---|---|
| 200 | none | It worked. | Nothing. |
| 401 | `unauthorized` | The API key is missing or wrong. | See "I get 401" below. |
| 413 | `payload_too_large` | The request is bigger than the size limit ([settings](architecture.md#settings)). | Send fewer or shorter tickets. |
| 422 | `validation_error`, `invalid_ticket`, `invalid_batch` | Something in the request is not valid. | Read the `errors` list or the `detail` sentence. Each code is explained on [the API page](apis/ticket-analysis.md#what-can-go-wrong). |
| 500 | `internal_error` | The service had an unexpected problem. | Send the `request_id` from the answer to the people who run the service. They can find the matching log lines. |
| 503 | `classifier_unavailable` | The service cannot do the work right now. | Wait a minute and try again. See "The service says it is not ready" below. |

## I get 401

**Cause:** the `X-API-Key` header is missing, has a typo, or holds a key the service does not know. The service gives the same answer in all these cases on purpose. A real answer looks like this:

```json
{"type": "about:blank", "title": "Unauthorized", "status": 401,
 "detail": "A valid API key is required.", "code": "unauthorized", "request_id": "<a short code>"}
```

**Check:**
- Is the header named exactly `X-API-Key`?
- Does the key have extra spaces or quotes around it?
- Did you edit `.env` recently, or write the same setting twice in it? See the notes in [deployment](deployment.md#how-do-i-run-it-in-docker).

**Fix:** use a key from the current `JEV_CLIENT_API_KEYS`. To compare keys without printing them, see [deployment](deployment.md#how-do-i-check-which-key-the-service-is-using).

## The service says it is not ready (503 on `/health/ready`)

**Cause:** the model is still loading. The first start downloads it, which can take a few minutes.

**Check:** `curl localhost:8000/health/ready`. It answers `{"ready": true}` when done. Watch progress with `docker compose logs -f api`.

**Fix:** wait. If it never becomes ready, look in the log for an error, such as the hosted backend being selected without `JEV_API_KEY`.

## The service will not start

**Cause:** it stops on purpose in these cases, so it never runs in an unsafe state:
- Authentication is on and `JEV_CLIENT_API_KEYS` is empty.
- A key in `JEV_CLIENT_API_KEYS` is shorter than the minimum length ([deployment](deployment.md#how-do-i-create-and-use-api-keys)).
- `JEV_BACKEND=jev` without `JEV_API_KEY`.

**Fix:** set the missing value in `.env` (see [deployment](deployment.md)), then restart.

## I cannot open /docs

**Cause:** the interactive docs are off unless `JEV_EXPOSE_DOCS=true`.

**Fix:** set it to `true` in `.env` for your own computer and recreate the container. With `docker compose up`, a local-development file turns them on by default; `docker compose -f compose.yaml up` does not.

## The answer is slow

**Cause:** tickets are handled one at a time. With the local model a large batch can take several seconds.

**Fix:** send smaller batches, or use `JEV_BACKEND=jev`.

## I get 413 even though my request seems small

**Cause:** the limit applies to the whole request in bytes, not to tickets. Long descriptions and evidence add up.

**Fix:** shorten the text or split the tickets across several requests.
