from __future__ import annotations

from types import SimpleNamespace

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.product_readiness import (
    build_product_readiness,
    render_product_readiness,
)


def _config(tmp_path):
    return SimpleNamespace(memory=SimpleNamespace(data_dir=tmp_path))


def test_product_readiness_scores_real_product_surfaces(tmp_path) -> None:
    readiness = build_product_readiness(
        config=_config(tmp_path),
        bridge=ControlBridgeStore.from_config(_config(tmp_path)),
    )

    assert readiness["score"] >= 90
    assert readiness["status"] == "ready"
    assert readiness["execution_enabled"] is False
    assert readiness["requires_human_approval"] is True
    assert readiness["counts"] == {
        "adapters": 6,
        "providers": 4,
        "capabilities": 19,
        "market_patterns": 16,
    }
    categories = {item["category"] for item in readiness["checks"]}
    assert {
        "install",
        "security",
        "product",
        "api",
        "documentation",
        "testing",
    } <= categories


def test_product_readiness_renderer_is_actionable(tmp_path) -> None:
    readiness = build_product_readiness(
        config=_config(tmp_path),
        bridge=ControlBridgeStore.from_config(_config(tmp_path)),
    )

    rendered = render_product_readiness(readiness)

    assert "KAIZEN7 Jarvis - product readiness" in rendered
    assert "RESULT: READY" in rendered
    assert "6 adapters" in rendered
    assert "19 capabilities" in rendered
    assert "no execution without approval" in rendered
