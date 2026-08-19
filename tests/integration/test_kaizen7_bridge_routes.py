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


def test_bridge_status_and_capabilities_are_mounted(tmp_path) -> None:
    with _client(tmp_path) as client:
        status = client.get("/api/kaizen7/bridge/status")
        assert status.status_code == 200
        assert status.json()["mode"] == "recommendation_only"
        assert status.json()["execution_enabled"] is False

        capabilities = client.get("/api/kaizen7/bridge/capabilities")
        assert capabilities.status_code == 200
        body = capabilities.json()
        assert body["count"] == 4
        assert {item["path"] for item in body["capabilities"]} == {
            "/api/kaizen7/bridge/status",
            "/api/kaizen7/bridge/capabilities",
            "/api/kaizen7/bridge/propose",
            "/api/kaizen7/bridge/receipts",
        }
        assert all(item["dangerous"] is False for item in body["capabilities"])


def test_bridge_propose_records_a_readable_receipt(tmp_path) -> None:
    with _client(tmp_path) as client:
        created = client.post(
            "/api/kaizen7/bridge/propose",
            json={"message": "Prepare today's focus without sending anything"},
        )
        assert created.status_code == 200
        proposal = created.json()["proposal"]
        assert proposal["execution_enabled"] is False
        assert proposal["requires_human_approval"] is True

        receipts = client.get("/api/kaizen7/bridge/receipts")
        assert receipts.status_code == 200
        body = receipts.json()
        assert body["count"] == 1
        assert body["receipts"][0]["id"] == proposal["id"]
        assert body["receipts"][0]["message"] == (
            "Prepare today's focus without sending anything"
        )


def test_bridge_rejects_blank_proposals(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.post("/api/kaizen7/bridge/propose", json={"message": "   "})
        assert resp.status_code == 422
