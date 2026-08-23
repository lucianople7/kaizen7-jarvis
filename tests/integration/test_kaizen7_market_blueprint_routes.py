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


def test_market_blueprint_route_exposes_absorbed_patterns(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/market-blueprint")

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 6
    assert any(item["id"] == "mcp-connectors" for item in body["patterns"])
    assert all(item["copy_code"] is False for item in body["patterns"])


def test_market_upgrade_plan_route_is_proposal_only(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/market-blueprint/upgrade-plan")

    assert resp.status_code == 200
    plan = resp.json()["plan"]
    assert plan["execution_enabled"] is False
    assert plan["recommended_now"][0]["capability_id"] == "daily-focus"
