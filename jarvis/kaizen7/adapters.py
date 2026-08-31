"""Agent-agnostic adapter registry for KAIZEN7 Jarvis.

Adapters describe how any model, cloud agent, CLI, MCP server or webhook could
be connected. They do not execute anything by default.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from jarvis.kaizen7.bridge import ControlBridgeStore, _utc_now


@dataclass(frozen=True)
class AgentAdapter:
    id: str
    label: str
    kind: str
    description: str
    capabilities: tuple[str, ...]
    auth: str
    required_env: tuple[str, ...] = ()
    endpoint_template: str = ""
    command_template: tuple[str, ...] = ()
    health_check: str = "manual"
    timeout_seconds: int = 30
    privacy: str = "external"
    cost: str = "configurable"
    permissions: tuple[str, ...] = ("read_context", "write_receipt")
    execution_mode: str = "proposal_only"
    execution_enabled: bool = False
    requires_human_approval: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "auth": self.auth,
            "required_env": list(self.required_env),
            "endpoint_template": self.endpoint_template,
            "command_template": list(self.command_template),
            "health_check": self.health_check,
            "timeout_seconds": self.timeout_seconds,
            "privacy": self.privacy,
            "cost": self.cost,
            "permissions": list(self.permissions),
            "execution_mode": self.execution_mode,
            "execution_enabled": self.execution_enabled,
            "requires_human_approval": self.requires_human_approval,
        }


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, AgentAdapter] = {}

    def register(self, adapter: AgentAdapter) -> None:
        adapter_id = _clean_id(adapter.id)
        if adapter_id in self._adapters:
            raise ValueError(f"Adapter {adapter_id!r} is already registered.")
        if adapter.execution_enabled:
            raise ValueError("KAIZEN7 adapters must default to execution_disabled.")
        self._adapters[adapter_id] = adapter

    def list(self) -> list[dict[str, Any]]:
        return [adapter.as_dict() for adapter in self._adapters.values()]

    def get(self, adapter_id: str) -> dict[str, Any]:
        return self._adapter(adapter_id).as_dict()

    def manifest(self) -> dict[str, Any]:
        return {
            "schema_version": "kaizen7.adapter.v1",
            "adapters": self.list(),
            "execution_enabled": False,
            "requires_human_approval": True,
            "secret_policy": "env-var names only; never store secret values in Git",
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
        for adapter in self._adapters.values():
            rejection = _rejection_reason(adapter, limits)
            if rejection:
                rejected.append({"id": adapter.id, "label": adapter.label, "reason": rejection})
                continue
            ranked.append(_score_adapter(adapter, requested, limits, clean_mission))
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

    def propose(
        self,
        adapter_id: str,
        message: str,
        *,
        bridge: ControlBridgeStore,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        adapter = self._adapter(adapter_id)
        clean = " ".join(message.strip().split())
        if not clean:
            raise ValueError("Proposal message cannot be blank.")
        now = _utc_now()
        proposal = {
            "id": f"adapter-{uuid4().hex}",
            "adapter_id": adapter.id,
            "adapter_label": adapter.label,
            "kind": adapter.kind,
            "message": clean,
            "context": dict(context or {}),
            "status": "proposed",
            "execution_mode": adapter.execution_mode,
            "execution_enabled": False,
            "requires_human_approval": True,
            "created_at": now,
        }
        bridge.record_receipt(
            {
                "id": proposal["id"],
                "kind": "adapter_proposal",
                "adapter_id": adapter.id,
                "adapter_label": adapter.label,
                "message": clean,
                "context": proposal["context"],
                "status": "recorded",
                "execution_enabled": False,
                "created_at": now,
            }
        )
        return proposal

    def _adapter(self, adapter_id: str) -> AgentAdapter:
        clean = _clean_id(adapter_id)
        try:
            return self._adapters[clean]
        except KeyError as exc:
            raise KeyError(f"Unknown KAIZEN7 adapter: {clean}") from exc


def default_adapter_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    for adapter in _DEFAULT_ADAPTERS:
        registry.register(adapter)
    return registry


def _clean_id(value: str) -> str:
    clean = str(value).strip().lower()
    if not clean:
        raise ValueError("Adapter id cannot be blank.")
    return clean


def _clean_token(value: str) -> str:
    return str(value).strip().lower().replace("-", "_")


def _rejection_reason(adapter: AgentAdapter, constraints: set[str]) -> str:
    if "local_only" in constraints and adapter.privacy != "local":
        return "rejected by local_only constraint"
    if "no_paid_api" in constraints and adapter.cost == "paid":
        return "rejected by no_paid_api constraint"
    return ""


def _score_adapter(
    adapter: AgentAdapter,
    needs: set[str],
    constraints: set[str],
    mission: str,
) -> dict[str, Any]:
    score = 0
    reasons: list[str] = []
    capabilities = {_clean_token(item) for item in adapter.capabilities}
    for need in sorted(needs):
        if need in capabilities:
            score += 20
            reasons.append(f"matches need: {need}")
    mission_lower = mission.lower()
    if adapter.kind in mission_lower:
        score += 8
        reasons.append(f"mission mentions adapter kind: {adapter.kind}")
    if "local_only" in constraints and adapter.privacy == "local":
        score += 10
        reasons.append("fits local_only constraint")
    if "no_paid_api" in constraints and adapter.cost in {"local", "free", "configurable"}:
        score += 5
        reasons.append("fits no_paid_api constraint")
    if adapter.execution_enabled is False:
        score += 3
        reasons.append("safe by default: execution disabled")
    if not reasons:
        reasons.append("available as proposal-only adapter")
    return {**adapter.as_dict(), "score": score, "reasons": reasons}


_DEFAULT_ADAPTERS: tuple[AgentAdapter, ...] = (
    AgentAdapter(
        id="openai-compatible",
        label="OpenAI-compatible API",
        kind="openai_compatible",
        description="Any API that implements the OpenAI chat/completions style contract.",
        capabilities=("chat", "research", "analysis", "structured_output"),
        auth="api_key_env",
        required_env=("OPENAI_API_KEY", "OPENAI_BASE_URL"),
        endpoint_template="${OPENAI_BASE_URL}/chat/completions",
        health_check="GET ${OPENAI_BASE_URL}/models",
        privacy="external",
        cost="paid",
    ),
    AgentAdapter(
        id="generic-http-api",
        label="Generic HTTP API Agent",
        kind="api",
        description="Any cloud or self-hosted agent exposed through HTTP.",
        capabilities=("chat", "research", "workflow", "tool_call_plan"),
        auth="bearer_token_env",
        required_env=("AGENT_API_URL", "AGENT_API_TOKEN"),
        endpoint_template="${AGENT_API_URL}",
        health_check="GET ${AGENT_API_URL}/health",
        privacy="external",
        cost="configurable",
    ),
    AgentAdapter(
        id="generic-cli-agent",
        label="Generic CLI Agent",
        kind="cli",
        description="Any local command-line agent, including cloud-code style CLIs.",
        capabilities=("code", "diagnostics", "local", "workflow", "skills"),
        auth="local_profile_or_env",
        required_env=("AGENT_CLI",),
        command_template=("${AGENT_CLI}", "--help"),
        health_check="${AGENT_CLI} --version",
        privacy="local",
        cost="local",
        permissions=("read_local_state", "write_receipt"),
    ),
    AgentAdapter(
        id="mcp-server",
        label="MCP Server",
        kind="mcp",
        description="Any Model Context Protocol server exposed locally or remotely.",
        capabilities=("tools", "mcp", "connectors", "workflow"),
        auth="mcp_config_or_env",
        required_env=("MCP_SERVER_URL",),
        endpoint_template="${MCP_SERVER_URL}",
        health_check="mcp capabilities/list",
        privacy="mixed",
        cost="configurable",
    ),
    AgentAdapter(
        id="webhook-agent",
        label="Webhook Agent",
        kind="webhook",
        description="Any automation or agent triggered through a webhook.",
        capabilities=("workflow", "automation", "external_sends"),
        auth="webhook_secret_env",
        required_env=("WEBHOOK_URL", "WEBHOOK_SECRET"),
        endpoint_template="${WEBHOOK_URL}",
        health_check="manual webhook verification",
        privacy="external",
        cost="configurable",
    ),
    AgentAdapter(
        id="cloud-agent",
        label="Cloud Agent Gateway",
        kind="cloud_agent",
        description="Any managed cloud agent, future OpenCloud service, or hosted coding assistant.",
        capabilities=("cloud", "code", "research", "workflow", "remote"),
        auth="oauth_or_api_key_env",
        required_env=("CLOUD_AGENT_URL", "CLOUD_AGENT_TOKEN"),
        endpoint_template="${CLOUD_AGENT_URL}",
        health_check="GET ${CLOUD_AGENT_URL}/health",
        privacy="external",
        cost="paid",
    ),
)
