from openjev import Choice, SystemOneRequest
from openjev.backends import get_backend

SAMPLE_TICKETS = [
    {
        "id": "JEV-001",
        "title": "API returns HTTP 500 for all users",
        "description": "After deploying version 2.4.1, the customer API started returning HTTP 500 errors for every request. Database connectivity checks are successful. Application logs show AttributeError: 'NoneType' object has no attribute 'id' in the authentication middleware.",
        "environment": "production",
        "severity": "critical",
        "category": "incident",
        "business_impact": "All customers are unable to access the service.",
        "evidence": [
            "Error rate increased from 0.1% to 100% immediately after deployment.",
            "Database connectivity checks are successful.",
            "Authentication middleware logs show an AttributeError.",
        ],
    },
    {
        "id": "JEV-002",
        "title": "API exposes another user's invoice",
        "description": "A user can retrieve another customer's invoice by changing the invoice_id parameter in the API request. The endpoint verifies that the requester is authenticated but does not verify invoice ownership.",
        "environment": "staging",
        "severity": "high",
        "category": "security",
        "business_impact": "Unauthorized users may access confidential customer invoice information.",
        "evidence": [
            "The issue was reproduced using two separate test accounts.",
            "The endpoint checks authentication but does not validate invoice ownership.",
        ],
    },
    {
        "id": "JEV-003",
        "title": "Dashboard button is misaligned",
        "description": "On the dashboard, the Export CSV button appears approximately 8 pixels lower than the Refresh button in Chrome. Both buttons work correctly. The issue does not occur in Firefox.",
        "environment": "production",
        "severity": "low",
        "category": "ui",
        "business_impact": "No functional impact has been reported. The issue is limited to visual alignment in Chrome.",
        "evidence": [
            "The misalignment is approximately 8 pixels.",
            "Both buttons function correctly.",
            "The issue does not occur in Firefox.",
        ],
    },
    {
        "id": "JEV-004",
        "title": "Application sometimes freezes",
        "description": "A user reports that the application occasionally freezes when opening a report. No screenshots, logs, browser information, steps to reproduce, or affected user count are provided.",
        "environment": "unknown",
        "severity": "unknown",
        "category": "performance",
        "business_impact": "Unknown. The affected users and operational consequences have not been established.",
        "evidence": [
            "A user reported intermittent freezing when opening a report.",
            "No diagnostic logs are available.",
            "The issue cannot currently be reproduced from the available information.",
        ],
    },
    {
        "id": "JEV-005",
        "title": "Payment marked failed but charged",
        "description": "The application displays a payment as Failed. However, the payment provider dashboard shows a successful charge, and the customer has provided a bank notification confirming the debit. The internal transaction record has no provider reference ID. The reconciliation job has not yet run.",
        "environment": "production",
        "severity": "high",
        "category": "financial_integrity",
        "business_impact": "The customer may be incorrectly informed that a payment failed despite evidence of a successful charge.",
        "evidence": [
            "The application displays the payment as Failed.",
            "The payment provider dashboard shows a successful charge.",
            "The customer provided a bank debit notification.",
            "The internal transaction record has no provider reference ID.",
            "Reconciliation has not yet run.",
        ],
    },
    {
        "id": "JEV-006",
        "title": "Add dark mode to the application",
        "description": "A customer requests a dark theme for the application. The current interface supports only a light theme. The product requirements do not specify dark mode, and no existing functionality is broken.",
        "environment": "production",
        "severity": "low",
        "category": "feature_request",
        "business_impact": "The requested enhancement may improve user preference and accessibility, but no existing business operation is disrupted.",
        "evidence": [
            "The application currently supports only a light theme.",
            "Dark mode is not included in the documented requirements.",
            "No existing functionality is broken.",
        ],
    },
    {
        "id": "JEV-007",
        "title": "Export fails after a dependency upgrade",
        "description": "CSV exports worked in version 3.8.0. After upgrading the CSV processing library and releasing version 3.9.0, exports containing accented characters fail with a Unicode encoding exception. The team has not yet confirmed whether reverting the library resolves the issue.",
        "environment": "production",
        "severity": "medium",
        "category": "regression",
        "business_impact": "Users cannot export certain CSV files containing accented characters.",
        "evidence": [
            "CSV exports worked in version 3.8.0.",
            "The CSV processing library was upgraded before version 3.9.0.",
            "Exports containing accented characters now fail.",
            "Reverting the dependency has not been tested.",
        ],
    },
    {
        "id": "JEV-008",
        "title": "Session expires after inactivity",
        "description": "A user reports being redirected to the login page after leaving the application idle for 30 minutes. The security specification explicitly requires sessions to expire after 30 minutes of inactivity.",
        "environment": "production",
        "severity": "low",
        "category": "authentication",
        "business_impact": "The user must log in again after the configured inactivity period.",
        "evidence": [
            "The session expires after 30 minutes of inactivity.",
            "The security specification explicitly requires a 30-minute inactivity timeout.",
            "The observed behavior matches the documented requirement.",
        ],
    },
]

SEVERITIES = ["critical", "high", "medium", "low", "unknown"]
CATEGORIES = [
    "incident",
    "security",
    "ui",
    "performance",
    "financial_integrity",
    "feature_request",
    "regression",
    "authentication",
]

QUESTIONS = {
    "severity": Choice(
        instructions="What is the severity of this ticket?", options=SEVERITIES
    ),
    "category": Choice(
        instructions="Which category best describes this ticket?", options=CATEGORIES
    ),
}

backend = get_backend("hf", model_id="Qwen/Qwen2.5-0.5B-Instruct")

sev_correct = cat_correct = 0
for ticket in SAMPLE_TICKETS:
    # strip the labels so the model judges the narrative, not the answers
    state = {k: v for k, v in ticket.items() if k not in QUESTIONS}
    resp = backend.decide(SystemOneRequest(state=state, questions=QUESTIONS))
    sev, cat = resp.answers["severity"], resp.answers["category"]
    sev_ok = sev.choice == ticket["severity"]
    cat_ok = cat.choice == ticket["category"]
    sev_correct += sev_ok
    cat_correct += cat_ok
    print(
        f"{ticket['id']} severity={sev.choice:<8} (exp {ticket['severity']:<8}) "
        f"{'PASS' if sev_ok else 'FAIL'} | "
        f"category={cat.choice:<20} (exp {ticket['category']:<20}) "
        f"{'PASS' if cat_ok else 'FAIL'} ({resp.latency_ms:.0f}ms)"
    )

n = len(SAMPLE_TICKETS)
print(f"\nAccuracy: severity {sev_correct}/{n}, category {cat_correct}/{n}")
