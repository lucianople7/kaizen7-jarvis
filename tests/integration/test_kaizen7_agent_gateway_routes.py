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


def test_agent_gateway_lists_passports_and_manifest(tmp_path) -> None:
    with _client(tmp_path) as client:
        agents = client.get("/api/kaizen7/agents")
        manifest = client.get("/api/kaizen7/agents/manifest")

    assert agents.status_code == 200
    assert agents.json()["count"] >= 7
    assert all(agent["execution_enabled"] is False for agent in agents.json()["agents"])
    assert manifest.status_code == 200
    assert manifest.json()["manifest"]["schema_version"] == "kaizen7.agent_gateway.v1"
    assert "sk-" not in str(manifest.json())


def test_agent_gateway_recommend_bench_and_propose_flow(tmp_path) -> None:
    with _client(tmp_path) as client:
        recommended = client.post(
            "/api/kaizen7/agents/recommend",
            json={
                "mission": "Fix private code with tests",
                "needs": ["code", "tests", "local"],
                "constraints": ["local_only"],
            },
        )
        bench = client.post("/api/kaizen7/agents/codex-cli/bench", json={})
        proposed = client.post(
            "/api/kaizen7/agents/codex-cli/propose",
            json={
                "message": "Prepare a bounded coding handoff",
                "context": {"workdir": "C:/repo"},
            },
        )
        receipts = client.get("/api/kaizen7/bridge/receipts")

    assert recommended.status_code == 200
    assert recommended.json()["recommendation"]["selected"]["id"] == "codex-cli"
    assert bench.status_code == 200
    assert bench.json()["bench"]["dry_run"] is True
    assert proposed.status_code == 200
    assert proposed.json()["proposal"]["execution_enabled"] is False
    assert receipts.json()["receipts"][0]["kind"] == "agent_proposal"
