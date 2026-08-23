from __future__ import annotations

from jarvis.kaizen7.market_blueprint import (
    default_market_blueprint,
    market_upgrade_plan,
)


def test_market_blueprint_tracks_best_open_patterns_without_copying_code() -> None:
    blueprint = default_market_blueprint()

    patterns = blueprint.list()
    ids = {pattern["id"] for pattern in patterns}

    assert {
        "operator-agent",
        "plugin-marketplace",
        "visual-workflows",
        "local-knowledge",
        "mcp-connectors",
        "quality-evals",
        "rowbot-agent-os",
        "openyak-workspace",
        "pioneer-gateway",
        "dax-policy-core",
        "opendex-voice-ux",
        "somi-control-room",
    } <= ids
    assert all(pattern["copy_code"] is False for pattern in patterns)
    assert all(pattern["license_posture"] in {"compatible-pattern", "reference-only"} for pattern in patterns)


def test_market_upgrade_plan_prioritizes_product_ready_capabilities() -> None:
    plan = market_upgrade_plan()

    assert plan["mode"] == "proposal_only"
    assert plan["execution_enabled"] is False
    assert [item["capability_id"] for item in plan["recommended_now"]][:6] == [
        "daily-focus",
        "governed-memory",
        "knowledge-graph-memory",
        "multi-device-command",
        "mcp-connector-plan",
        "quality-evaluation",
    ]
    assert any(item["source_pattern"] == "plugin-marketplace" for item in plan["backlog"])


def test_market_upgrade_plan_has_next_gen_product_pack() -> None:
    plan = market_upgrade_plan()

    next_gen = {item["capability_id"] for item in plan["recommended_now"]}

    assert {
        "knowledge-graph-memory",
        "multi-device-command",
        "context-compaction",
        "workflow-console",
        "developer-studio",
        "designer-studio",
    } <= next_gen


def test_market_blueprint_explains_rejections() -> None:
    blueprint = default_market_blueprint()

    rejected = blueprint.rejected()

    assert any(item["reason"] == "too heavy for default install" for item in rejected)
    assert any(item["reason"] == "requires credentials or external publishing approval" for item in rejected)
