from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

import jarvis.core.config as core_config
from jarvis.brain import modes
from jarvis.core.bus import EventBus
from jarvis.core.config import JarvisConfig
from jarvis.ui.web.server import WebServer


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_config, "DATA_DIR", tmp_path)
    modes.set_section_override(None)


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


def test_bots_roster_route_is_mounted(tmp_path) -> None:
    modes.save_mode(
        slug="operator",
        name="Operator",
        description="Coordinates work.",
        character="Coordinate, verify, report.",
    )

    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/bots")

    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "assistant_modes"
    assert body["execution_enabled"] is False
    assert "operator" in {bot["slug"] for bot in body["bots"]}


def test_bot_create_proposal_route_records_a_receipt(tmp_path) -> None:
    with _client(tmp_path) as client:
        created = client.post(
            "/api/kaizen7/bots/propose",
            json={
                "name": "Market Scout",
                "title": "Market Scout",
                "description": "Researches sources before action.",
            },
        )
        receipts = client.get("/api/kaizen7/bridge/receipts")

    assert created.status_code == 200
    proposal = created.json()["proposal"]
    assert proposal["draft"]["slug"] == "market-scout"
    assert proposal["execution_enabled"] is False
    assert receipts.status_code == 200
    assert receipts.json()["count"] == 1
    assert receipts.json()["receipts"][0]["kind"] == "bot_create_proposal"
