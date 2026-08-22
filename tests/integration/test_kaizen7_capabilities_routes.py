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


def test_capabilities_are_exposed_as_safe_marketplace(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/capabilities")

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 6
    assert all(item["execution_enabled"] is False for item in body["capabilities"])


def test_capability_launch_plan_endpoint_returns_ordered_plan(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.post(
            "/api/kaizen7/capabilities/plan",
            json={
                "mission": "Grow THE FOCUX this week",
                "needs": ["focus", "research", "content"],
                "constraints": ["no_paid_api"],
            },
        )

    assert resp.status_code == 200
    plan = resp.json()["plan"]
    assert [step["capability_id"] for step in plan["steps"]][:3] == [
        "daily-focus",
        "business-research",
        "content-pipeline",
    ]
    assert plan["execution_enabled"] is False


def test_capability_launch_plan_rejects_blank_mission(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.post("/api/kaizen7/capabilities/plan", json={"mission": " "})

    assert resp.status_code == 422
