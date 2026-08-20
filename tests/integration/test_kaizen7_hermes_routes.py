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


def test_hermes_status_route_is_mounted(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KAIZEN7_HERMES_CLI", "missing-hermes")

    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/hermes/status")

    assert resp.status_code == 200
    body = resp.json()
    assert body["installed"] is False
    assert body["execution_enabled"] is False


def test_hermes_profiles_route_is_mounted(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KAIZEN7_HERMES_CLI", "missing-hermes")

    with _client(tmp_path) as client:
        resp = client.get("/api/kaizen7/hermes/profiles")

    assert resp.status_code == 200
    body = resp.json()
    assert body["execution_enabled"] is False
    assert body["profiles"] == []
