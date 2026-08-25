"""Integration tests for the KAIZEN7 mobile companion routes."""
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


def test_mobile_status_route_is_mounted() -> None:
    with client() as c:
        resp = c.get("/api/mobile/status")

    assert resp.status_code == 200
    assert resp.json()["product"] == "KAIZEN7 Mobile Companion"
