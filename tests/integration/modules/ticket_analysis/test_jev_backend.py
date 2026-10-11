import json

import httpx
import pytest
from pydantic import SecretStr

from jev_playground.config import Settings
from jev_playground.modules.ticket_analysis.domain.entities import Ticket
from jev_playground.modules.ticket_analysis.domain.errors import ClassifierUnavailable
from jev_playground.modules.ticket_analysis.domain.value_objects import (
    Category,
    Severity,
    Team,
)
from jev_playground.modules.ticket_analysis.infrastructure.backends import build_backend
from jev_playground.modules.ticket_analysis.infrastructure.jev_backend import JevBackend
from jev_playground.modules.ticket_analysis.infrastructure.openjev_classifier import (
    OpenJevTicketClassifier,
)

API_RESPONSE = {
    "model": "jev-latest",
    "answers": {
        "severity": {
            "type": "choice",
            "choice": "high",
            "probabilities": {
                "critical": 0.1,
                "high": 0.7,
                "medium": 0.1,
                "low": 0.05,
                "unknown": 0.05,
            },
            "confidence": 0.8,
        },
        "category": {
            "type": "choice",
            "choice": "security",
            "probabilities": {"security": 0.9, "incident": 0.1},
            "confidence": 0.9,
        },
        "assigned_team": {
            "type": "choice",
            "choice": "security",
            "probabilities": {"security": 0.8, "backend": 0.2},
            "confidence": 0.7,
        },
    },
    "usage": {"input_tokens": None, "output_tokens": None},
}


def make_backend(handler) -> JevBackend:
    client = httpx.Client(
        base_url="https://api.test",
        headers={"Authorization": "Bearer k"},
        transport=httpx.MockTransport(handler),
    )
    return JevBackend(api_key="k", client=client)


def test_classifies_via_hosted_api_and_sends_wire_format():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                request.headers["authorization"],
                request.url.path,
                json.loads(request.content),
            )
        )
        return httpx.Response(200, json=API_RESPONSE)

    raw = OpenJevTicketClassifier(make_backend(handler)).classify_many(
        [
            Ticket(id="A", title="Leak", description="d"),
            Ticket(id="B", title="Leak 2", description="d"),
        ]
    )

    assert [a.ticket_id for a in raw.analyses] == ["A", "B"]
    assert raw.analyses[0].severity is Severity.HIGH
    assert raw.analyses[0].category is Category.SECURITY
    assert raw.analyses[0].assigned_team is Team.SECURITY
    assert raw.analyses[0].assigned_team_confidence.value == 0.7
    assert raw.model == "jev-latest"
    assert len(seen) == 2  # one hosted call per ticket
    auth, path, body = seen[0]
    assert auth == "Bearer k"
    assert path == "/v1/systemone"
    q = body["questions"]
    assert set(q["severity"]["criteria"]) == {s.value for s in Severity}
    assert set(q["category"]["criteria"]) == {c.value for c in Category}
    assert set(q["assigned_team"]["criteria"]) == {t.value for t in Team}
    assert "options" not in q["assigned_team"]
    assert "options" not in q["severity"]
    assert body["state"] == {"id": "A", "title": "Leak", "description": "d"}
    assert body["model"] == "jev-latest"


@pytest.mark.parametrize("status", [401, 429, 500])
def test_http_errors_become_classifier_unavailable(status):
    backend = make_backend(lambda r: httpx.Response(status, json={"error": "x"}))
    with pytest.raises(ClassifierUnavailable):
        OpenJevTicketClassifier(backend).classify_many(
            [Ticket(id="A", title="t", description="d")]
        )


def test_build_backend_requires_api_key():
    with pytest.raises(RuntimeError, match="JEV_API_KEY"):
        build_backend(Settings(backend="jev", api_key=None, _env_file=None))


def test_build_backend_jev_with_key():
    settings = Settings(backend="jev", api_key=SecretStr("k"), _env_file=None)
    assert isinstance(build_backend(settings), JevBackend)
