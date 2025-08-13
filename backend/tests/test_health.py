"""
Тесты для health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app


client = TestClient(app)


def test_health_check_success():
    """Тест успешного health check."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "checks" in data
    assert data["checks"]["database"] == "ok"


def test_root_endpoint():
    """Тест корневого endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "version" in data
    assert "health" in data
    assert data["health"] == "/health"


def test_metrics_endpoint():
    """Тест metrics endpoint."""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
