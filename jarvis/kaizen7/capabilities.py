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

        selected.sort(key=lambda item: (-int(item["score"]), int(item["order"]), str(item["id"])))
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
    "business-research": 20,
    "content-pipeline": 30,
    "code-repair": 40,
    "mobile-approval": 50,
    "desktop-control-plan": 60,
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
)
