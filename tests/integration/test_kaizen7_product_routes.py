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


def test_product_readiness_route_returns_ready_score(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/product/readiness")

    assert resp.status_code == 200
    body = resp.json()["readiness"]
    assert body["status"] == "ready"
    assert body["score"] >= 90
    assert body["counts"]["capabilities"] == 19
    assert body["execution_enabled"] is False
