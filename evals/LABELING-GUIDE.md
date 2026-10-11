# Labeling guide (draft)

Rules a person follows to decide the expected label of each ticket in the labeled set. The process rules below were agreed on 2026-10-11. The label definitions in the last section are for the owner to write.

This guide must stay independent of the label descriptions in the classifier. Those descriptions are what is being tuned; this guide is what they are measured against. Do not copy one into the other.

## Who labels

One person, the owner, labels every ticket and follows this guide. Do not ask a model to label tickets, and do not look at what the model predicted before deciding.

## Where tickets come from

A mix of real and hand-written tickets.

- **Real tickets:** remove names, emails, phone numbers, account and customer ids, keys and tokens, and internal hostnames. Keep the technical details, because those are what the model reads.
- **Hand-written tickets:** use them to fill gaps: tickets with too little information (`unknown`), rare teams, and tickets that could reasonably go to two teams.

## Which team? The team that can fix the cause

`assigned_team` is the team that can fix the cause. It is not the team that notices the problem first or has to respond.

- Example (`JEV-001`): every request fails right after a deploy, and the log shows an `AttributeError` in application code. The cause is code, so the team is `backend`, not `devops`.
- `devops` gets problems caused by infrastructure, releases or configuration.
- A ticket too vague to route goes to `tech_support`. There is no `unknown` team.

## When to use `unknown`

- **Severity `unknown`:** nothing in the ticket allows judging the impact (`JEV-004`: it says the app freezes, but not for whom or how badly).
- **Category `unknown`:** none of the eight other categories fits. This should be rare.

## Ambiguous tickets

If you read a ticket twice and still cannot decide one of its labels, set `"ambiguous": true` and explain why in `"note"`. Ambiguous tickets are listed in the report but left out of accuracy. If many pile up, the guide is missing a rule: add it here.

## Anchor examples

The eight tickets in `data/smoke.jsonl` show how the rules apply. They are used up for tuning, so do not count them as a test.

## How many tickets, and how they are spread

At least 30 new tickets, in addition to the smoke set. Cover at least:

| Label | Minimum |
|---|---|
| Each of the 7 teams | 2 tickets |
| Each of the 9 categories | 1 ticket |
| Each of the 5 severities | 2 tickets |
| Hard cases (minimal information, or could go to two teams) | about 5 |

One ticket can count toward several rows.

## Tuning set and held-out set

- **Tuning set:** about 12 tickets. You may look at their results while editing label descriptions.
- **Held-out set:** at least 18 tickets. Never edit descriptions based on them. Run them to report accuracy, once per milestone. The report hides their misses unless you pass `--show-heldout-misses`.
- Choose a ticket's split when you add it, not after seeing how the model did.

## File format

One JSON object per line, in `data/tuning.jsonl` and `data/heldout.jsonl`:

```json
{"id": "T-001", "title": "...", "description": "...", "environment": "production",
 "business_impact": "...", "evidence": ["..."], "split": "tuning",
 "expected": {"severity": "high", "category": "incident", "assigned_team": "backend"},
 "ambiguous": false, "note": ""}
```

`id`, `title`, `description`, `split` and `expected` are required. Ids must be unique across all files. Check a file without calling any model:

```bash
uv run python -m evals.run_eval --backend mock
```

A mistake is reported as `file:line` with the problem.

## Label definitions (owner to write before labeling)

Write one sentence per label, in your own words, before you label the first ticket.

- **Severity:** `critical`, `high`, `medium`, `low`, `unknown`
- **Category:** `incident`, `security`, `ui`, `performance`, `financial_integrity`, `feature_request`, `regression`, `authentication`, `unknown`
- **Team:** `backend`, `frontend`, `devops`, `security`, `product_management`, `tech_support`, `payments_financial_systems`
