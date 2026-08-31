"""Market pattern blueprint for KAIZEN7 Jarvis.

This module is a legal pattern fork, not a code fork. It records which current
open-source agent patterns are worth absorbing into KAIZEN7's product surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MarketPattern:
    id: str
    source: str
    source_url: str
    pattern: str
    source_license: str
    license_posture: str
    kaizen7_layer: str
    capability_id: str
    adoption: str
    reason: str
    copy_code: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_pattern": self.id,
            "source": self.source,
            "source_url": self.source_url,
            "pattern": self.pattern,
            "source_license": self.source_license,
            "license_posture": self.license_posture,
            "kaizen7_layer": self.kaizen7_layer,
            "capability_id": self.capability_id,
            "adoption": self.adoption,
            "reason": self.reason,
            "copy_code": self.copy_code,
        }


class MarketBlueprint:
    def __init__(self, patterns: tuple[MarketPattern, ...]) -> None:
        self._patterns = patterns

    def list(self) -> list[dict[str, Any]]:
        return [pattern.as_dict() for pattern in self._patterns]

    def adopted(self) -> list[dict[str, Any]]:
        return [
            pattern.as_dict()
            for pattern in self._patterns
            if pattern.adoption in {"adopt_now", "adapt_pattern"}
        ]

    def rejected(self) -> list[dict[str, Any]]:
        return [
            pattern.as_dict()
            for pattern in self._patterns
            if pattern.adoption in {"test_later", "reference_only", "reject"}
        ]


def default_market_blueprint() -> MarketBlueprint:
    return MarketBlueprint(_PATTERNS)


def market_upgrade_plan() -> dict[str, Any]:
    blueprint = default_market_blueprint()
    adopted = blueprint.adopted()
    recommended_now = [
        item
        for item in adopted
        if item["capability_id"]
        in {
            "daily-focus",
            "governed-memory",
            "knowledge-graph-memory",
            "multi-device-command",
            "mcp-connector-plan",
            "quality-evaluation",
            "context-compaction",
            "workflow-console",
            "developer-studio",
            "designer-studio",
            "skill-forge",
        }
    ]
    recommended_now.sort(key=lambda item: _CAPABILITY_ORDER.get(item["capability_id"], 99))
    recommended_now = _dedupe_by_capability(recommended_now)
    backlog = [
        item
        for item in blueprint.list()
        if item["capability_id"] not in {entry["capability_id"] for entry in recommended_now}
    ]
    return {
        "strategy": "absorb proven open-source patterns without copying large frameworks",
        "recommended_now": recommended_now,
        "backlog": backlog,
        "mode": "proposal_only",
        "execution_enabled": False,
        "requires_human_approval": True,
    }


_CAPABILITY_ORDER = {
    "daily-focus": 10,
    "governed-memory": 20,
    "knowledge-graph-memory": 30,
    "multi-device-command": 40,
    "mcp-connector-plan": 50,
    "quality-evaluation": 60,
    "context-compaction": 70,
    "workflow-console": 80,
    "developer-studio": 90,
    "designer-studio": 100,
    "skill-forge": 110,
}


def _dedupe_by_capability(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        capability_id = str(item["capability_id"])
        if capability_id in seen:
            continue
        seen.add(capability_id)
        deduped.append(item)
    return deduped

_PATTERNS: tuple[MarketPattern, ...] = (
    MarketPattern(
        id="operator-agent",
        source="PersonalJarvis + OpenHands",
        source_url="https://github.com/PersonalJarvis/PersonalJarvis",
        pattern="assistant as operator: local app, voice, tools, coding workers, review loop",
        source_license="MIT / Apache-style patterns verified per source before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Operator",
        capability_id="daily-focus",
        adoption="adopt_now",
        reason="core product loop: focus, act, review, receipt",
    ),
    MarketPattern(
        id="plugin-marketplace",
        source="DeepSeek Harness + Flowise",
        source_url="https://github.com/deepseek-ai/deepseek-harness",
        pattern="capabilities are plugins with provider, permissions, and lifecycle",
        source_license="reference pattern; do not copy desktop/community wrappers",
        license_posture="reference-only",
        kaizen7_layer="K7 Operator",
        capability_id="visual-workflow-plan",
        adoption="test_later",
        reason="too heavy for default install",
    ),
    MarketPattern(
        id="visual-workflows",
        source="Flowise / n8n",
        source_url="https://github.com/FlowiseAI/Flowise",
        pattern="visual workflow planning for non-technical operation",
        source_license="Apache/MIT-style patterns depending on source",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Operator",
        capability_id="visual-workflow-plan",
        adoption="adapt_pattern",
        reason="useful as planning view; avoid importing full workflow engine",
    ),
    MarketPattern(
        id="local-knowledge",
        source="AnythingLLM / Open WebUI",
        source_url="https://github.com/Mintplex-Labs/anything-llm",
        pattern="local-first knowledge, workspace memory, model/provider choice",
        source_license="reference pattern; verify exact license before reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Memory",
        capability_id="governed-memory",
        adoption="adopt_now",
        reason="memory must be useful, scoped, and inspectable",
    ),
    MarketPattern(
        id="mcp-connectors",
        source="MCP ecosystem / Composio-style toolkits",
        source_url="https://modelcontextprotocol.io/",
        pattern="standard tool connector contracts instead of one-off integrations",
        source_license="protocol/pattern",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Operator",
        capability_id="mcp-connector-plan",
        adoption="adopt_now",
        reason="best current way to grow agents without hardcoding every tool",
    ),
    MarketPattern(
        id="quality-evals",
        source="OpenHands / OpenJudge-style eval loops",
        source_url="https://github.com/All-Hands-AI/OpenHands",
        pattern="agent output needs checks, scores, and acceptance gates",
        source_license="reference pattern; do not copy evaluators without review",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Judge",
        capability_id="quality-evaluation",
        adoption="adopt_now",
        reason="market-ready agents need quality gates before execution",
    ),
    MarketPattern(
        id="external-publishing",
        source="Postiz / n8n / social schedulers",
        source_url="https://github.com/gitroomhq/postiz-app",
        pattern="publish and schedule content from one cockpit",
        source_license="reference pattern; execution requires approval",
        license_posture="reference-only",
        kaizen7_layer="Content Factory",
        capability_id="social-publishing-plan",
        adoption="test_later",
        reason="requires credentials or external publishing approval",
    ),
    MarketPattern(
        id="rowbot-agent-os",
        source="Row-Bot",
        source_url="https://github.com/siddsachar/row-bot",
        pattern="agent OS with durable memory, knowledge graph, workflows, profiles, MCP, plugins and multi-device access",
        source_license="reference pattern; verify exact license before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Operator",
        capability_id="knowledge-graph-memory",
        adoption="adopt_now",
        reason="best benchmark for an evolvable personal/business agent OS",
    ),
    MarketPattern(
        id="openyak-workspace",
        source="OpenYak",
        source_url="https://github.com/openyak/openyak",
        pattern="workspace-first assistant for files, long context and secure remote access",
        source_license="reference pattern; verify exact license before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Context",
        capability_id="context-compaction",
        adoption="adopt_now",
        reason="long-running work needs compact handoffs and file-grounded context",
    ),
    MarketPattern(
        id="pioneer-gateway",
        source="Pioneer",
        source_url="https://github.com/pioneerdotai/pioneer",
        pattern="gateway-first desktop agent with remote/local routing and MCP-style control",
        source_license="reference pattern; verify exact license before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Operator",
        capability_id="multi-device-command",
        adoption="adopt_now",
        reason="mobile and desktop command need one governed gateway contract",
    ),
    MarketPattern(
        id="dax-policy-core",
        source="Dax Assistant",
        source_url="https://github.com/daxrpm/dax-assistant",
        pattern="backend-authoritative policy, approvals, audit and client separation",
        source_license="reference pattern; verify exact license before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Scope",
        capability_id="multi-device-command",
        adoption="adopt_now",
        reason="keeps phone, desktop and agents behind one policy layer",
    ),
    MarketPattern(
        id="opendex-voice-ux",
        source="OpenDex",
        source_url="https://github.com/wassgha/opendex",
        pattern="voice-first Jarvis UX with hotkeys, local command intent and permission gate",
        source_license="reference pattern; verify exact license before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Operator",
        capability_id="daily-focus",
        adoption="adapt_pattern",
        reason="voice UX should reduce friction without bypassing approvals",
    ),
    MarketPattern(
        id="somi-control-room",
        source="SOMI",
        source_url="https://github.com/Somi-Project/Somi",
        pattern="control-room product surface with research, coding, design and automation studios",
        source_license="reference pattern; verify exact license before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Operator",
        capability_id="workflow-console",
        adoption="adopt_now",
        reason="KAIZEN7 needs studios and dashboards, not only chat",
    ),
    MarketPattern(
        id="developer-studio-pattern",
        source="Codex/OpenHands/Pioneer",
        source_url="https://github.com/All-Hands-AI/OpenHands",
        pattern="developer studio with repo context, tests, review gates and safe patches",
        source_license="reference pattern; verify exact license before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Operator",
        capability_id="developer-studio",
        adoption="adopt_now",
        reason="a serious product agent needs a first-class software workbench",
    ),
    MarketPattern(
        id="designer-studio-pattern",
        source="SOMI / product design agent tools",
        source_url="https://github.com/Somi-Project/Somi",
        pattern="designer studio for brand, content, product assets and approval-first publishing",
        source_license="reference pattern; verify exact license before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="Content Factory",
        capability_id="designer-studio",
        adoption="adopt_now",
        reason="business growth needs content/design production, not only code and chat",
    ),
    MarketPattern(
        id="skill-library",
        source="Hermes skills / DeepSeek Harness plugins / Codex skills",
        source_url="https://github.com/NousResearch/hermes-agent",
        pattern="skills as reusable, tested operating units with owners, permissions and receipts",
        source_license="reference pattern; verify exact license before code reuse",
        license_posture="compatible-pattern",
        kaizen7_layer="K7 Operator",
        capability_id="skill-forge",
        adoption="adopt_now",
        reason="a market-ready agent must grow by adding verified skills, not ad-hoc prompts",
    ),
)
