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
            "mcp-connector-plan",
            "quality-evaluation",
        }
    ]
    recommended_now.sort(key=lambda item: _CAPABILITY_ORDER.get(item["capability_id"], 99))
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
    "mcp-connector-plan": 30,
    "quality-evaluation": 40,
}

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
)
