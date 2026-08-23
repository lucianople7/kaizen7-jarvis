"""Product readiness score for KAIZEN7 Jarvis."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.kaizen7.agent_gateway import default_agent_gateway
from jarvis.kaizen7.adapters import default_adapter_registry
from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.capabilities import default_capability_registry
from jarvis.kaizen7.market_blueprint import default_market_blueprint
from jarvis.kaizen7.providers import default_provider_registry


def build_product_readiness(
    *,
    config: Any | None = None,
    bridge: ControlBridgeStore | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    bridge = bridge or ControlBridgeStore.from_config(config)
    agents = default_agent_gateway().list()
    adapters = default_adapter_registry().list()
    providers = default_provider_registry().list()
    capabilities = default_capability_registry().list()
    patterns = default_market_blueprint().list()
    checks = _checks(root, bridge, agents, adapters, providers, capabilities, patterns)
    passed = sum(1 for check in checks if check["status"] == "ok")
    score = round((passed / len(checks)) * 100) if checks else 0
    return {
        "status": "ready" if score >= 90 else "needs_work",
        "score": score,
        "counts": {
            "agents": len(agents),
            "adapters": len(adapters),
            "providers": len(providers),
            "capabilities": len(capabilities),
            "market_patterns": len(patterns),
        },
        "checks": checks,
        "mode": "proposal_only",
        "execution_enabled": False,
        "requires_human_approval": True,
    }


def render_product_readiness(readiness: dict[str, Any]) -> str:
    lines = ["KAIZEN7 Jarvis - product readiness", "=" * 48]
    counts = readiness["counts"]
    lines.append(
        f"Surface: {counts['agents']} agents, {counts['adapters']} adapters, "
        f"{counts['providers']} providers, "
        f"{counts['capabilities']} capabilities, "
        f"{counts['market_patterns']} market patterns"
    )
    lines.append("Safety: no execution without approval")
    lines.append("")
    for check in readiness["checks"]:
        icon = "[ OK ]" if check["status"] == "ok" else "[MISS]"
        lines.append(f"{icon} {check['category']}: {check['message']}")
    lines.append("")
    lines.append("=" * 48)
    result = "READY" if readiness["status"] == "ready" else "NEEDS WORK"
    lines.append(f"RESULT: {result} ({readiness['score']}/100)")
    return "\n".join(lines)


def _checks(
    root: Path,
    bridge: ControlBridgeStore,
    agents: list[dict[str, Any]],
    adapters: list[dict[str, Any]],
    providers: list[dict[str, Any]],
    capabilities: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
) -> list[dict[str, str]]:
    bridge_status = bridge.status()
    return [
        _check("install", (root / "install" / "install.ps1").exists(), "Windows installer present"),
        _check("install", (root / "install" / "install.sh").exists(), "Unix installer present"),
        _check("security", bridge_status.get("execution_enabled") is False, "execution disabled by default"),
        _check("security", bool(bridge_status.get("approval_required_for")), "human approval categories configured"),
        _check("product", len(agents) >= 7, f"{len(agents)} agent passports registered"),
        _check("product", len(adapters) >= 6, f"{len(adapters)} adapters registered"),
        _check("product", len(providers) >= 4, f"{len(providers)} providers registered"),
        _check("product", len(capabilities) >= 19, f"{len(capabilities)} capabilities registered"),
        _check("product", len(patterns) >= 16, f"{len(patterns)} market patterns mapped"),
        _check("api", (root / "jarvis" / "ui" / "web" / "kaizen7_agent_os_routes.py").exists(), "Agent OS API mounted"),
        _check("documentation", (root / "README.md").exists(), "README present"),
        _check("documentation", (root / ".env.example").exists(), ".env.example present"),
        _check("testing", (root / "tests" / "unit" / "kaizen7").exists(), "unit tests present"),
        _check("testing", (root / "tests" / "integration").exists(), "integration tests present"),
    ]


def _check(category: str, passed: bool, message: str) -> dict[str, str]:
    return {"category": category, "status": "ok" if passed else "missing", "message": message}
