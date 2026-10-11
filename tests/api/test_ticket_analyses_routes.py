import pytest
from fastapi.testclient import TestClient

from jev_playground.main import create_app
from jev_playground.modules.ticket_analysis.api.dependencies import get_classifier
from jev_playground.modules.ticket_analysis.domain.errors import ClassifierUnavailable
from tests.conftest import AUTH, make_settings

URL = "/api/v1/ticket-analyses"


def ticket(id="JEV-001", **kw):
    return {"id": id, "title": "API returns 500", "description": "All users fail", **kw}


def post(client, *tickets, **kw):
    return client.post(URL, json={"tickets": list(tickets)}, **kw)


def test_happy_path_returns_results_in_input_order(client):
    r = post(
        client,
        ticket("B", environment="production", evidence=["errors at 100%"]),
        ticket("A", business_impact="All customers blocked"),
    )
    assert r.status_code == 200
    body = r.json()
    assert [x["id"] for x in body["results"]] == ["B", "A"]
    for x in body["results"]:
        assert x["severity"]["label"] in {
            "critical",
            "high",
            "medium",
            "low",
            "unknown",
        }
        assert 0 <= x["category"]["confidence"] <= 1
        assert x["assigned_team"]["label"] in {
            "backend",
            "frontend",
            "devops",
            "security",
            "product_management",
            "tech_support",
            "payments_financial_systems",
        }
        assert 0 <= x["assigned_team"]["confidence"] <= 1
    assert body["model"] == "openjev-mock"
    assert "x-request-id" in r.headers


def test_empty_batch_is_422(client):
    assert client.post(URL, json={"tickets": []}).status_code == 422


def test_oversized_batch_is_422(client):
    r = post(client, *[ticket(str(i)) for i in range(21)])
    assert r.status_code == 422


def test_duplicate_ids_are_422_problem_json(client):
    r = post(client, ticket("A"), ticket("A"))
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["code"] == "invalid_batch"


def test_whitespace_title_is_422_problem_json(client):
    r = post(client, ticket(title="   "))
    assert r.status_code == 422
    assert r.json()["code"] == "invalid_ticket"


def test_oversized_description_is_422(client):
    assert post(client, ticket(description="x" * 10_001)).status_code == 422


def test_missing_required_field_is_422(client):
    assert client.post(URL, json={"tickets": [{"id": "A"}]}).status_code == 422


@pytest.mark.parametrize("label", ["severity", "category", "assigned_team"])
def test_labels_cannot_be_sent_as_input(client, label):
    assert post(client, ticket(**{label: "high"})).status_code == 422


def test_extra_top_level_fields_forbidden(client):
    assert client.post(URL, json={"tickets": [ticket()], "x": 1}).status_code == 422


def test_old_single_ticket_shape_is_rejected(client):
    assert client.post(URL, json={"ticket": "help"}).status_code == 422


def test_classifier_failure_is_503():
    class Failing:
        def classify_many(self, tickets):
            raise ClassifierUnavailable()

    app = create_app(make_settings())
    app.dependency_overrides[get_classifier] = lambda: Failing()
    with TestClient(app, headers=AUTH) as c:
        r = post(c, ticket())
    assert r.status_code == 503
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["code"] == "classifier_unavailable"


def test_unexpected_error_is_generic_500():
    class Exploding:
        def classify_many(self, tickets):
            raise RuntimeError("secret internals")

    app = create_app(make_settings(log_level="CRITICAL"))
    app.dependency_overrides[get_classifier] = lambda: Exploding()
    with TestClient(app, raise_server_exceptions=False, headers=AUTH) as c:
        r = post(c, ticket())
    assert r.status_code == 500
    assert "secret" not in r.text
    assert r.json()["code"] == "internal_error"


def test_health(client):
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").json() == {"ready": True}


def test_not_ready_before_lifespan():
    app = create_app(make_settings())
    r = TestClient(app).get("/health/ready")  # no context manager: lifespan not run
    assert r.status_code == 503
    assert r.json() == {"ready": False}


def test_docs_enabled_by_default(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_root_redirects_to_docs_without_a_key(client):
    r = TestClient(client.app).get("/", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/docs"


def test_root_is_404_when_docs_not_exposed():
    app = create_app(make_settings(expose_docs=False))
    with TestClient(app) as c:
        assert c.get("/").status_code == 404


def test_docs_disabled_when_not_exposed():
    app = create_app(make_settings(expose_docs=False))
    with TestClient(app, headers=AUTH) as c:
        assert c.get("/docs").status_code == 404
        assert c.get("/redoc").status_code == 404
        assert c.get("/openapi.json").status_code == 404
