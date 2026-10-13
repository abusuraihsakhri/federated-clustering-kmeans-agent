"""FastAPI route-level regression tests (synthetic data only)."""
from fastapi.testclient import TestClient
from agents.api import app

client = TestClient(app)


def test_health_and_console():
    assert client.get("/health").status_code == 200
    page = client.get("/console/index.html")
    assert page.status_code == 200
    assert "No audit result was generated" in page.text


def test_clustering_endpoint():
    response = client.post("/api/cluster", json={
        "sites": [[[0, 0], [0, 2]], [[10, 10], [10, 12]]],
        "initial_centroids": [[0, 0], [10, 10]],
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["centroids"] == [[0, 1], [10, 11]]
    assert data["inertia"] == 4


def test_clustering_rejects_inconsistent_dimensions():
    result = client.post("/api/cluster", json={
        "sites": [[[0, 0]]],
        "initial_centroids": [[0]],
    })
    assert result.status_code == 422


def test_audit_rejects_nested_email():
    result = client.post("/api/audit", json={
        "task_id": "TEST-01",
        "target_identifier": "KEY-01",
        "primary_metric": 1,
        "attributes": {"nested": {"email": "patient@example.com"}}
    })
    assert result.status_code == 422
    assert "patient@example.com" not in result.text
