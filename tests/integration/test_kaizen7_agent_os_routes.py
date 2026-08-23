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


def test_agent_os_plan_endpoint_returns_product_plan_and_receipt(tmp_path) -> None:
    with _client(tmp_path) as client:
        created = client.post(
            "/api/kaizen7/agent-os/plan",
            json={
                "mission": "Make Jarvis useful from mobile with memory and code",
                "needs": ["mobile", "memory", "code"],
                "constraints": ["no_paid_api"],
                "record_receipt": True,
            },
        )
        receipts = client.get("/api/kaizen7/bridge/receipts")

    assert created.status_code == 200
    plan = created.json()["plan"]
    assert plan["execution_enabled"] is False
    assert plan["phases"][0]["id"] == "stabilize"
    assert receipts.json()["receipts"][0]["kind"] == "agent_os_plan"


def test_agent_os_plan_endpoint_rejects_blank_mission(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.post("/api/kaizen7/agent-os/plan", json={"mission": " "})

    assert resp.status_code == 422
