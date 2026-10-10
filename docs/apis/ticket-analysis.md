# Ticket analysis API

Use it to label support tickets: for each ticket it tells you how severe the problem is and what kind of problem it is, with a confidence score for each.

New to a word? See the [word list](../glossary.md).

`POST /api/v1/ticket-analyses` · needs an API key: yes · code: `src/jev_playground/modules/ticket_analysis/`

## How do I use it?

1. Get an API key from whoever runs the service (or see [deployment](../deployment.md) if you run it yourself).
2. Send a `POST` request with your tickets as JSON and the key in the `X-API-Key` header:

```bash
curl -X POST localhost:8000/api/v1/ticket-analyses \
  -H 'X-API-Key: <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "tickets": [
      {
        "id": "JEV-001",
        "title": "API returns HTTP 500 for all users",
        "description": "After deploying 2.4.1 every request returns 500. Production.",
        "environment": "production",
        "business_impact": "All customers are unable to access the service."
      },
      {
        "id": "JEV-003",
        "title": "Dashboard button is misaligned",
        "description": "Export CSV button is 8px lower in Chrome. Both work.",
        "business_impact": "No functional impact."
      }
    ]
  }'
```

3. Read the answer. This one is from a real run against the hosted Jev service (`JEV_BACKEND=jev`):

```json
{
  "results": [
    {
      "id": "JEV-001",
      "severity": {"label": "critical", "confidence": 1.0},
      "category": {"label": "incident", "confidence": 0.93}
    },
    {
      "id": "JEV-003",
      "severity": {"label": "low", "confidence": 1.0},
      "category": {"label": "ui", "confidence": 1.0}
    }
  ],
  "model": "jev-1.13.0",
  "latency_ms": 484.5
}
```

The local model gives answers of the same shape, but its labels and confidences can differ.

## What do I send?

| Field | Required? | What it means | Limit |
|---|---|---|---|
| `tickets` | yes | The list of tickets to label. | 1 to 20 tickets |
| `id` | yes | Your own name for the ticket. You use it to match answers to tickets. | 64 characters; must be different for every ticket in the request |
| `title` | yes | A short summary. | 200 characters |
| `description` | yes | What happened, in your own words. | 10,000 characters |
| `environment` | no | Where it happened, for example `production`. | 100 characters |
| `business_impact` | no | Who or what is affected. | 2,000 characters |
| `evidence` | no | A list of facts that support the report. | 20 items, 1,000 characters each |

The limits come from `domain/entities.py` and `domain/policies.py`. The whole request must also stay under the size limit; see [settings](../architecture.md#settings).

Do not send `severity` or `category`. They are the answers, and the service rejects them (status 422). If a label were included, the model might repeat it back instead of judging the ticket.

## What do I get back?

| Field | What it means |
|---|---|
| `results` | One entry per ticket, in the same order you sent them. |
| `id` | Your ticket id, repeated so you can match it up. |
| `severity.label` | How serious it is: `critical`, `high`, `medium`, `low` or `unknown` (not enough information to tell). |
| `category.label` | What kind of problem: `incident`, `security`, `ui`, `performance`, `financial_integrity`, `feature_request`, `regression` or `authentication`. |
| `confidence` | A number from 0 to 1: how sure the model is. Treat it as a hint, not a promise. Small models can be unsure. |
| `model` | Which model answered. |
| `latency_ms` | How long the analysis of the whole batch took, in milliseconds. |

The allowed labels are defined in `domain/value_objects.py`. If the model ever returns something outside that list, you get a 503 error instead of an invented label.

## How does it work inside?

For each ticket, the service builds a short description from the fields you sent (never from labels) and asks the model two multiple-choice questions: one for severity and one for category. Each choice comes with a one-line explanation, for example "critical: widespread outage or data exposure", which is what helps a small model pick well. The questions are in `infrastructure/openjev_classifier.py`.

Tickets are handled one at a time, in order. With the local model, only one ticket is being worked on at any moment, so a full batch can take several seconds. With the hosted service, each ticket is a separate call.

A batch is all or nothing. If anything in the request is invalid, nothing is analyzed and you get an error. If the model fails partway, you get an error for the whole request, not a half-finished list.

## What can go wrong?

| Code (status) | What it means here | What to do |
|---|---|---|
| `invalid_batch` (422) | The list is empty, has more tickets than the limit, or two tickets share an `id`. The message names the repeated ids. | Fix the list and send it again. |
| `invalid_ticket` (422) | A required field is blank, or a field is over its limit. | Fix the field named in the message. |
| `validation_error` (422) | The request does not match the format: wrong type, a missing field, an extra field, or broken JSON. | Read the `errors` list. Each item gives the field and the problem. |
| `classifier_unavailable` (503) | The model could not answer, or is still loading. | Wait a minute and try again. |

A real example. Here `title` was sent as a number instead of text:

```json
{
  "type": "about:blank",
  "title": "Validation error",
  "status": 422,
  "detail": "The request body is not valid.",
  "code": "validation_error",
  "request_id": "<a short code>",
  "errors": [{"loc": ["body", "tickets", "0", "title"], "msg": "Input should be a valid string"}]
}
```

`loc` is the path to the problem: the first ticket's `title`. The service never repeats the text you sent.

For errors every API shares (401, 413, 500), see [troubleshooting](../troubleshooting.md).

Back to [how it works](../architecture.md).
