"""Provider registry for any KAIZEN7-compatible agent or API.

The registry is intentionally execution-neutral: it describes providers and
records proposal receipts, but it never calls a third-party API or launches an
agent. Concrete adapters can be added behind the same contract once Luciano
approves credentials, cost limits, and execution boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from jarvis.kaizen7.bridge import ControlBridgeStore, _utc_now


@dataclass(frozen=True)
class AgentProvider:
    id: str
    label: str
    kind: str
    description: str
    auth_methods: tuple[str, ...]
    capabilities: tuple[str, ...]
    privacy: str = "external"
    cost: str = "unknown"
    latency: str = "unknown"
    strengths: tuple[str, ...] = ()
    mode: str = "proposal_only"
    execution_enabled: bool = False
    cost_control: str = "requires explicit configuration before paid use"
    approval_required: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "description": self.description,
            "auth_methods": list(self.auth_methods),
            "capabilities": list(self.capabilities),
            "privacy": self.privacy,
            "cost": self.cost,
            "latency": self.latency,
            "strengths": list(self.strengths),
            "mode": self.mode,
            "execution_enabled": self.execution_enabled,
            "cost_control": self.cost_control,
            "approval_required": self.approval_required,
        }


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AgentProvider] = {}

    def register(self, provider: AgentProvider) -> None:
        provider_id = _clean_id(provider.id)
        if provider_id in self._providers:
            raise ValueError(f"Provider {provider_id!r} is already registered.")
        if provider.execution_enabled:
            raise ValueError("KAIZEN7 providers must default to execution_disabled.")
        self._providers[provider_id] = provider

    def list(self) -> list[dict[str, Any]]:
        return [provider.as_dict() for provider in self._providers.values()]

    def get(self, provider_id: str) -> dict[str, Any]:
        return self._provider(provider_id).as_dict()

    def propose(
        self,
        provider_id: str,
        message: str,
        *,
        bridge: ControlBridgeStore,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        provider = self._provider(provider_id)
        clean = " ".join(message.strip().split())
        if not clean:
            raise ValueError("Proposal message cannot be blank.")
        now = _utc_now()
        proposal = {
            "id": f"provider-{uuid4().hex}",
            "provider_id": provider.id,
            "provider_label": provider.label,
            "kind": provider.kind,
            "message": clean,
            "context": dict(context or {}),
            "status": "proposed",
            "mode": provider.mode,
            "execution_enabled": False,
            "requires_human_approval": True,
            "created_at": now,
            "next_step": (
                "Review provider, credentials, cost limits, and approval scope "
                "before any execution adapter is enabled."
            ),
        }
        bridge.record_receipt(
            {
                "id": proposal["id"],
                "kind": "provider_proposal",
                "provider_id": provider.id,
                "provider_label": provider.label,
                "message": clean,
                "context": proposal["context"],
                "status": "recorded",
                "execution_enabled": False,
                "created_at": now,
            }
        )
        return proposal

    def recommend(
        self,
        mission: str,
        *,
        needs: tuple[str, ...] | list[str] = (),
        constraints: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        clean_mission = " ".join(mission.strip().split())
        if not clean_mission:
            raise ValueError("mission cannot be blank.")
        requested = {_clean_token(item) for item in needs if _clean_token(item)}
        limits = {_clean_token(item) for item in constraints if _clean_token(item)}
        ranked: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []

        for provider in self._providers.values():
            rejection = _rejection_reason(provider, limits)
            if rejection:
                rejected.append({"id": provider.id, "label": provider.label, "reason": rejection})
                continue
            candidate = _score_provider(provider, requested, limits, clean_mission)
            ranked.append(candidate)

        ranked.sort(key=lambda item: (-int(item["score"]), str(item["id"])))
        selected = ranked[0] if ranked else None
        return {
            "mission": clean_mission,
            "needs": sorted(requested),
            "constraints": sorted(limits),
            "selected": selected,
            "ranked": ranked,
            "rejected": rejected,
            "mode": "proposal_only",
            "execution_enabled": False,
            "requires_human_approval": True,
        }

    def _provider(self, provider_id: str) -> AgentProvider:
        clean = _clean_id(provider_id)
        try:
            return self._providers[clean]
        except KeyError as exc:
            raise KeyError(f"Unknown KAIZEN7 provider: {clean}") from exc


def default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    for provider in _DEFAULT_PROVIDERS:
        registry.register(provider)
    return registry


def _clean_id(provider_id: str) -> str:
    clean = provider_id.strip().lower()
    if not clean:
        raise ValueError("Provider id cannot be blank.")
    return clean


def _clean_token(value: str) -> str:
    return str(value).strip().lower().replace("-", "_")


def _rejection_reason(provider: AgentProvider, constraints: set[str]) -> str:
    if "local_only" in constraints and provider.privacy != "local":
        return "rejected by local_only constraint"
    if "no_paid_api" in constraints and provider.cost == "paid":
        return "rejected by no_paid_api constraint"
    return ""


def _score_provider(
    provider: AgentProvider,
    needs: set[str],
    constraints: set[str],
    mission: str,
) -> dict[str, Any]:
    score = 0
    reasons: list[str] = []
    capabilities = {_clean_token(item) for item in provider.capabilities}
    strengths = {_clean_token(item) for item in provider.strengths}

    for need in sorted(needs):
        if need in capabilities or need in strengths:
            score += 20
            reasons.append(f"matches required capability: {need}")

    mission_lower = mission.lower()
    keyword_scores = {
        "code": ("repo", "code", "test", "bug", "commit", "python", "typescript"),
        "research": ("research", "market", "compare", "source", "competitor"),
        "chat": ("chat", "conversation", "assistant", "voice"),
        "local_plan": ("local", "desktop", "offline", "private"),
    }
    for capability, keywords in keyword_scores.items():
        if capability in capabilities and any(word in mission_lower for word in keywords):
            score += 8
            reasons.append(f"mission language fits: {capability}")

    if "no_paid_api" in constraints and provider.cost in {"free", "local"}:
        score += 5
        reasons.append("fits no_paid_api constraint")
    if "local_only" in constraints and provider.privacy == "local":
        score += 10
        reasons.append("fits local_only constraint")
    if provider.execution_enabled is False:
        score += 3
        reasons.append("safe by default: execution disabled")

    if not reasons:
        reasons.append("available as a proposal-only fallback")

    return {
        **provider.as_dict(),
        "score": score,
        "reasons": reasons,
    }


_DEFAULT_PROVIDERS: tuple[AgentProvider, ...] = (
    AgentProvider(
        id="hermes",
        label="Hermes Agent",
        kind="agent_runtime",
        description="Hermes profiles, Bot Mode, gateway platforms, skills, memory, and ACP flows.",
        auth_methods=("hermes_config", "provider_env_vars", "gateway_env_vars"),
        capabilities=("chat", "bot_mode", "skills", "memory", "gateway", "cron"),
        privacy="mixed",
        cost="configurable",
        latency="medium",
        strengths=("agent_runtime", "long_running", "messaging"),
    ),
    AgentProvider(
        id="codex",
        label="Codex CLI",
        kind="coding_agent",
        description="Delegates implementation, repository repair, tests, and code review plans.",
        auth_methods=("codex_login", "openai_api_key_env"),
        capabilities=("code", "tests", "repo_review", "implementation_plan"),
        privacy="mixed",
        cost="configurable",
        latency="medium",
        strengths=("repositories", "debugging", "patches"),
    ),
    AgentProvider(
        id="api",
        label="Generic API Provider",
        kind="api",
        description="Template connector for any HTTP model API or agent service.",
        auth_methods=("api_key_env", "oauth", "bearer_token_env"),
        capabilities=("chat", "research", "analysis", "tool_call_plan"),
        privacy="external",
        cost="paid",
        latency="fast",
        strengths=("model_router", "external_knowledge", "structured_output"),
    ),
    AgentProvider(
        id="cli",
        label="Generic CLI Agent",
        kind="cli",
        description="Template connector for local command-line agents with explicit allowlists.",
        auth_methods=("local_binary", "profile_config", "env_vars"),
        capabilities=("local_plan", "diagnostics", "offline_tools"),
        privacy="local",
        cost="local",
        latency="fast",
        strengths=("private_files", "desktop", "debugging"),
    ),
)
