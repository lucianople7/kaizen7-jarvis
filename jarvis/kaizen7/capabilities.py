"""KAIZEN7 capability marketplace.

This is the product layer above providers. Providers are connectors; capabilities
are the useful work surfaces KAIZEN7 can recommend, plan, and govern.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jarvis.kaizen7.bridge import APPROVAL_REQUIRED_FOR


@dataclass(frozen=True)
class Kaizen7Capability:
    id: str
    title: str
    provider_id: str
    summary: str
    needs: tuple[str, ...]
    permissions: tuple[str, ...]
    approval_required_for: tuple[str, ...]
    privacy: str
    cost: str
    maturity: str = "ready"
    mode: str = "proposal_only"
    execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "provider_id": self.provider_id,
            "summary": self.summary,
            "needs": list(self.needs),
            "permissions": list(self.permissions),
            "approval_required_for": list(self.approval_required_for),
            "privacy": self.privacy,
            "cost": self.cost,
            "maturity": self.maturity,
            "mode": self.mode,
            "execution_enabled": self.execution_enabled,
        }


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, Kaizen7Capability] = {}

    def register(self, capability: Kaizen7Capability) -> None:
        capability_id = _clean(capability.id)
        if capability_id in self._capabilities:
            raise ValueError(f"Capability {capability_id!r} is already registered.")
        if capability.execution_enabled:
            raise ValueError("KAIZEN7 capabilities must default to execution_disabled.")
        self._capabilities[capability_id] = capability

    def list(self) -> list[dict[str, Any]]:
        return [capability.as_dict() for capability in self._capabilities.values()]

    def get(self, capability_id: str) -> dict[str, Any]:
        return self._capability(capability_id).as_dict()

    def match(
        self,
        mission: str,
        *,
        needs: tuple[str, ...] | list[str] = (),
        constraints: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        clean_mission = _clean_mission(mission)
        requested = {_clean(item) for item in needs if _clean(item)}
        limits = {_clean(item) for item in constraints if _clean(item)}
        selected: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []

        for capability in self._capabilities.values():
            rejection = _rejection_reason(capability, limits)
            if rejection:
                rejected.append(
                    {
                        "id": capability.id,
                        "title": capability.title,
                        "reason": rejection,
                    }
                )
                continue
            scored = _score_capability(capability, requested, limits, clean_mission)
            if scored["matched"] or not requested:
                selected.append(scored)

        selected.sort(key=lambda item: (int(item["order"]), -int(item["score"]), str(item["id"])))
        return {
            "mission": clean_mission,
            "needs": sorted(requested),
            "constraints": sorted(limits),
            "selected": selected,
            "rejected": rejected,
            "execution_enabled": False,
            "requires_human_approval": True,
        }

    def launch_plan(
        self,
        mission: str,
        *,
        needs: tuple[str, ...] | list[str] = (),
        constraints: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        match = self.match(mission, needs=needs, constraints=constraints)
        steps = [
            {
                "step": index,
                "capability_id": item["id"],
                "title": item["title"],
                "provider_id": item["provider_id"],
                "reason": item["reasons"][0],
                "mode": "proposal_only",
                "execution_enabled": False,
            }
            for index, item in enumerate(match["selected"], start=1)
        ]
        approval_required = sorted(
            {
                approval
                for item in match["selected"]
                for approval in item["approval_required_for"]
            }
            | set(APPROVAL_REQUIRED_FOR)
        )
        return {
            "mission": match["mission"],
            "needs": match["needs"],
            "constraints": match["constraints"],
            "steps": steps,
            "rejected": match["rejected"],
            "approval_required_for": approval_required,
            "mode": "proposal_only",
            "execution_enabled": False,
            "requires_human_approval": True,
        }

    def _capability(self, capability_id: str) -> Kaizen7Capability:
        clean = _clean(capability_id)
        try:
            return self._capabilities[clean]
        except KeyError as exc:
            raise KeyError(f"Unknown KAIZEN7 capability: {clean}") from exc


def default_capability_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    for capability in _DEFAULT_CAPABILITIES:
        registry.register(capability)
    return registry


def _clean(value: str) -> str:
    return str(value).strip().lower().replace("_", "-")


def _clean_mission(value: str) -> str:
    clean = " ".join(value.strip().split())
    if not clean:
        raise ValueError("mission cannot be blank.")
    return clean


def _rejection_reason(capability: Kaizen7Capability, constraints: set[str]) -> str:
    if "local-only" in constraints and capability.privacy != "local":
        return "rejected by local_only constraint"
    if "no-paid-api" in constraints and capability.cost == "paid":
        return "rejected by no_paid_api constraint"
    return ""


def _score_capability(
    capability: Kaizen7Capability,
    needs: set[str],
    constraints: set[str],
    mission: str,
) -> dict[str, Any]:
    score = 0
    matched = False
    reasons: list[str] = []
    capability_needs = {_clean(item) for item in capability.needs}
    for need in sorted(needs):
        if need in capability_needs:
            matched = True
            score += 20
            reasons.append(f"matches need: {need}")
    mission_lower = mission.lower()
    for need in capability_needs:
        if need.replace("-", " ") in mission_lower or need in mission_lower:
            matched = True
            score += 5
            reasons.append(f"mission language fits: {need}")
    if "local-only" in constraints and capability.privacy == "local":
        score += 10
        reasons.append("fits local_only constraint")
    if "no-paid-api" in constraints and capability.cost in {"local", "free", "configurable"}:
        score += 5
        reasons.append("fits no_paid_api constraint")
    if not reasons:
        reasons.append("available as proposal-only capability")
    return {
        **capability.as_dict(),
        "score": score,
        "order": _ORDER.get(capability.id, 99),
        "matched": matched,
        "reasons": reasons,
    }


_ORDER = {
    "daily-focus": 10,
    "governed-memory": 20,
    "business-research": 30,
    "content-pipeline": 40,
    "code-repair": 50,
    "mcp-connector-plan": 60,
    "quality-evaluation": 70,
    "knowledge-graph-memory": 80,
    "multi-device-command": 90,
    "context-compaction": 100,
    "workflow-console": 110,
    "developer-studio": 120,
    "designer-studio": 130,
    "skill-forge": 140,
    "mobile-approval": 150,
    "desktop-control-plan": 160,
    "agent-session-control": 170,
    "visual-workflow-plan": 180,
    "social-publishing-plan": 190,
}

_DEFAULT_CAPABILITIES: tuple[Kaizen7Capability, ...] = (
    Kaizen7Capability(
        id="daily-focus",
        title="Daily Focus",
        provider_id="hermes",
        summary="Turn a messy day into one mission, three priorities, and a review loop.",
        needs=("focus", "planning", "review"),
        permissions=("read_capsule", "write_receipt"),
        approval_required_for=("irreversible_changes",),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="business-research",
        title="Business Research",
        provider_id="api",
        summary="Compare markets, competitors, offers, and sources before a decision.",
        needs=("research", "market", "strategy"),
        permissions=("read_context", "write_receipt"),
        approval_required_for=("external_sends", "financial_operations"),
        privacy="external",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="governed-memory",
        title="Governed Memory",
        provider_id="cli",
        summary="Keep decisions, context, metrics and receipts scoped, inspectable and recoverable.",
        needs=("memory", "receipts", "context"),
        permissions=("read_receipts", "write_receipt", "read_capsule"),
        approval_required_for=("credentials", "irreversible_changes"),
        privacy="local",
        cost="local",
    ),
    Kaizen7Capability(
        id="content-pipeline",
        title="Content Pipeline",
        provider_id="hermes",
        summary="Plan content from trust to offer to lead path, with approval before publishing.",
        needs=("content", "sales", "publishing"),
        permissions=("read_capsule", "draft_content", "write_receipt"),
        approval_required_for=("publishing", "messages", "external_sends"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="mcp-connector-plan",
        title="MCP Connector Plan",
        provider_id="api",
        summary="Plan tool connectors through stable contracts instead of one-off integrations.",
        needs=("mcp", "connectors", "tools"),
        permissions=("read_context", "write_receipt"),
        approval_required_for=("credentials", "external_sends", "financial_operations"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="quality-evaluation",
        title="Quality Evaluation",
        provider_id="codex",
        summary="Score agent proposals against tests, risks, evidence and acceptance criteria.",
        needs=("evaluation", "quality", "tests"),
        permissions=("read_context", "read_repo", "write_receipt"),
        approval_required_for=("destructive_changes", "irreversible_changes"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="knowledge-graph-memory",
        title="Knowledge Graph Memory",
        provider_id="cli",
        summary="Map people, projects, decisions, metrics and receipts as linked business memory.",
        needs=("memory", "knowledge", "graph", "context"),
        permissions=("read_receipts", "read_capsule", "write_receipt"),
        approval_required_for=("credentials", "irreversible_changes"),
        privacy="local",
        cost="local",
    ),
    Kaizen7Capability(
        id="multi-device-command",
        title="Multi-device Command",
        provider_id="cli",
        summary="Prepare mobile and desktop command surfaces with approval queues and receipt review.",
        needs=("mobile", "remote", "approval", "command"),
        permissions=("read_receipts", "write_receipt"),
        approval_required_for=("messages", "credentials", "external_sends"),
        privacy="local",
        cost="local",
    ),
    Kaizen7Capability(
        id="context-compaction",
        title="Context Compaction",
        provider_id="cli",
        summary="Compress long work context into reversible briefs before routing to agents.",
        needs=("context", "compression", "memory", "handoff"),
        permissions=("read_context", "read_receipts", "write_receipt"),
        approval_required_for=("credentials", "irreversible_changes"),
        privacy="local",
        cost="local",
    ),
    Kaizen7Capability(
        id="workflow-console",
        title="Workflow Console",
        provider_id="hermes",
        summary="Represent recurring work as visible workflows with state, owner, risk and receipts.",
        needs=("workflow", "planning", "operations", "review"),
        permissions=("read_capsule", "read_receipts", "write_receipt"),
        approval_required_for=("external_sends", "financial_operations", "irreversible_changes"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="developer-studio",
        title="Developer Studio",
        provider_id="codex",
        summary="Plan code missions with repo context, tests, review gates and rollback notes.",
        needs=("code", "developer", "tests", "debugging"),
        permissions=("read_repo", "write_patch", "write_receipt"),
        approval_required_for=("destructive_changes", "irreversible_changes"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="designer-studio",
        title="Designer Studio",
        provider_id="api",
        summary="Plan product, content and visual assets from brand context before generation or publishing.",
        needs=("design", "content", "brand", "visual"),
        permissions=("read_capsule", "draft_content", "write_receipt"),
        approval_required_for=("publishing", "external_sends", "credentials"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="skill-forge",
        title="Skill Forge",
        provider_id="codex",
        summary="Design, version and test reusable skills for agents, APIs and business workflows.",
        needs=("skills", "agents", "tests", "workflow"),
        permissions=("read_context", "write_patch", "write_receipt"),
        approval_required_for=("credentials", "destructive_changes", "irreversible_changes"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="code-repair",
        title="Code Repair",
        provider_id="codex",
        summary="Prepare repository fixes, tests, reviews, and implementation plans.",
        needs=("code", "tests", "debugging"),
        permissions=("read_repo", "write_patch", "write_receipt"),
        approval_required_for=("destructive_changes", "irreversible_changes"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="mobile-approval",
        title="Mobile Approval",
        provider_id="cli",
        summary="Queue approvals and receipts for a mobile-first control surface.",
        needs=("approval", "mobile", "receipts"),
        permissions=("read_receipts", "write_receipt"),
        approval_required_for=APPROVAL_REQUIRED_FOR,
        privacy="local",
        cost="local",
    ),
    Kaizen7Capability(
        id="desktop-control-plan",
        title="Desktop Control Plan",
        provider_id="cli",
        summary="Prepare local desktop diagnostics and control plans behind allowlists.",
        needs=("diagnostics", "desktop", "local"),
        permissions=("read_local_state", "write_receipt"),
        approval_required_for=("credentials", "destructive_changes", "irreversible_changes"),
        privacy="local",
        cost="local",
    ),
    Kaizen7Capability(
        id="agent-session-control",
        title="Agent Session Control",
        provider_id="hermes",
        summary="Represent every agent run as a session with profile, owner, permissions and receipt trail.",
        needs=("sessions", "agents", "audit"),
        permissions=("read_receipts", "write_receipt", "read_capsule"),
        approval_required_for=("messages", "external_sends", "irreversible_changes"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="visual-workflow-plan",
        title="Visual Workflow Plan",
        provider_id="api",
        summary="Generate a user-readable workflow graph before automation exists.",
        needs=("workflow", "planning", "visual"),
        permissions=("read_context", "write_receipt"),
        approval_required_for=("external_sends", "financial_operations"),
        privacy="mixed",
        cost="configurable",
    ),
    Kaizen7Capability(
        id="social-publishing-plan",
        title="Social Publishing Plan",
        provider_id="api",
        summary="Prepare social/content publishing calendars with approval before any external post.",
        needs=("publishing", "social", "content"),
        permissions=("read_capsule", "draft_content", "write_receipt"),
        approval_required_for=("publishing", "messages", "external_sends", "credentials"),
        privacy="external",
        cost="configurable",
    ),
)
