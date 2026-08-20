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


def test_codex_status_route_is_mounted(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KAIZEN7_CODEX_CLI", "missing-codex")

    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/codex/status")

    assert resp.status_code == 200
    body = resp.json()
    assert body["installed"] is False
    assert body["execution_enabled"] is False
    assert body["requires_git_repo"] is True
    assert body["requires_pty"] is True


def test_codex_capabilities_route_is_proposal_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KAIZEN7_CODEX_CLI", "missing-codex")

    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/codex/capabilities")

    assert resp.status_code == 200
    body = resp.json()
    assert body["execution_enabled"] is False
    assert {cap["id"] for cap in body["capabilities"]} >= {
        "codex-version",
        "codex-exec",
        "codex-review",
    }
    assert all(cap["requires_approval"] for cap in body["capabilities"] if cap["id"] != "codex-version")


def test_codex_delegate_proposal_records_receipt(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KAIZEN7_CODEX_CLI", "missing-codex")

    with _client(tmp_path) as client:
        resp = client.post(
            "/api/kaizen7/codex/delegate/propose",
            json={
                "workdir": "C:/repo/project",
                "prompt": "Fix the failing tests and report the diff.",
                "sandbox": "workspace-write",
            },
        )
        receipts = client.get("/api/kaizen7/bridge/receipts")

    assert resp.status_code == 200
    proposal = resp.json()["proposal"]
    assert proposal["executed"] is False
    assert proposal["requires_approval"] is True
    assert proposal["command"] == [
        "missing-codex",
        "exec",
        "--sandbox",
        "workspace-write",
        "Fix the failing tests and report the diff.",
    ]
    assert proposal["workdir"] == "C:/repo/project"
    assert receipts.json()["receipts"][0]["kind"] == "codex_delegate_proposal"
