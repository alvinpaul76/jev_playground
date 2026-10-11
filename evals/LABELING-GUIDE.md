# JEV Ticket Labeling Guide

**Version:** 1.1  
**Status:** Working standard  
**Process rules agreed:** 2026-10-11  
**Owner:** Project owner

## 1. Purpose

This guide defines how the owner assigns ground-truth labels to issue tickets used to evaluate JEV.

The labeled dataset measures whether JEV can correctly classify:

- **Severity:** How significantly the issue affects business or system operations.
- **Category:** What kind of issue is being reported.
- **Assigned team:** Which team is primarily responsible for resolving the issue, based on the available evidence.

Labels must be based on the ticket's content and the rules in this guide, not on the classifier's predictions.

**Independence rule:** This guide must remain independent of the label descriptions supplied to the classifier. The classifier descriptions are what is being tuned; this guide defines the standard against which the results are measured.

Do not copy classifier descriptions into this guide. Changing a classifier description must not automatically change a ground-truth label or labeling rule.

## 2. Who Labels

One person, the owner, labels every ticket.

The owner must:

- Read the ticket and its available evidence before assigning labels.
- Apply the same rules to every ticket, regardless of its source.
- Never consult JEV's predictions before deciding the expected labels.
- Never change a label simply to agree with a model prediction.
- Record a note when a decision is ambiguous or depends on an important assumption.
- Apply any new labeling rule consistently to all affected tickets.

If a labeling error is discovered, correct it according to this guide and record the reason for the correction.

## 3. Ticket Sources and Data Preparation

The dataset may contain both real and hand-written tickets.

### 3.1 Real tickets

Before including a real ticket:

- Remove personal names, email addresses, phone numbers, account numbers, customer identifiers, API keys, tokens, passwords, and other sensitive information.
- Remove internal hostnames, IP addresses, and infrastructure identifiers when they could expose private systems.
- Preserve relevant technical details, error messages, stack traces, affected components, observed behavior, and diagnostic evidence.
- Preserve the distinction between confirmed facts, user reports, and unverified hypotheses.
- Do not invent missing details or rewrite the issue to make its cause more obvious.

If a ticket contains too little information to support a reliable decision, retain it as a difficult example where appropriate.

### 3.2 Hand-written tickets

Use hand-written tickets to fill gaps in the dataset, including:

- Underrepresented severity levels, categories, or teams.
- Tickets with insufficient information.
- Cases where two teams could reasonably be considered.
- Cases where the visible symptom differs from the underlying cause.
- False alarms and expected behavior.
- Feature requests that could be mistaken for defects.
- Tickets with conflicting or incomplete evidence.

Hand-written tickets must be realistic and internally consistent. Do not make every ticket artificially obvious or design examples solely to favor the classifier.

## 4. Labeling Dimensions

Each ticket receives exactly three primary labels:

```text
severity
category
assigned_team
```

Determine each label independently.

A security issue is not automatically critical. A production issue is not automatically a high-severity incident. A category does not automatically determine which team owns the fix.

Use only the evidence available in the ticket. Do not infer facts that the ticket does not support.

## 5. How to Assign a Team

**Assign the team best positioned to resolve the underlying issue, not necessarily the team that first receives the ticket, detects the problem, or responds to the incident.**

The valid team identifiers are:

| Identifier | Responsibility |
|---|---|
| `backend` | Server-side application code, APIs, business logic, database integration, and backend processing. |
| `frontend` | User interfaces, browser behavior, client-side code, rendering, layout, and frontend interactions. |
| `devops` | Infrastructure, deployments, runtime configuration, environment setup, and operational reliability when these are the source of the problem. |
| `security` | Security vulnerabilities, authorization weaknesses, security-control failures, and specialist security remediation. |
| `product_management` | Product requirements, feature requests, prioritization, acceptance criteria, and decisions about intended product behavior. |
| `tech_support` | Initial investigation, information gathering, reproduction assistance, and triage when there is insufficient evidence to select a specialist team. |
| `payments_financial_systems` | Payment processing, transaction states, financial reconciliation, payment integrations, and financial data integrity. |

Use these exact identifiers in all datasets and evaluation code. Do not use spaces, ampersands, or display names in `assigned_team`.

### 5.1 Root cause versus symptom

When the ticket provides evidence of a specific cause, select the team responsible for that cause.

Example: `JEV-001` reports that all API requests fail immediately after a deployment. However, the available logs show an application-code exception in the authentication middleware.

Expected assignment: `backend`.

Do not automatically assign `devops` merely because the problem appeared after a deployment. Assign `devops` when the evidence points to the deployment mechanism, infrastructure, environment, or runtime configuration as the primary cause.

### 5.2 Security-related issues

Assign `security` when a security vulnerability or failure of a security control is the primary issue, even if another team must change application code to implement the fix.

Example: An authenticated user can access another customer's invoice because ownership authorization is missing.

Expected assignment: `security`.

An alternative team such as `backend` may be documented in `note` if application-code ownership is genuinely uncertain.

### 5.3 Payments and financial systems

Assign `payments_financial_systems` when the primary issue concerns payment processing, transaction-state inconsistencies, reconciliation, payment integrations, or financial data correctness.

Example: The application marks a payment as failed while the payment provider confirms a successful charge.

Expected assignment: `payments_financial_systems`.

### 5.4 Product requests

Assign `product_management` when the ticket requests new functionality or requires a decision about product requirements, and the implementation owner is not otherwise established.

If a ticket reports an existing function that violates a documented requirement, assign the team responsible for that defective function instead.

### 5.5 Insufficient routing information

Use `tech_support` when the ticket is too vague to identify a responsible specialist team.

Do not use `unknown` as a team label. Every ticket must receive one of the seven valid team identifiers.

If the root cause is not confirmed but the ticket clearly identifies the responsible technical domain, choose the best-supported team instead of defaulting automatically to `tech_support`.

### 5.6 Team tie-breaker

When two teams could reasonably fix an issue:

1. Prefer the team responsible for the evidenced cause over the team that merely reports or detects the problem.
2. Prefer `security` when specialist security remediation is central.
3. Prefer `payments_financial_systems` when financial transaction correctness is central.
4. Prefer `devops` when infrastructure, deployment mechanisms, or runtime configuration are the evidenced cause.
5. Prefer `tech_support` when the ticket does not establish a sufficiently clear technical domain.
6. Select one primary team, and document a plausible alternative in `note` when it helps explain genuine ambiguity.

Do not change the expected team merely because another team may need to assist with the fix.

## 6. How to Assign Severity

Valid values:

```text
critical
high
medium
low
unknown
```

Severity measures the business or operational impact supported by the ticket evidence. It does not measure technical complexity, the reporter's urgency, or how difficult a problem is to fix.

### 6.1 Severity definitions

**`critical`**

Use when the evidence establishes exceptionally severe impact, such as a core production service being unavailable to most or all users, major data loss or corruption, serious active security exposure, or widespread failure of an essential financial process. Immediate attention is required, and an effective workaround is generally unavailable.

**`high`**

Use when a major feature or important business workflow is substantially impaired, many users or a significant business function are affected, or the established risk requires prompt remediation. A workaround may exist but is impractical, incomplete, or costly.

**`medium`**

Use when a meaningful but bounded problem affects some functionality, a limited group of users, or a noncritical workflow. Business impact is real, but normal operations can generally continue through a reasonable workaround.

**`low`**

Use when the impact is minor, such as a cosmetic defect or small inconvenience with no material disruption to business operations. The affected function remains usable, or a simple workaround is available.

**`unknown`**

Use when the ticket provides insufficient information to assess the impact reliably. Do not use this label merely because the root cause is unknown if the business impact is already clear.

### 6.2 Severity decision rules

- Do not infer critical severity merely because an issue occurs in production.
- Do not assign high severity solely because a ticket concerns security or payments.
- Do not assign low severity merely because an issue appears cosmetic; consider any documented accessibility or operational impact.
- Do not treat a possible risk as proof that harm has already occurred.
- Consider the affected users, scope, duration, business consequences, data impact, and availability of workarounds.
- If evidence is insufficient to distinguish severity levels reliably, use `unknown` rather than guessing.

For example, `JEV-004` reports occasional application freezing but does not establish the number of affected users or business consequences. Its expected severity is `unknown`.

By contrast, `JEV-001` establishes that all customers are unable to access the production API. Its expected severity is `critical`.

## 7. How to Assign Category

Valid values:

```text
incident
security
ui
performance
financial_integrity
feature_request
regression
authentication
unknown
```

Assign exactly one primary category per ticket.

Choose the category that best represents the primary issue, rather than selecting a category solely because a related keyword appears in the description.

### 7.1 Category definitions

**`incident`**

An unplanned operational disruption affecting a service or important business workflow, where no more specific category adequately represents the primary issue.

**`security`**

A security vulnerability or security-control failure that could permit unauthorized access, information exposure, privilege escalation, or another violation of system security.

**`ui`**

A defect in interface presentation or client-side interaction, such as a misaligned control, broken navigation element, or incorrectly rendered screen.

**`performance`**

A problem involving latency, throughput, resource consumption, or application responsiveness that materially affects expected behavior.

**`financial_integrity`**

An error or inconsistency in financial transactions, payment states, amounts, balances, accounting records, or reconciliation.

**`feature_request`**

A request for new or changed functionality that is not required by the existing specifications and does not primarily report a defect in existing required behavior.

**`regression`**

A failure of previously working functionality associated with a subsequent code, dependency, configuration, or system change, where a more specific category does not better represent the main issue and the problem is not a broader operational incident.

**`authentication`**

An issue involving login, identity verification, session handling, or expected authentication behavior, excluding cases where a security vulnerability is the primary issue.

**`unknown`**

Use when the available evidence is insufficient to determine the category reliably, or the issue does not fit any defined category.

### 7.2 Category precedence rules

Some tickets fit more than one category. Apply these rules to choose a consistent primary label.

**Rule 1 — Security vulnerability**

Choose `security` when unauthorized access, a vulnerability, or a security-control failure is the primary issue.

Example: A user can access another customer's invoice due to missing ownership authorization.

Expected category: `security`.

**Rule 2 — Financial correctness**

Choose `financial_integrity` when the primary issue is an incorrect or inconsistent financial state and a security vulnerability is not the central issue.

Example: The application marks a payment as failed while the payment provider confirms a successful charge.

Expected category: `financial_integrity`.

**Rule 3 — Authentication behavior**

Choose `authentication` for ordinary login failures, incorrect session behavior, or identity-verification issues that are not primarily security vulnerabilities.

Example: A session expires after 10 minutes even though the specification requires 30 minutes.

Expected category: `authentication`.

**Rule 4 — Feature requests**

Choose `feature_request` when the user requests functionality that is not required by current specifications.

Example: Adding dark mode when the existing specification requires only a light theme.

Expected category: `feature_request`.

If existing functionality violates a requirement, label the defect according to its actual nature instead.

**Rule 5 — UI and performance**

Choose `ui` for presentation or client-side interaction defects. Choose `performance` for responsiveness, latency, throughput, or resource-use problems.

Example: A report takes 45 seconds to open because processing is slow.

Expected category: `performance`.

**Rule 6 — Broad operational incidents**

Choose `incident` when the primary issue is a broad, unplanned operational disruption, such as a production-wide service outage. Do not use `regression` as the primary category merely because a deployment preceded the outage.

Example: All production API requests fail following a deployment.

Expected category: `incident`.

**Rule 7 — Localized regressions**

Choose `regression` when previously working functionality breaks following a change and the failure is localized rather than a broad service incident.

Example: CSV exports containing accented characters stop working after a library upgrade, while other application functions continue operating.

Expected category: `regression`.

**Rule 8 — Unknown**

Use `unknown` when no category is adequately supported by the evidence or when the issue falls outside the defined taxonomy. Do not guess merely to avoid using `unknown`.

### 7.3 Category is independent of severity and team

A category does not determine the severity or the assigned team.

For example, a security vulnerability may have low, medium, high, or critical severity depending on the evidence of exposure and impact. Its responsible team is determined by the team-assignment rules in Section 5.

A ticket describing expected behavior may still be categorized by the type of behavior being discussed. The presence of a category does not mean a defect has been confirmed.

## 8. Unknown and Ambiguous Labels

These concepts are different and must not be used interchangeably.

### 8.1 Unknown

Use `unknown` for a particular labeling dimension when the evidence is insufficient to support a reliable decision, or when a category cannot be represented by the current taxonomy.

Unknown is a valid expected label where permitted by the schema. It is not a substitute for careful analysis.

A ticket may have an unknown severity but a clear category and team.

### 8.2 Ambiguous

Set:

```json
"ambiguous": true
```

when the ticket remains genuinely open to multiple reasonable interpretations under the current rules.

Examples include:

- Two teams have equally strong evidence of primary ownership.
- The ticket contains contradictory evidence that cannot be resolved.
- Two categories remain equally plausible after applying the precedence rules.

Provide a concise explanation in `note`. Identify the affected labeling dimension where possible.

Do not mark a ticket ambiguous simply because it is difficult, short, or missing a technical root cause. Apply the existing rules first.

### 8.3 Evaluation treatment

Ambiguous tickets must be reported separately and excluded from the primary accuracy calculation. Report their count and percentage.

If a recurring ambiguity reveals a missing rule, revise this guide, record the change, and apply it consistently to all affected tickets.

Do not exclude valid `unknown` labels merely because they are unknown. They are part of the classification task.

## 9. Anchor Examples and Smoke Tests

The eight tickets in `data/smoke.jsonl` are anchor examples for checking the labeling process and basic classifier behavior.

They may be used during development and classifier tuning, but they must not be counted as new held-out evaluation tickets.

The intended labels for these examples follow the rules in this guide. For the current eight examples, the principal assignments are:

| Ticket | Severity | Category | Assigned team |
|---|---|---|---|
| `JEV-001` | `critical` | `incident` | `backend` |
| `JEV-002` | `high` | `security` | `security` |
| `JEV-003` | `low` | `ui` | `frontend` |
| `JEV-004` | `unknown` | `performance` | `tech_support` |
| `JEV-005` | `medium` | `financial_integrity` | `payments_financial_systems` |
| `JEV-006` | `low` | `feature_request` | `product_management` |
| `JEV-007` | `medium` | `regression` | `backend` |
| `JEV-008` | `low` | `authentication` | `tech_support` |

For `JEV-005`, `medium` reflects the documented, bounded impact of an individual payment discrepancy. If subsequent evidence establishes a wider disruption, revise its label according to this guide.

For `JEV-008`, the observed session timeout conforms to the stated specification. The category describes the subject of the ticket, not confirmation that the system is defective.

When a labeling rule changes:

1. Review whether existing anchor labels remain correct.
2. Update labels only when justified by the revised guide.
3. Record the change and its reason.
4. Do not treat smoke-test accuracy as evidence of generalization.

## 10. Dataset Size and Coverage

Create at least 30 new labeled tickets in addition to the smoke set.

Use these minimum coverage targets:

| Coverage dimension | Minimum |
|---|---:|
| Each of the 7 teams | 2 tickets per team |
| Each of the 9 categories | 1 ticket per category |
| Each of the 5 severity values | 2 tickets per value |
| Difficult cases | Approximately 5 tickets |
| Total new tickets | At least 30 |

A single ticket may count toward multiple coverage targets.

These are minimum coverage requirements, not guarantees of statistical reliability. Increase the dataset size when a label is rare, the classifier behaves inconsistently, or a more reliable performance estimate is required.

Include both positive and negative examples for binary questions evaluated separately. Avoid constructing a dataset in which one answer is overwhelmingly common.

Track label distributions and the percentage of unknown and ambiguous tickets. Do not remove difficult cases simply to improve reported accuracy.

## 11. Tuning and Held-Out Evaluation

Assign each new ticket to a split when it is first added. Do not choose or change the split after seeing the classifier's prediction.

### 11.1 Tuning set

**File:** `data/tuning.jsonl`  
**Target:** Approximately 12 tickets.

The tuning set may be used to evaluate results while editing classifier label descriptions.

Use tuning results to identify unclear descriptions, overlapping categories, and systematic misclassifications.

### 11.2 Held-out set

**File:** `data/heldout.jsonl`  
**Minimum:** 18 tickets.

The held-out set measures how well JEV performs on tickets that were not used to tune the classifier descriptions.

Rules:

- Never use held-out results to choose, rewrite, or optimize classifier descriptions.
- Do not move tickets between splits because of predictions or evaluation results.
- Avoid placing near-duplicate tickets or tickets from the same underlying incident in different splits.
- Keep expected labels separate from the ticket data supplied to JEV.
- Run held-out evaluation at defined milestones and preserve the results.
- Use `--show-heldout-misses` only when inspecting held-out errors is necessary. Do not use those results to tune the same held-out set and continue reporting it as independent.

If held-out results are used to change the classifier, the set is no longer a fully independent evaluation set. Establish a fresh held-out set for subsequent independent evaluation.

Report tuning and held-out results separately.

## 12. Label Definitions Summary

Use the following exact values in the dataset and evaluation code.

### Severity

```python
SEVERITIES = [
    "critical",
    "high",
    "medium",
    "low",
    "unknown",
]
```

### Category

```python
CATEGORIES = [
    "incident",
    "security",
    "ui",
    "performance",
    "financial_integrity",
    "feature_request",
    "regression",
    "authentication",
    "unknown",
]
```

### Team

```python
TEAMS = [
    "backend",
    "frontend",
    "devops",
    "security",
    "product_management",
    "tech_support",
    "payments_financial_systems",
]
```

These constants represent the ground-truth label sets. Keep them consistent with the dataset schema, output validation, and evaluation code.

## 13. File Format and Validation

Store one JSON object per line in each JSONL dataset file. Do not put the tickets inside a JSON array when using JSONL.

The `expected` object contains the three ground-truth labels. The input passed to JEV must not reveal these labels.

Example:

```json
{"id":"T-001","title":"API returns HTTP 500 for all users","description":"All API requests fail after a deployment.","environment":"production","business_impact":"All customers are unable to access the service.","evidence":["The error rate increased immediately after deployment.","Application logs show an exception in the authentication middleware."],"split":"tuning","expected":{"severity":"critical","category":"incident","assigned_team":"backend"},"ambiguous":false,"note":""}
```

Required fields:

- `id`
- `title`
- `description`
- `split`
- `expected`

The `expected` object must contain:

- `severity`
- `category`
- `assigned_team`

Each label must use one of the exact valid values listed in Section 12.

The `split` value must match the file containing the ticket:

- `data/tuning.jsonl`: `"split": "tuning"`
- `data/heldout.jsonl`: `"split": "heldout"`

Ticket IDs must be unique across the dataset files, including the smoke set if the evaluator loads all of them together.

The `environment`, `business_impact`, and `evidence` fields should be included when available and supported by the implemented schema. Do not fabricate missing information.

For ambiguous tickets, use `"ambiguous": true` and provide a meaningful explanation in `note`. For unambiguous tickets, use `"ambiguous": false` and an empty note unless an explanation is needed.

Validate the files without calling a model:

```bash
uv run python -m evals.run_eval --backend mock
```

A validation error should identify the file, line, and problem. Resolve validation errors before running model-based evaluation.

## 14. Evaluation and Reporting

The evaluation report should distinguish classifier performance from dataset quality.

At a minimum, report:

- Number of tickets in each split.
- Number and percentage of ambiguous tickets.
- Label distribution for severity, category, and assigned team.
- Accuracy for each labeling dimension.
- Macro-F1 and per-label precision, recall, and F1 where applicable.
- Number of invalid or missing predictions.
- Tuning and held-out results separately.

Exclude ambiguous tickets from the primary accuracy calculation, but report their count and percentage. Do not silently exclude valid `unknown` labels or invalid model outputs.

If a metric cannot be meaningfully calculated because a label has no examples or no predictions, report it as unavailable rather than treating it as zero or perfect performance.

Record changes to the labeling guide, expected labels, classifier descriptions, and evaluation results so that results from different milestones can be compared fairly.

## 15. Final Labeling Principle

**Label what the evidence supports, not what seems likely without evidence, and never what JEV predicts.**

When evidence is incomplete, use the appropriate `unknown` value. When the labeling rules genuinely permit multiple reasonable interpretations, record the ambiguity. When a general rule is missing, improve the guide before applying inconsistent decisions across the dataset.
