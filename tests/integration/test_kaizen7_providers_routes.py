from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient

from jarvis.core.bus import EventBus
from jarvis.core.config import JarvisConfig
from jarvis.ui.web.server import WebServer


@contextmanager
def _client(tmp_path) -> Iterator[TestClient]:
    cfg = JarvisConfig()
    cfg.ui.dev_mode = True
    cfg.memory.data_dir = tmp_path
    bus = EventBus()
    server = WebServer(cfg, bus=bus)
    server.app.state.config = cfg
    server.app.state.bus = bus
    with TestClient(server.app) as client:
        yield client


def test_providers_are_listed_as_safe_pluggable_connectors(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/providers")

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 3
    ids = {provider["id"] for provider in body["providers"]}
    assert {"hermes", "codex", "api"} <= ids
    assert all(provider["execution_enabled"] is False for provider in body["providers"])


def test_provider_proposal_endpoint_records_receipt(tmp_path) -> None:
    with _client(tmp_path) as client:
        created = client.post(
            "/api/kaizen7/providers/api/propose",
            json={
                "message": "Research agent options without spending money",
                "context": {"capsule": "THE FOCUX"},
            },
        )
        receipts = client.get("/api/kaizen7/bridge/receipts")

    assert created.status_code == 200
    proposal = created.json()["proposal"]
    assert proposal["provider_id"] == "api"
    assert proposal["execution_enabled"] is False
    assert proposal["requires_human_approval"] is True
    assert receipts.json()["receipts"][0]["kind"] == "provider_proposal"


def test_provider_proposal_rejects_blank_message(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.post("/api/kaizen7/providers/api/propose", json={"message": " "})

    assert resp.status_code == 422


def test_provider_recommendation_endpoint_selects_best_safe_connector(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.post(
            "/api/kaizen7/providers/recommend",
            json={
                "mission": "Fix a repository and run tests",
                "needs": ["code", "tests"],
                "constraints": ["no_paid_api"],
            },
        )

    assert resp.status_code == 200
    recommendation = resp.json()["recommendation"]
    assert recommendation["selected"]["id"] == "codex"
    assert recommendation["execution_enabled"] is False
    assert recommendation["requires_human_approval"] is True


def test_provider_recommendation_endpoint_rejects_blank_mission(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.post("/api/kaizen7/providers/recommend", json={"mission": " "})

    assert resp.status_code == 422
