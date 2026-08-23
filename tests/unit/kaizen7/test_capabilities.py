from __future__ import annotations

import pytest

from jarvis.kaizen7.capabilities import (
    CapabilityRegistry,
    Kaizen7Capability,
    default_capability_registry,
)


def test_default_capabilities_cover_product_operating_loop() -> None:
    registry = default_capability_registry()

    capabilities = registry.list()

    ids = {capability["id"] for capability in capabilities}
    assert {
        "daily-focus",
        "business-research",
        "content-pipeline",
        "code-repair",
        "mobile-approval",
        "desktop-control-plan",
        "governed-memory",
        "mcp-connector-plan",
        "quality-evaluation",
        "visual-workflow-plan",
        "social-publishing-plan",
        "agent-session-control",
    } <= ids
    assert all(capability["mode"] == "proposal_only" for capability in capabilities)
    assert all(capability["execution_enabled"] is False for capability in capabilities)


def test_marketplace_filters_by_need_and_constraints() -> None:
    registry = default_capability_registry()

    result = registry.match(
        mission="Private local desktop diagnostic",
        needs=("diagnostics",),
        constraints=("local_only", "no_paid_api"),
    )

    assert result["selected"][0]["id"] == "desktop-control-plan"
    assert all(item["privacy"] == "local" for item in result["selected"])
    assert any(item["id"] == "business-research" for item in result["rejected"])


def test_launch_plan_is_ordered_and_requires_approval() -> None:
    registry = default_capability_registry()

    plan = registry.launch_plan(
        "Grow THE FOCUX this week with memory, research and content",
        needs=("focus", "memory", "research", "content"),
        constraints=("no_paid_api",),
    )

    assert plan["mission"] == "Grow THE FOCUX this week with memory, research and content"
    assert [step["capability_id"] for step in plan["steps"]][:4] == [
        "daily-focus",
        "governed-memory",
        "business-research",
        "content-pipeline",
    ]
    assert plan["execution_enabled"] is False
    assert plan["requires_human_approval"] is True
    assert "publishing" in plan["approval_required_for"]


def test_registry_rejects_duplicate_capabilities() -> None:
    registry = CapabilityRegistry()
    capability = Kaizen7Capability(
        id="x",
        title="X",
        provider_id="cli",
        summary="Local test capability.",
        needs=("diagnostics",),
        permissions=("read_local_state",),
        approval_required_for=("destructive_changes",),
        privacy="local",
        cost="local",
    )

    registry.register(capability)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(capability)


def test_blank_launch_plan_mission_is_rejected() -> None:
    registry = default_capability_registry()

    with pytest.raises(ValueError, match="mission cannot be blank"):
        registry.launch_plan("   ")
