"""KAIZEN7 Agent OS planner.

The planner converts the marketplace into a phased product plan. It is still
proposal-only: no provider is called and no external action is executed.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from jarvis.kaizen7.bridge import APPROVAL_REQUIRED_FOR, ControlBridgeStore, _utc_now
from jarvis.kaizen7.capabilities import default_capability_registry
from jarvis.kaizen7.providers import default_provider_registry


def build_agent_os_plan(
    mission: str,
    *,
    needs: tuple[str, ...] | list[str] = (),
    constraints: tuple[str, ...] | list[str] = (),
    bridge: ControlBridgeStore | None = None,
) -> dict[str, Any]:
    clean_mission = " ".join(mission.strip().split())
    if not clean_mission:
        raise ValueError("mission cannot be blank.")

    needs_list = list(needs)
    constraints_list = list(constraints)
    capability_registry = default_capability_registry()
    provider_registry = default_provider_registry()
    launch = capability_registry.launch_plan(
        clean_mission,
        needs=needs_list,
        constraints=constraints_list,
    )
    capability_by_id = {item["id"]: item for item in capability_registry.list()}
    provider_recommendation = provider_registry.recommend(
        clean_mission,
        needs=needs_list,
        constraints=constraints_list,
    )

    phases = [
        _phase(
            "stabilize",
            "Stabilize the operating core",
            ("daily-focus", "governed-memory", "knowledge-graph-memory", "quality-evaluation"),
            launch,
            capability_by_id,
        ),
        _phase(
            "operate",
            "Operate from desktop and mobile",
            (
                "multi-device-command",
                "context-compaction",
                "workflow-console",
                "developer-studio",
                "skill-forge",
            ),
            launch,
            capability_by_id,
        ),
        _phase(
            "grow",
            "Grow business and content output",
            ("business-research", "content-pipeline", "designer-studio", "mcp-connector-plan"),
            launch,
            capability_by_id,
        ),
    ]
    phases = [phase for phase in phases if phase["capabilities"]]
    readiness_score = _readiness_score(phases, provider_recommendation)
    plan = {
        "id": f"agent-os-plan-{uuid4().hex}",
        "mission": clean_mission,
        "needs": sorted({_clean(item) for item in needs_list if _clean(item)}),
        "constraints": sorted({_clean(item) for item in constraints_list if _clean(item)}),
        "readiness_score": readiness_score,
        "provider_recommendation": provider_recommendation["selected"],
        "phases": phases,
        "approval_required_for": sorted(set(APPROVAL_REQUIRED_FOR)),
        "mode": "proposal_only",
        "execution_enabled": False,
        "requires_human_approval": True,
        "receipt_id": None,
        "created_at": _utc_now(),
    }
    if bridge is not None:
        receipt_id = f"agent-os-{uuid4().hex}"
        bridge.record_receipt(
            {
                "id": receipt_id,
                "kind": "agent_os_plan",
                "message": clean_mission,
                "result": f"{len(phases)} phases, score {readiness_score}",
                "status": "recorded",
                "execution_enabled": False,
                "created_at": plan["created_at"],
            }
        )
        plan["receipt_id"] = receipt_id
    return plan


def _phase(
    phase_id: str,
    title: str,
    capability_ids: tuple[str, ...],
    launch: dict[str, Any],
    capability_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    launched = {step["capability_id"]: step for step in launch["steps"]}
    capabilities: list[dict[str, Any]] = []
    for capability_id in capability_ids:
        step = launched.get(capability_id)
        capability = capability_by_id.get(capability_id)
        if not capability:
            continue
        reason = step["reason"] if step else "baseline Agent OS capability"
        capabilities.append(
            {
                "capability_id": capability_id,
                "title": capability["title"],
                "provider_id": capability["provider_id"],
                "privacy": capability["privacy"],
                "cost": capability["cost"],
                "reason": reason,
                "mode": "proposal_only",
                "execution_enabled": False,
            }
        )
    return {"id": phase_id, "title": title, "capabilities": capabilities}


def _readiness_score(phases: list[dict[str, Any]], provider_recommendation: dict[str, Any]) -> int:
    capability_count = sum(len(phase["capabilities"]) for phase in phases)
    score = min(95, 50 + capability_count * 6)
    if provider_recommendation.get("selected"):
        score += 5
    return min(score, 100)


def _clean(value: str) -> str:
    return str(value).strip().lower().replace("_", "-")
