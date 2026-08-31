from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis.kaizen7.agent_os_planner import build_agent_os_plan
from jarvis.kaizen7.bridge import ControlBridgeStore


def _config(tmp_path):
    return SimpleNamespace(memory=SimpleNamespace(data_dir=tmp_path))


def test_agent_os_plan_turns_mission_into_phased_product_plan() -> None:
    plan = build_agent_os_plan(
        "Make KAIZEN7 Jarvis useful from mobile, with memory, coding and content",
        needs=("mobile", "memory", "code", "content", "workflow"),
        constraints=("no_paid_api",),
    )

    assert plan["mode"] == "proposal_only"
    assert plan["execution_enabled"] is False
    assert plan["requires_human_approval"] is True
    assert plan["readiness_score"] >= 80
    assert [phase["id"] for phase in plan["phases"]] == [
        "stabilize",
        "operate",
        "grow",
    ]
    phase_capabilities = {
        capability["capability_id"]
        for phase in plan["phases"]
        for capability in phase["capabilities"]
    }
    assert {
        "daily-focus",
        "governed-memory",
        "knowledge-graph-memory",
        "multi-device-command",
            "developer-studio",
            "content-pipeline",
            "workflow-console",
            "skill-forge",
        } <= phase_capabilities


def test_agent_os_plan_includes_skill_forge_for_agent_skill_work() -> None:
    plan = build_agent_os_plan(
        "Build reusable skills for research, coding and business execution",
        needs=("skills", "agents", "tests"),
        constraints=("no_paid_api",),
    )

    phase_capabilities = {
        capability["capability_id"]
        for phase in plan["phases"]
        for capability in phase["capabilities"]
    }
    assert "skill-forge" in phase_capabilities
    assert plan["execution_enabled"] is False


def test_agent_os_plan_records_receipt_when_bridge_is_supplied(tmp_path) -> None:
    bridge = ControlBridgeStore.from_config(_config(tmp_path))

    plan = build_agent_os_plan(
        "Prepare a safe market-ready Jarvis upgrade",
        needs=("memory", "mobile", "quality"),
        bridge=bridge,
    )

    receipts = bridge.receipts()
    assert plan["receipt_id"] == receipts[0]["id"]
    assert receipts[0]["kind"] == "agent_os_plan"
    assert receipts[0]["execution_enabled"] is False


def test_agent_os_plan_rejects_blank_mission() -> None:
    with pytest.raises(ValueError, match="mission cannot be blank"):
        build_agent_os_plan("   ")
