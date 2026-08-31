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


def test_growth_command_route_returns_operating_card(tmp_path) -> None:
    with _client(tmp_path) as client:
        response = client.post(
            "/api/kaizen7/growth/command",
            json={
                "objective": "Monetize THE FOCUX with viral content and ecommerce",
                "business": "THE FOCUX",
                "audience": "premium buyers",
                "channels": ["instagram", "youtube"],
                "assets": ["logo", "product", "proof"],
            },
        )

    assert response.status_code == 200
    card = response.json()["growth_command"]
    assert card["schema_version"] == "kaizen7.growth_command.v1"
    assert card["asset_to_create"]["mode"] == "draft_only"
    assert card["distribution_plan"]["publishing_enabled"] is False


def test_launch_kit_route_returns_installable_onboarding(tmp_path) -> None:
    with _client(tmp_path) as client:
        response = client.post(
            "/api/kaizen7/growth/launch-kit",
            json={
                "objective": "Help a new user monetize with KAIZEN7 Jarvis",
                "business": "KAIZEN7 Jarvis",
                "audience": "solo builders",
            },
        )

    assert response.status_code == 200
    kit = response.json()["launch_kit"]
    assert kit["schema_version"] == "kaizen7.launch_kit.v1"
    assert kit["five_minute_start"][0]["command"]
    assert kit["demo_payload"]["business"] == "KAIZEN7 Jarvis"


def test_growth_asset_and_ecommerce_audit_routes(tmp_path) -> None:
    with _client(tmp_path) as client:
        asset = client.post(
            "/api/kaizen7/growth/asset",
            json={
                "objective": "Create a viral ecommerce launch",
                "business": "THE FOCUX",
                "audience": "premium buyers",
                "channels": ["tiktok"],
            },
        )
        audit = client.post(
            "/api/kaizen7/growth/ecommerce-audit",
            json={
                "business": "THE FOCUX",
                "assets": ["logo", "product"],
            },
        )

    assert asset.status_code == 200
    assert asset.json()["growth_asset"]["asset"]["type"] == "short_video_script"
    assert audit.status_code == 200
    assert audit.json()["ecommerce_audit"]["checks"]["agent_readable"]["status"] == "missing"


def test_growth_propose_route_records_receipt(tmp_path) -> None:
    with _client(tmp_path) as client:
        proposed = client.post(
            "/api/kaizen7/growth/propose",
            json={
                "objective": "Create the first Growth OS proposal",
                "business": "THE FOCUX",
                "audience": "premium buyers",
            },
        )
        receipts = client.get("/api/kaizen7/bridge/receipts")

    assert proposed.status_code == 200
    assert proposed.json()["proposal"]["execution_enabled"] is False
    assert receipts.json()["receipts"][0]["kind"] == "growth_os_proposal"
