import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from jev_playground.config import Settings
from jev_playground.main import create_app
from tests.conftest import AUTH, TEST_KEY, make_settings

URL = "/api/v1/ticket-analyses"
BODY = {
    "tickets": [{"id": "A", "title": "Stripe is down", "description": "Payments fail"}]
}
SECOND_KEY = "second-key-0123456789-0123456789-xyz"


def test_missing_key_is_401():
    with TestClient(create_app(make_settings())) as c:
        r = c.post(URL, json=BODY)
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.headers["www-authenticate"] == "ApiKey"
    assert r.json()["code"] == "unauthorized"


def test_wrong_key_looks_identical_to_missing_key():
    with TestClient(create_app(make_settings())) as c:
        missing = c.post(URL, json=BODY)
        wrong = c.post(URL, json=BODY, headers={"X-API-Key": "x" * 40})
    assert wrong.status_code == 401
    strip = lambda r: {k: v for k, v in r.json().items() if k != "request_id"}
    assert strip(wrong) == strip(missing)


def test_valid_key_is_200():
    with TestClient(create_app(make_settings())) as c:
        assert c.post(URL, json=BODY, headers=AUTH).status_code == 200


def test_any_configured_key_works_for_rotation():
    app = create_app(make_settings(client_api_keys=[TEST_KEY, SECOND_KEY]))
    with TestClient(app) as c:
        assert c.post(URL, json=BODY, headers=AUTH).status_code == 200
        assert (
            c.post(URL, json=BODY, headers={"X-API-Key": SECOND_KEY}).status_code == 200
        )


def test_key_is_checked_before_body_validation():
    with TestClient(create_app(make_settings())) as c:
        assert c.post(URL, json={"tickets": []}).status_code == 401


def test_health_needs_no_key():
    with TestClient(create_app(make_settings())) as c:
        assert c.get("/health/live").status_code == 200
        assert c.get("/health/ready").status_code == 200


def test_openapi_advertises_the_key_scheme():
    with TestClient(create_app(make_settings())) as c:
        schemes = c.get("/openapi.json").json()["components"]["securitySchemes"]
    assert schemes["APIKeyHeader"]["name"] == "X-API-Key"


def test_app_refuses_to_start_without_keys():
    with pytest.raises(RuntimeError, match="JEV_CLIENT_API_KEYS"):
        create_app(make_settings(client_api_keys=[]))


def test_auth_disabled_allows_requests_without_key():
    with TestClient(create_app(make_settings(auth_enabled=False))) as c:
        assert c.post(URL, json=BODY).status_code == 200


def test_auth_disabled_starts_without_keys(caplog):
    app = create_app(make_settings(auth_enabled=False, client_api_keys=[]))
    with TestClient(app) as c:
        assert c.post(URL, json=BODY).status_code == 200
    assert "JEV_AUTH_ENABLED=false" in caplog.text


def test_auth_disabled_still_validates_body():
    with TestClient(create_app(make_settings(auth_enabled=False))) as c:
        assert c.post(URL, json={"tickets": []}).status_code == 422


def test_auth_is_enabled_by_default():
    assert Settings(_env_file=None).auth_enabled is True


def test_auth_enabled_parses_from_env(monkeypatch):
    monkeypatch.setenv("JEV_AUTH_ENABLED", "false")
    assert Settings(_env_file=None).auth_enabled is False


def test_short_key_is_rejected():
    with pytest.raises(ValidationError):
        Settings(client_api_keys=["short"], _env_file=None)


def test_keys_parse_from_comma_separated_env(monkeypatch):
    monkeypatch.setenv("JEV_CLIENT_API_KEYS", f" {TEST_KEY} , {SECOND_KEY} ,")
    settings = Settings(_env_file=None)
    assert [k.get_secret_value() for k in settings.client_api_keys] == [
        TEST_KEY,
        SECOND_KEY,
    ]
