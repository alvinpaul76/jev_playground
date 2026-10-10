import threading

from fastapi.testclient import TestClient

from jev_playground.config import Settings
from jev_playground.main import create_app
from jev_playground.modules.ticket_analysis.api.dependencies import get_classifier
from jev_playground.modules.ticket_analysis.domain.errors import ClassifierUnavailable
from tests.conftest import AUTH, make_settings

URL = "/api/v1/ticket-analyses"
TICKET = {"id": "A", "title": "Stripe is down", "description": "Payments fail"}
BODY = {"tickets": [TICKET]}


# --- classifier lifecycle -------------------------------------------------


def test_classifier_is_built_once_in_lifespan():
    app = create_app(make_settings())
    assert app.state.classifier is None  # nothing before startup
    with TestClient(app):
        built = app.state.classifier
        assert built is not None
        assert app.state.classifier is built
    assert app.state.classifier is None  # released on shutdown


def test_concurrent_first_requests_share_one_classifier():
    app = create_app(make_settings())
    with TestClient(app):
        request = type("R", (), {"app": app})()
        seen: list[object] = []
        threads = [
            threading.Thread(target=lambda: seen.append(get_classifier(request)))
            for _ in range(8)
        ]
        [t.start() for t in threads]
        [t.join() for t in threads]
    assert len({id(c) for c in seen}) == 1


def test_dependency_refuses_before_the_model_is_loaded():
    request = type("R", (), {"app": create_app(make_settings())})()
    try:
        get_classifier(request)
    except ClassifierUnavailable:
        return
    raise AssertionError("expected ClassifierUnavailable")


# --- docs default ---------------------------------------------------------


def test_docs_are_off_by_default_in_settings():
    assert Settings(_env_file=None).expose_docs is False


# --- request id -----------------------------------------------------------


def test_safe_request_id_is_echoed(client):
    r = client.get("/health/live", headers={"X-Request-ID": "abc-123_XYZ"})
    assert r.headers["x-request-id"] == "abc-123_XYZ"


def test_unsafe_request_ids_are_replaced(client):
    for bad in ["a" * 65, "id with spaces", "x;y", "tab\there"]:
        r = client.get("/health/live", headers={"X-Request-ID": bad})
        assert r.headers["x-request-id"] != bad
        assert len(r.headers["x-request-id"]) == 32


# --- body size limit ------------------------------------------------------


def test_oversized_body_is_413_problem_json_with_request_id():
    app = create_app(make_settings(max_request_bytes=1_024))
    with TestClient(app, headers=AUTH) as c:
        r = c.post(
            URL, content=b"x" * 2_000, headers={"Content-Type": "application/json"}
        )
    assert r.status_code == 413
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["code"] == "payload_too_large"
    assert r.json()["request_id"] == r.headers["x-request-id"]


def test_chunked_body_over_the_limit_is_413():
    app = create_app(make_settings(max_request_bytes=1_024))

    def chunks():
        for _ in range(5):
            yield b"x" * 500

    with TestClient(app, headers=AUTH) as c:
        r = c.post(URL, content=chunks(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_body_under_the_limit_is_accepted():
    app = create_app(make_settings(max_request_bytes=1_024))
    with TestClient(app, headers=AUTH) as c:
        assert c.post(URL, json=BODY).status_code == 200


def test_size_limit_applies_before_auth_work_is_done():
    # An oversized unauthenticated request is cut off without reading the body.
    app = create_app(make_settings(max_request_bytes=1_024))
    with TestClient(app) as c:
        r = c.post(
            URL, content=b"x" * 2_000, headers={"Content-Type": "application/json"}
        )
    assert r.status_code == 413


# --- validation errors as problem+json ------------------------------------


def test_validation_error_is_problem_json_without_echoing_input(client):
    secret = "do-not-echo-this-value"
    r = client.post(
        URL, json={"tickets": [{"id": "A", "title": 5, "description": secret}]}
    )
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["code"] == "validation_error"
    assert body["errors"] and {"loc", "msg"} == set(body["errors"][0])
    assert secret not in r.text


def test_malformed_json_is_problem_json(client):
    r = client.post(
        URL, content=b"{not json", headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422
    assert r.json()["code"] == "validation_error"


# --- documented responses -------------------------------------------------


def test_error_responses_are_documented_in_openapi(client):
    op = client.get("/openapi.json").json()["paths"][URL]["post"]
    for status in ("401", "413", "422", "500", "503"):
        assert "application/problem+json" in op["responses"][status]["content"]
