import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(test_client: TestClient):
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "postgres" in data
    assert "redis" in data
    assert data["rules_loaded"] > 0
    assert "ruleset_version" in data

def test_metrics_endpoint(test_client: TestClient):
    response = test_client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "requests_total" in data

def test_rules_endpoint(test_client: TestClient):
    response = test_client.get("/api/v1/rules")
    assert response.status_code == 200
    data = response.json()
    assert "ruleset_version" in data
    assert "rules" in data
    assert len(data["rules"]) > 0

def test_inspect_clean(test_client: TestClient):
    response = test_client.post("/api/v1/inspect", json={
        "method": "GET",
        "path": "/index.html",
        "body": "",
        "headers": {"Host": "localhost"}
    })
    assert response.status_code == 200
    # In mock, proxy forward returns 200 and some body, but test client returns the forward response
    # Or inspect endpoint returns proxy response.
    pass # Adjust as needed based on actual inspect behavior

def test_inspect_sqli(test_client: TestClient):
    response = test_client.post("/api/v1/inspect", json={
        "method": "GET",
        "path": "/search?q=1 UNION SELECT 1,2,3--",
        "body": "",
        "headers": {"Host": "localhost"}
    })
    assert response.status_code == 200
    data = response.json()
    assert not data["allowed"]
    assert data["attack_type"] == "SQLI"
