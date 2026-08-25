"""Integration tests for the KAIZEN7 business capsule route."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient

from jarvis.core.bus import EventBus
from jarvis.core.config import JarvisConfig
from jarvis.ui.web.server import WebServer


@contextmanager
def client() -> Iterator[TestClient]:
    cfg = JarvisConfig()
    cfg.ui.dev_mode = True
    bus = EventBus()
    server = WebServer(cfg, bus=bus)
    server.app.state.config = cfg
    server.app.state.bus = bus
    with TestClient(server.app) as c:
        yield c


def test_business_capsule_route_is_mounted() -> None:
    with client() as c:
        resp = c.get("/api/kaizen7/capsule")

    assert resp.status_code == 200
    body = resp.json()
    assert body["owner"] == "Luciano Lopez Barba"
    assert body["business"]["name"] == "THE FOCUX"
    assert body["active_mission"]["name"] == "Personalized Jarvis for focused execution"
    assert len(body["priorities"]) <= 3
    assert "payments" in body["approval_required_for"]
    assert body["assets"]["mark"].endswith("/kaizen7/the-focux-mark-512.png")
