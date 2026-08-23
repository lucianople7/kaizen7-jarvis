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


def test_adapters_route_lists_agent_agnostic_connectors(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/adapters")

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 6
    assert all(adapter["execution_enabled"] is False for adapter in body["adapters"])


def test_adapter_manifest_route_is_secret_free(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/adapters/manifest")

    assert resp.status_code == 200
    manifest = resp.json()["manifest"]
    assert manifest["schema_version"] == "kaizen7.adapter.v1"
    assert "sk-" not in str(manifest)


def test_adapter_recommendation_and_proposal_routes(tmp_path) -> None:
    with _client(tmp_path) as client:
        recommended = client.post(
            "/api/kaizen7/adapters/recommend",
            json={
                "mission": "Connect a private local coding agent",
                "needs": ["code", "local"],
                "constraints": ["local_only"],
            },
        )
        proposed = client.post(
            "/api/kaizen7/adapters/generic-cli-agent/propose",
            json={"message": "Prepare a CLI adapter for a new agent"},
        )
        receipts = client.get("/api/kaizen7/bridge/receipts")

    assert recommended.status_code == 200
    assert recommended.json()["recommendation"]["selected"]["id"] == "generic-cli-agent"
    assert proposed.status_code == 200
    assert proposed.json()["proposal"]["execution_enabled"] is False
    assert receipts.json()["receipts"][0]["kind"] == "adapter_proposal"
