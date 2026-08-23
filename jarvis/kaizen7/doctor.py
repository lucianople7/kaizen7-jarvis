"""KAIZEN7 readiness diagnostics.

The KAIZEN7 layer is useful only if a fresh install can tell the user what is
ready, what is optional, and what will never execute without approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from jarvis.kaizen7.bridge import APPROVAL_REQUIRED_FOR, ControlBridgeStore
from jarvis.kaizen7.capabilities import default_capability_registry
from jarvis.kaizen7.codex_runtime import CodexRuntime
from jarvis.kaizen7.hermes_runtime import HermesRuntime
from jarvis.kaizen7.market_blueprint import default_market_blueprint
from jarvis.kaizen7.providers import default_provider_registry

Status = Literal["ok", "warn", "fail", "info"]


@dataclass(frozen=True)
class Kaizen7DoctorFinding:
    category: str
    status: Status
    message: str
    hint: str = ""


def run_kaizen7_doctor(
    config: Any | None = None,
    *,
    hermes: HermesRuntime | None = None,
    codex: CodexRuntime | None = None,
    bridge: ControlBridgeStore | None = None,
) -> list[Kaizen7DoctorFinding]:
    """Return KAIZEN7 readiness findings without executing external actions."""

    hermes = hermes or HermesRuntime.from_environment()
    codex = codex or CodexRuntime.from_environment()
    bridge = bridge or ControlBridgeStore.from_config(config)

    findings: list[Kaizen7DoctorFinding] = []

    bridge_status = bridge.status()
    required = set(APPROVAL_REQUIRED_FOR)
    advertised = set(bridge_status.get("approval_required_for", []))
    if bridge_status.get("mode") == "recommendation_only" and not bridge_status.get(
        "execution_enabled"
    ):
        findings.append(
            Kaizen7DoctorFinding(
                "control-bridge",
                "ok",
                "bridge is recommendation-only and execution is disabled",
            )
        )
    else:
        findings.append(
            Kaizen7DoctorFinding(
                "control-bridge",
                "fail",
                "bridge safety mode is not locked to recommendation-only",
                "Do not use external actions until execution is disabled.",
            )
        )
    missing_approvals = sorted(required - advertised)
    if missing_approvals:
        findings.append(
            Kaizen7DoctorFinding(
                "control-bridge",
                "fail",
                "approval guard is missing categories: " + ", ".join(missing_approvals),
                "Restore the KAIZEN7 approval contract before running live work.",
            )
        )
    else:
        findings.append(
            Kaizen7DoctorFinding(
                "control-bridge",
                "ok",
                "human approval guard covers sensitive operations",
            )
        )
    findings.append(
        Kaizen7DoctorFinding(
            "control-bridge",
            "info",
            f"receipt store: {bridge_status.get('storage_path', '')}",
        )
    )

    providers = default_provider_registry().list()
    unsafe_providers = [
        provider["id"] for provider in providers if provider.get("execution_enabled")
    ]
    if unsafe_providers:
        findings.append(
            Kaizen7DoctorFinding(
                "providers",
                "fail",
                "providers expose execution by default: " + ", ".join(unsafe_providers),
                "Keep every provider proposal-only until a human approval contract exists.",
            )
        )
    else:
        findings.append(
            Kaizen7DoctorFinding(
                "providers",
                "ok",
                f"universal provider registry ready: {len(providers)} connectors",
                "Hermes, Codex, generic API, generic CLI.",
            )
        )

    capabilities = default_capability_registry().list()
    unsafe_capabilities = [
        item["id"] for item in capabilities if item.get("execution_enabled")
    ]
    if unsafe_capabilities:
        findings.append(
            Kaizen7DoctorFinding(
                "capabilities",
                "fail",
                "capabilities expose execution by default: "
                + ", ".join(unsafe_capabilities),
                "Keep capabilities proposal-only until an approval adapter exists.",
            )
        )
    else:
        findings.append(
            Kaizen7DoctorFinding(
                "capabilities",
                "ok",
                f"capability marketplace ready: {len(capabilities)} safe capabilities",
                "Agent OS pack: memory, mobile, context, workflow, developer, designer.",
            )
        )

    market_patterns = default_market_blueprint().list()
    copied_patterns = [item["id"] for item in market_patterns if item.get("copy_code")]
    if copied_patterns:
        findings.append(
            Kaizen7DoctorFinding(
                "market-blueprint",
                "fail",
                "market patterns copied code: " + ", ".join(copied_patterns),
                "Keep the blueprint as legal pattern adaptation unless explicitly approved.",
            )
        )
    else:
        findings.append(
            Kaizen7DoctorFinding(
                "market-blueprint",
                "ok",
                f"market pattern fork ready: {len(market_patterns)} patterns",
                "no third-party code copied; patterns are mapped to KAIZEN7 capabilities.",
            )
        )

    hermes_status = hermes.status()
    if hermes_status.get("installed"):
        findings.append(
            Kaizen7DoctorFinding(
                "hermes",
                "ok",
                f"Hermes detected: {hermes_status.get('version', '')}",
            )
        )
        profile_count = int(hermes_status.get("profile_count", 0) or 0)
        findings.append(
            Kaizen7DoctorFinding(
                "hermes",
                "ok" if profile_count else "warn",
                f"Hermes profiles visible: {profile_count}",
                "" if profile_count else "Create the kaizen7/market/sales/content/ops profiles in Hermes Bot Mode.",
            )
        )
    else:
        findings.append(
            Kaizen7DoctorFinding(
                "hermes",
                "warn",
                "Hermes CLI not detected",
                "Install Hermes Agent or set KAIZEN7_HERMES_CLI/HERMES_CLI.",
            )
        )

    bot_contract = hermes.bot_mode_contract()
    recommended = bot_contract.get("recommended_bots", [])
    installed_bots = [
        str(bot.get("profile", "")) for bot in recommended if bot.get("installed")
    ]
    findings.append(
        Kaizen7DoctorFinding(
            "hermes",
            "info",
            f"recommended Bot Mode profiles installed: {len(installed_bots)}/{len(recommended)}",
            "Recommended: kaizen7, market, sales, content, ops.",
        )
    )

    codex_status = codex.status()
    if codex_status.get("installed"):
        findings.append(
            Kaizen7DoctorFinding(
                "codex",
                "ok",
                f"Codex CLI detected: {codex_status.get('version', '')}",
            )
        )
    else:
        findings.append(
            Kaizen7DoctorFinding(
                "codex",
                "warn",
                "Codex CLI not detected",
                "Install Codex CLI or set KAIZEN7_CODEX_CLI/CODEX_CLI.",
            )
        )
    if codex_status.get("execution_enabled") is False:
        findings.append(
            Kaizen7DoctorFinding(
                "codex",
                "ok",
                "Codex bridge only prepares delegation plans; it does not execute",
            )
        )
    else:
        findings.append(
            Kaizen7DoctorFinding(
                "codex",
                "fail",
                "Codex bridge reports execution enabled",
                "Keep Codex execution behind explicit human approval.",
            )
        )

    return findings


def has_failures(findings: list[Kaizen7DoctorFinding]) -> bool:
    return any(item.status == "fail" for item in findings)


def render_kaizen7_doctor(findings: list[Kaizen7DoctorFinding]) -> str:
    icons = {"ok": "[ OK ]", "warn": "[WARN]", "fail": "[FAIL]", "info": "[ -- ]"}
    lines = ["KAIZEN7 Jarvis - readiness doctor", "=" * 48]
    previous: str | None = None
    for finding in findings:
        if finding.category != previous:
            lines.append("")
            lines.append(f"{finding.category}:")
            previous = finding.category
        lines.append(f"  {icons[finding.status]} {finding.message}")
        if finding.hint:
            lines.append(f"         -> {finding.hint}")
    lines.append("")
    lines.append("=" * 48)
    lines.append(
        "RESULT: FAIL - safety contract broken."
        if has_failures(findings)
        else "RESULT: OK - KAIZEN7 layer is safe to use."
    )
    return "\n".join(lines)
