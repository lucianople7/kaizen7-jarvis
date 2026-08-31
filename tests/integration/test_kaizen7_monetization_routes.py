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


def test_monetization_routes_list_playbooks_and_build_pack(tmp_path) -> None:
    with _client(tmp_path) as client:
        playbooks = client.get("/api/kaizen7/monetization/playbooks")
        pack = client.post(
            "/api/kaizen7/monetization/pack",
            json={
                "objective": "Monetize a Jarvis product with viral content and ecommerce",
                "business": "KAIZEN7 Jarvis",
                "audience": "builders and small businesses",
                "needs": ["content", "ecommerce", "monetization"],
                "constraints": ["no_paid_ads"],
            },
        )

    assert playbooks.status_code == 200
    assert playbooks.json()["count"] >= 6
    assert pack.status_code == 200
    body = pack.json()["growth_pack"]
    assert body["primary_lane"] == "ecommerce"
    assert body["execution_enabled"] is False
    assert body["experiments"][0]["metric"]


def test_monetization_quick_route_returns_one_move(tmp_path) -> None:
    with _client(tmp_path) as client:
        quick = client.post(
            "/api/kaizen7/monetization/quick",
            json={
                "objective": "Monetize THE FOCUX with ecommerce and viral content",
                "business": "THE FOCUX",
                "audience": "premium buyers",
            },
        )

    assert quick.status_code == 200
    body = quick.json()["quick_start"]
    assert body["opportunity_score"] >= 80
    assert body["next_move"]["title"]
    assert len(body["quick_actions"]) == 3


def test_monetization_proposal_records_receipt(tmp_path) -> None:
    with _client(tmp_path) as client:
        proposed = client.post(
            "/api/kaizen7/monetization/propose",
            json={
                "objective": "Create the first monetization experiment",
                "business": "THE FOCUX",
                "audience": "premium buyers",
            },
        )
        receipts = client.get("/api/kaizen7/bridge/receipts")

    assert proposed.status_code == 200
    assert proposed.json()["proposal"]["execution_enabled"] is False
    assert receipts.json()["receipts"][0]["kind"] == "monetization_proposal"
