from __future__ import annotations

import os
import types

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("ADMIN_TOKEN", "test-token")

from app.main import create_app  # noqa: E402
from app.core.db import init_db  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    init_db()
    return TestClient(app)


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {os.environ['ADMIN_TOKEN']}"}


def test_health(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200


def test_dashboard(client: TestClient) -> None:
    resp = client.get("/api/v1/admin/dashboard", headers=_auth())
    assert resp.status_code == 200
    data = resp.json()
    assert {"agents", "tasks_open", "prs_open", "risks_open"}.issubset(data.keys())


def test_tasks_crud_min(client: TestClient) -> None:
    # create
    resp = client.post(
        "/api/v1/admin/tasks",
        json={"title": "Test", "description": "desc"},
        headers=_auth(),
    )
    assert resp.status_code == 201
    task = resp.json()
    # list
    resp = client.get("/api/v1/admin/tasks", headers=_auth())
    assert resp.status_code == 200
    assert any(t["id"] == task["id"] for t in resp.json())


def test_risks_crud(client: TestClient) -> None:
    # create
    resp = client.post(
        "/api/v1/admin/risks",
        json={"title": "R1", "level": "high"},
        headers=_auth(),
    )
    assert resp.status_code == 201
    body = resp.json()
    rid = body["id"]
    # get
    resp = client.get(f"/api/v1/admin/risks/{rid}", headers=_auth())
    assert resp.status_code == 200
    # update
    resp = client.put(
        f"/api/v1/admin/risks/{rid}",
        json={"title": "R2", "level": "medium"},
        headers=_auth(),
    )
    assert resp.status_code == 200
    # list
    resp = client.get("/api/v1/admin/risks", headers=_auth())
    assert resp.status_code == 200
    # delete
    resp = client.delete(f"/api/v1/admin/risks/{rid}", headers=_auth())
    assert resp.status_code == 204


