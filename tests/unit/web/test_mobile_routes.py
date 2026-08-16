"""Mobile companion API contract tests."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from jarvis.ui.web.mobile_routes import router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_mobile_status_is_read_only_and_names_safety_boundaries() -> None:
    client = _client()

    resp = client.get("/api/mobile/status")

    assert resp.status_code == 200
    body = resp.json()
    assert body["product"] == "KAIZEN7 Mobile Companion"
    assert body["mode"] == "companion"
    assert "chat" in body["capabilities"]
    assert "approvals" in body["capabilities"]
    assert "payments" in body["human_approval_required_for"]
    assert body["execution"]["can_execute"] is False
    assert body["execution"]["reason"] == "mobile_companion_recommend_only"


def test_mobile_pairing_challenge_is_short_lived_and_does_not_expose_token() -> None:
    client = _client()

    resp = client.post("/api/mobile/pairing/challenge")

    assert resp.status_code == 201
    body = resp.json()
    assert body["expires_in_seconds"] <= 600
    assert body["pairing_url"].startswith("/mobile/pair?")
    assert "token" not in body
    assert len(body["code"].replace("-", "")) >= 8


def test_mobile_intent_records_pending_approval_instead_of_executing() -> None:
    client = _client()

    resp = client.post(
        "/api/mobile/intents",
        json={"text": "Publish this offer and charge the customer"},
    )

    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "approval_required"
    assert body["execution"]["executed"] is False
    assert "public posts" in body["approval_required_for"]
    assert "payments" in body["approval_required_for"]
    assert body["receipt"]["source"] == "mobile_companion"
