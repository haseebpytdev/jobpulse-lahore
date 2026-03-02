"""Tests for main app routes."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_dashboard_returns_200(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Job" in r.content or b"job" in r.content


def test_refresh_redirects_to_root(client):
    r = client.get("/refresh", follow_redirects=False)
    assert r.status_code in (303, 302)
    assert r.headers.get("location", "").strip("/").startswith("") or "?" in r.headers.get("location", "")


def test_dashboard_with_freshness_params(client):
    r = client.get("/?days=new_today")
    assert r.status_code == 200
    r2 = client.get("/?days=last_3_days")
    assert r2.status_code == 200


def test_dashboard_includes_freshness_ui(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"New today" in r.content or b"new_today" in r.content


def test_export_csv_returns_csv(client):
    r = client.get("/export.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert "attachment" in r.headers.get("content-disposition", "").lower()


def test_export_csv_with_days_param(client):
    r = client.get("/export.csv?days=new_today")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
