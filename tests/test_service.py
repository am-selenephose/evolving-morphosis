import json

import pytest
from fastapi.testclient import TestClient

from morphosis.os.application import MorphosisApplication
from morphosis.os.config import ServiceSettings
from morphosis.os.service import create_app


def make_client(tmp_path):
    app = MorphosisApplication(
        tmp_path / "service.db",
        clock=lambda: "2026-09-20T00:00:00Z",
    )
    settings = ServiceSettings(
        db_path=str(tmp_path / "service.db"),
        request_max_bytes=4096,
        sse_heartbeat_seconds=1,
    )
    return app, TestClient(create_app(settings, app))


def test_health_readiness_metrics_and_security_headers(tmp_path):
    app, http = make_client(tmp_path)
    with http:
        health = http.get("/healthz")
        assert health.status_code == 200
        assert health.json()["version"] == "0.3.0"

        ready = http.get("/readyz")
        assert ready.status_code == 200
        assert ready.json()["ledger"]["integrity"] == "ok"

        metrics = http.get("/metrics")
        assert metrics.status_code == 200
        assert "morphosis_http_requests_total" in metrics.text

        system = http.get("/api/v1/system", headers={"X-Request-ID": "contract-test"})
        assert system.status_code == 200
        assert system.headers["x-request-id"] == "contract-test"
        assert system.headers["x-content-type-options"] == "nosniff"
        assert system.headers["cache-control"] == "no-store"
    app.close()


def test_command_boundary_is_idempotent_and_structured(tmp_path):
    app, http = make_client(tmp_path)
    payload = {
        "model": "future-model-x",
        "provider": "reference",
        "endpoint": "reference://echo",
        "claims": ["future.semantic_patch.v1"],
    }
    envelope = {
        "name": "bootstrap",
        "payload": payload,
        "command_id": "stable-command",
    }
    with http:
        first = http.post("/api/v1/commands", json=envelope)
        second = http.post("/api/v1/commands", json=envelope)
        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()

        rejected = http.post(
            "/api/v1/commands",
            json={"name": "nope", "payload": {}, "command_id": "bad"},
        )
        assert rejected.status_code == 400
        body = rejected.json()["error"]
        assert body["code"] == "COMMAND_REJECTED"
        assert body["request_id"]
    app.close()


def test_unknown_projection_and_request_limit(tmp_path):
    app, http = make_client(tmp_path)
    with http:
        missing = http.get("/api/v1/not-a-projection")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "PROJECTION_NOT_FOUND"

        huge = {
            "name": "bootstrap",
            "payload": {"padding": "x" * 5000},
            "command_id": "huge",
        }
        response = http.post(
            "/api/v1/commands",
            content=json.dumps(huge),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"
    app.close()


def test_bedrock_discovery_enablement_fails_closed_without_region(monkeypatch):
    monkeypatch.setenv("MORPHOSIS_BEDROCK_DISCOVERY", "true")
    monkeypatch.delenv("MORPHOSIS_AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    with pytest.raises(ValueError, match="Bedrock discovery requires"):
        ServiceSettings.from_env()


def test_bedrock_discovery_enablement_uses_explicit_host_region(monkeypatch):
    monkeypatch.setenv("MORPHOSIS_BEDROCK_DISCOVERY", "true")
    monkeypatch.setenv("MORPHOSIS_AWS_REGION", "eu-west-1")
    settings = ServiceSettings.from_env()
    assert settings.bedrock_discovery is True
    assert settings.aws_region == "eu-west-1"
