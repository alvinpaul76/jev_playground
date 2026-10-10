import pytest
from fastapi.testclient import TestClient

from jev_playground.config import Settings
from jev_playground.main import create_app

TEST_KEY = "test-key-0123456789-0123456789-abcdef"
AUTH = {"X-API-Key": TEST_KEY}


def make_settings(**overrides) -> Settings:
    values = {
        "log_level": "WARNING",
        "backend": "mock",
        "expose_docs": True,
        "client_api_keys": [TEST_KEY],
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture
def client():
    with TestClient(create_app(make_settings()), headers=AUTH) as c:
        yield c
