"""Universal agent gateway for KAIZEN7 Jarvis.

The gateway describes agents that KAIZEN7 can route work to. It is deliberately
dry-run/proposal-only: it can rank, diagnose and record handoffs, but it never
calls a model, CLI, API, MCP server or cloud agent.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from jarvis.kaizen7.bridge import ControlBridgeStore, _utc_now


@dataclass(frozen=True)
class AgentPassport:
    id: str
    label: str
    kind: str
    adapter_id: str
    description: str
    capabilities: tuple[str, ...]
    required_env: tuple[str, ...] = ()
    privacy: str = "external"
    cost: str = "configurable"
    risk_level: str = "medium"
    runtime: str = "external"
    auth: str = "env_or_local_profile"
    approval_required_for: tuple[str, ...] = (
        "payments",
        "publishing",
        "outbound_messages",
        "credentials",
        "financial_operations",
        "irreversible_changes",
        "deployments",
    )
    execution_mode: str = "proposal_only"
    execution_enabled: bool = False
    requires_human_approval: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "adapter_id": self.adapter_id,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "required_env": list(self.required_env),
            "privacy": self.privacy,
            "cost": self.cost,
            "risk_level": self.risk_level,
            "runtime": self.runtime,
            "auth": self.auth,
            "approval_required_for": list(self.approval_required_for),
            "execution_mode": self.execution_mode,
            "execution_enabled": self.execution_enabled,
            "requires_human_approval": self.requires_human_approval,
        }


class AgentGateway:
    def __init__(self) -> None:
        self._agents: dict[str, AgentPassport] = {}

    def register(self, passport: AgentPassport) -> None:
        agent_id = _clean_id(passport.id)
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id!r} is already registered.")
        if passport.execution_enabled:
            raise ValueError("KAIZEN7 agent passports must default to execution_disabled.")
        self._agents[agent_id] = passport

    def list(self) -> list[dict[str, Any]]:
        return [agent.as_dict() for agent in self._agents.values()]

    def get(self, agent_id: str) -> dict[str, Any]:
        return self._agent(agent_id).as_dict()

    def manifest(self) -> dict[str, Any]:
        return {
            "schema_version": "kaizen7.agent_gateway.v1",
            "runtime_policy": "agent/model/cloud agnostic",
            "agents": self.list(),
            "execution_enabled": False,
            "requires_human_approval": True,
            "secret_policy": "env-var names and local profile names only; never store secret values in Git",
        }

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
        for agent in self._agents.values():
            rejection = _rejection_reason(agent, limits)
            if rejection:
                rejected.append({"id": agent.id, "label": agent.label, "reason": rejection})
                continue
            ranked.append(_score_agent(agent, requested, limits, clean_mission))
        ranked.sort(key=lambda item: (-int(item["score"]), str(item["id"])))
        return {
            "mission": clean_mission,
            "needs": sorted(requested),
            "constraints": sorted(limits),
            "selected": ranked[0] if ranked else None,
            "ranked": ranked,
            "rejected": rejected,
            "execution_enabled": False,
            "requires_human_approval": True,
        }

    def bench(
        self,
        agent_id: str,
        *,
        env: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        agent = self._agent(agent_id)
        source = os.environ if env is None else env
        missing = [name for name in agent.required_env if not str(source.get(name, "")).strip()]
        checks = [
            {
                "name": name,
                "status": "missing" if name in missing else "ok",
                "message": "required environment value is absent"
                if name in missing
                else "required environment value is present",
            }
            for name in agent.required_env
        ]
        if not checks:
            checks.append(
                {
                    "name": "local_profile",
                    "status": "ok",
                    "message": "no environment variable is required for dry-run discovery",
                }
            )
        return {
            "agent_id": agent.id,
            "agent_label": agent.label,
            "adapter_id": agent.adapter_id,
            "status": "not_configured" if missing else "ready_for_proposal",
            "dry_run": True,
            "missing_env": missing,
            "checks": checks,
            "execution_enabled": False,
            "requires_human_approval": True,
        }

    def propose(
        self,
        agent_id: str,
        message: str,
        *,
        bridge: ControlBridgeStore,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        agent = self._agent(agent_id)
        clean = " ".join(message.strip().split())
        if not clean:
            raise ValueError("Proposal message cannot be blank.")
        now = _utc_now()
        proposal = {
            "id": f"agent-{uuid4().hex}",
            "agent_id": agent.id,
            "agent_label": agent.label,
            "adapter_id": agent.adapter_id,
            "kind": agent.kind,
            "message": clean,
            "context": dict(context or {}),
            "status": "proposed",
            "execution_mode": agent.execution_mode,
            "execution_enabled": False,
            "requires_human_approval": True,
            "created_at": now,
        }
        bridge.record_receipt(
            {
                "id": proposal["id"],
                "kind": "agent_proposal",
                "agent_id": agent.id,
                "agent_label": agent.label,
                "adapter_id": agent.adapter_id,
                "message": clean,
                "context": proposal["context"],
                "status": "recorded",
                "execution_enabled": False,
                "created_at": now,
            }
        )
        return proposal

    def _agent(self, agent_id: str) -> AgentPassport:
        clean = _clean_id(agent_id)
        try:
            return self._agents[clean]
        except KeyError as exc:
            raise KeyError(f"Unknown KAIZEN7 agent: {clean}") from exc


def default_agent_gateway() -> AgentGateway:
    gateway = AgentGateway()
    for passport in _DEFAULT_AGENT_PASSPORTS:
        gateway.register(passport)
    return gateway


def _clean_id(value: str) -> str:
    clean = str(value).strip().lower()
    if not clean:
        raise ValueError("Agent id cannot be blank.")
    return clean


def _clean_token(value: str) -> str:
    return str(value).strip().lower().replace("-", "_")


def _rejection_reason(agent: AgentPassport, constraints: set[str]) -> str:
    if "local_only" in constraints and agent.privacy != "local":
        return "rejected by local_only constraint"
    if "no_paid_api" in constraints and agent.cost == "paid":
        return "rejected by no_paid_api constraint"
    return ""


def _score_agent(
    agent: AgentPassport,
    needs: set[str],
    constraints: set[str],
    mission: str,
) -> dict[str, Any]:
    score = 0
    reasons: list[str] = []
    capabilities = {_clean_token(item) for item in agent.capabilities}
    for need in sorted(needs):
        if need in capabilities:
            score += 20
            reasons.append(f"matches need: {need}")
    mission_lower = mission.lower()
    if agent.kind in mission_lower or agent.id.replace("-", " ") in mission_lower:
        score += 8
        reasons.append("mission mentions this agent surface")
    if "local_only" in constraints and agent.privacy == "local":
        score += 10
        reasons.append("fits local_only constraint")
    if "no_paid_api" in constraints and agent.cost in {"local", "free", "configurable"}:
        score += 5
        reasons.append("fits no_paid_api constraint")
    if agent.risk_level == "low":
        score += 4
        reasons.append("low risk proposal surface")
    if agent.execution_enabled is False:
        score += 3
        reasons.append("safe by default: execution disabled")
    if not reasons:
        reasons.append("available as proposal-only agent")
    return {**agent.as_dict(), "score": score, "reasons": reasons}


_DEFAULT_AGENT_PASSPORTS: tuple[AgentPassport, ...] = (
    AgentPassport(
        id="kaizen7-local-cli",
        label="KAIZEN7 Local CLI",
        kind="cli",
        adapter_id="generic-cli-agent",
        description="Local KAIZEN7/Jarvis command surface for diagnostics, routing and receipts.",
        capabilities=("focus", "routing", "diagnostics", "local", "receipts"),
        privacy="local",
        cost="local",
        risk_level="low",
        runtime="jarvis",
        auth="local_install",
    ),
    AgentPassport(
        id="hermes-runtime",
        label="Hermes Agent Runtime",
        kind="runtime",
        adapter_id="generic-cli-agent",
        description="Hermes profile, Bot Mode, skill and gateway runtime as an optional execution surface.",
        capabilities=("chat", "skills", "memory", "workflow", "agents"),
        required_env=("KAIZEN7_HERMES_CLI",),
        privacy="local",
        cost="local",
        risk_level="medium",
        runtime="hermes",
        auth="local_profile",
    ),
    AgentPassport(
        id="codex-cli",
        label="Codex CLI",
        kind="cli",
        adapter_id="generic-cli-agent",
        description="Local coding agent for repository inspection, edits and tests after approval.",
        capabilities=("code", "tests", "diagnostics", "local", "review"),
        required_env=("KAIZEN7_CODEX_CLI",),
        privacy="local",
        cost="local",
        risk_level="medium",
        runtime="codex",
        auth="local_profile_or_api_key",
    ),
    AgentPassport(
        id="openhands-worker",
        label="OpenHands Worker",
        kind="remote_worker",
        adapter_id="cloud-agent",
        description="Self-hosted or remote coding worker for sandboxed development handoffs.",
        capabilities=("code", "tests", "sandbox", "remote", "workflow"),
        required_env=("OPENHANDS_URL",),
        privacy="mixed",
        cost="configurable",
        risk_level="medium",
        runtime="openhands",
        auth="server_or_local_profile",
    ),
    AgentPassport(
        id="mcp-tool-server",
        label="MCP Tool Server",
        kind="mcp",
        adapter_id="mcp-server",
        description="Model Context Protocol tool/resource/prompt server exposed to Jarvis.",
        capabilities=("tools", "resources", "mcp", "connectors", "workflow"),
        required_env=("MCP_SERVER_URL",),
        privacy="mixed",
        cost="configurable",
        risk_level="medium",
        runtime="mcp",
        auth="mcp_config_or_env",
    ),
    AgentPassport(
        id="openai-compatible-model",
        label="OpenAI-Compatible Model",
        kind="model_api",
        adapter_id="openai-compatible",
        description="Any OpenAI-compatible model gateway, including local servers and approved hosted providers.",
        capabilities=("chat", "research", "analysis", "structured_output"),
        required_env=("OPENAI_API_KEY", "OPENAI_BASE_URL"),
        privacy="external",
        cost="paid",
        risk_level="medium",
        runtime="openai_compatible",
        auth="api_key_env",
    ),
    AgentPassport(
        id="generic-cloud-agent",
        label="Generic Cloud Agent",
        kind="cloud_agent",
        adapter_id="cloud-agent",
        description="Any managed cloud agent, future OpenCloud runtime or hosted specialist worker.",
        capabilities=("cloud", "code", "research", "workflow", "remote"),
        required_env=("CLOUD_AGENT_URL", "CLOUD_AGENT_TOKEN"),
        privacy="external",
        cost="paid",
        risk_level="high",
        runtime="cloud",
        auth="oauth_or_api_key_env",
    ),
)
