import json

import pytest

from src.app import app


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_home(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["message"] == "CI/CD Pipeline Generator API"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "healthy"
    assert "services" in data


def test_generate_ci_missing_description(client):
    resp = client.post(
        "/api/generate-ci",
        json={},
        content_type="application/json",
    )
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["status"] == "error"


def test_generate_ci_success(client):
    resp = client.post(
        "/api/generate-ci",
        json={
            "project_description": "A simple Python web application",
            "language": "python",
            "requirements": ["run tests", "lint code"],
        },
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "success"
    assert "pipeline" in data
    assert data["format"] == "github_actions"
