"""Tests for the telemetry endpoint."""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.telemetry import router as telemetry_router

test_app = FastAPI()
test_app.include_router(telemetry_router)


class TestTelemetryEndpoint:
    def test_post_telemetry_no_events(self):
        with TestClient(test_app) as client:
            resp = client.post("/api/telemetry", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["count"] == "0"

    def test_post_telemetry_with_events(self):
        events = [
            {"type": "api_call", "name": "fetch_data", "duration": 150, "status": 200},
            {"type": "page_view", "name": "/home"},
            {"type": "error", "name": "TypeError"},
            {"type": "web_vital", "name": "LCP", "duration": 2500},
            {"type": "unknown_event", "name": "some_custom"},
        ]
        with TestClient(test_app) as client:
            resp = client.post("/api/telemetry", json={"events": events})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["count"] == "5"

    def test_post_telemetry_invalid_json(self):
        with TestClient(test_app) as client:
            resp = client.post("/api/telemetry", content=b"not json", headers={"content-type": "application/json"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
