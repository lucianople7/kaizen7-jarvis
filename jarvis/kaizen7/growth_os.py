"""KAIZEN7 Growth OS.

One-command operating layer for monetization, content, ecommerce readiness and
agentic-commerce preparation. It creates proposal-only cards and receipts; it
never publishes, charges, spends, sends messages or changes credentials.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from jarvis.kaizen7.bridge import APPROVAL_REQUIRED_FOR, ControlBridgeStore, _utc_now
from jarvis.kaizen7.monetization import MonetizationEngine, default_monetization_engine


class GrowthOS:
    def __init__(self, monetization: MonetizationEngine | None = None) -> None:
        self._monetization = monetization or default_monetization_engine()

    def surfaces(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "growth-command",
                "title": "One-command growth card",
                "output": "next move, asset, audit, distribution plan and receipt seed",
                "execution_enabled": False,
            },
            {
                "id": "growth-asset",
                "title": "Draft-only growth asset",
                "output": "short script, carousel, landing section or email draft",
                "execution_enabled": False,
            },
            {
                "id": "launch-kit",
                "title": "Five-minute product launch kit",
                "output": "GitHub pitch, install checklist, demo payload and first value path",
                "execution_enabled": False,
            },
            {
                "id": "ecommerce-audit",
                "title": "Ecommerce and agent-readable audit",
                "output": "checkout, claims, analytics and agentic-commerce blockers",
                "execution_enabled": False,
            },
            {
                "id": "growth-proposal-receipt",
                "title": "Growth proposal receipt",
                "output": "durable proposal receipt for human approval",
                "execution_enabled": False,
            },
        ]

    def command(
        self,
        objective: str,
        *,
        business: str = "KAIZEN7 Business",
        audience: str = "buyers with a costly problem",
        channels: tuple[str, ...] | list[str] = (),
        assets: tuple[str, ...] | list[str] = (),
        constraints: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        clean_objective = _clean(objective, field="objective")
        clean_business = _clean_default(business, "KAIZEN7 Business")
        clean_audience = _clean_default(audience, "buyers with a costly problem")
        clean_channels = _clean_list(channels) or ["owned_content"]
        clean_assets = _clean_list(assets)
        quick = self._monetization.quick_start(
            clean_objective,
            business=clean_business,
            audience=clean_audience,
            assets=clean_assets,
            needs=tuple(clean_channels),
            constraints=constraints,
        )
        route = _select_route(clean_objective, clean_channels, clean_assets, quick)
        audit = self.ecommerce_audit(business=clean_business, assets=clean_assets)
        asset = self.asset(
            clean_objective,
            business=clean_business,
            audience=clean_audience,
            channel=clean_channels[0],
            route=route,
        )["asset"]
        return {
            "schema_version": "kaizen7.growth_command.v1",
            "business": clean_business,
            "objective": clean_objective,
            "audience": clean_audience,
            "route": route,
            "priorities": _priorities_for(route),
            "monetization_quick_start": quick,
            "next_move": quick["next_move"],
            "asset_to_create": asset,
            "distribution_plan": _distribution_plan(clean_channels, asset),
            "ecommerce_audit": audit,
            "agentic_commerce": _agentic_commerce(audit),
            "effectiveness_multiplier": {
                "less_steps": True,
                "reason": "one request returns move, asset, audit, distribution and receipt seed",
            },
            "approval_gates": _approval_gates(),
            "receipt_seed": {
                "kind": "growth_os_proposal",
                "business": clean_business,
                "route": route,
                "metric": quick["success_metric"],
            },
            "mode": "proposal_only",
            "execution_enabled": False,
            "requires_human_approval": True,
        }

    def launch_kit(
        self,
        objective: str,
        *,
        business: str = "KAIZEN7 Jarvis",
        audience: str = "builders and small businesses",
    ) -> dict[str, Any]:
        clean_objective = _clean(objective, field="objective")
        clean_business = _clean_default(business, "KAIZEN7 Jarvis")
        clean_audience = _clean_default(audience, "builders and small businesses")
        demo_payload = {
            "objective": clean_objective,
            "business": clean_business,
            "audience": clean_audience,
            "channels": ["owned_content", "instagram", "youtube"],
            "assets": ["logo", "product", "proof"],
        }
        first_card = self.command(
            clean_objective,
            business=clean_business,
            audience=clean_audience,
            channels=demo_payload["channels"],
            assets=demo_payload["assets"],
        )
        return {
            "schema_version": "kaizen7.launch_kit.v1",
            "github_pitch": {
                "headline": clean_business,
                "tagline": "A proposal-only business agent that turns one objective into the next monetizable move.",
                "promise": "Install it, run one growth command, get an asset, an audit, gates and a receipt.",
                "best_for": [
                    "solo builders",
                    "content-led ecommerce",
                    "agent-agnostic business operations",
                ],
            },
            "five_minute_start": [
                {
                    "step": "install",
                    "command": "irm https://raw.githubusercontent.com/lucianople7/kaizen7-jarvis/main/install/install.ps1 | iex",
                },
                {
                    "step": "doctor",
                    "command": "python -m jarvis --kaizen7-doctor",
                },
                {
                    "step": "first-growth-card",
                    "command": "python -m jarvis --kaizen7-product",
                },
            ],
            "demo_payload": demo_payload,
            "first_value": {
                "next_move": first_card["next_move"],
                "asset_type": first_card["asset_to_create"]["type"],
                "success_metric": first_card["receipt_seed"]["metric"],
                "approval_gate": "human approval before publishing, payments, messages or irreversible changes",
            },
            "community_tasks": [
                "try the launch kit on one real business objective",
                "add one new adapter passport as proposal-only",
                "improve one ecommerce audit check with evidence",
                "publish one safe example payload with no secrets",
                "report one missing install friction with exact command output",
            ],
            "acceptance_tests": [
                "doctor reports OK",
                "product readiness reports READY 100/100",
                "growth command returns a draft-only asset",
                "proposal receipt is recorded without execution",
            ],
            "mode": "proposal_only",
            "execution_enabled": False,
            "requires_human_approval": True,
        }

    def asset(
        self,
        objective: str,
        *,
        business: str = "KAIZEN7 Business",
        audience: str = "buyers with a costly problem",
        channel: str = "owned_content",
        route: str | None = None,
    ) -> dict[str, Any]:
        clean_objective = _clean(objective, field="objective")
        clean_business = _clean_default(business, "KAIZEN7 Business")
        clean_audience = _clean_default(audience, "buyers with a costly problem")
        clean_channel = _clean_default(channel, "owned_content").lower()
        selected_route = route or _select_route(clean_objective, [clean_channel], [], {})
        asset_type = _asset_type(selected_route, clean_channel, clean_objective)
        asset = {
            "type": asset_type,
            "title": f"{clean_business}: {selected_route.replace('_', ' ')} draft",
            "hook": _hook(clean_business, clean_audience, clean_objective),
            "body": _body(asset_type, clean_business, clean_audience),
            "cta": "Ask to join the founding list or request the first offer pack.",
            "channel": clean_channel,
            "mode": "draft_only",
            "approval_required_for": ["publishing", "messages", "claims"],
        }
        return {
            "schema_version": "kaizen7.growth_asset.v1",
            "business": clean_business,
            "objective": clean_objective,
            "audience": clean_audience,
            "route": selected_route,
            "asset": asset,
            "mode": "proposal_only",
            "execution_enabled": False,
            "requires_human_approval": True,
            "approval_required_for": list(APPROVAL_REQUIRED_FOR),
        }

    def ecommerce_audit(
        self,
        *,
        business: str = "KAIZEN7 Business",
        assets: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        clean_business = _clean_default(business, "KAIZEN7 Business")
        asset_tokens = {item.lower() for item in _clean_list(assets)}
        checks = {
            "product_clarity": _status(
                bool(asset_tokens & {"product", "catalog", "offer", "page"}),
                "one clear product, buyer, promise and CTA",
            ),
            "proof": _status(
                bool(asset_tokens & {"proof", "testimonial", "case-study", "receipt"}),
                "one credible proof asset before conversion claims",
            ),
            "checkout_policy": _status(
                bool(asset_tokens & {"policy", "refund", "checkout", "terms"}),
                "refund, delivery, taxes and checkout policy reviewed",
            ),
            "analytics": _status(
                bool(asset_tokens & {"analytics", "utm", "tracking", "metric"}),
                "track views, clicks, leads, checkout intent and sales",
            ),
            "agent_readable": _status(
                bool(asset_tokens & {"llms.txt", "schema", "structured-data", "mcp"}),
                "agent-readable commerce: llms.txt, structured product data or storefront MCP",
            ),
        }
        blockers = [
            f"{name}: {item['requirement']}"
            for name, item in checks.items()
            if item["status"] == "missing"
        ]
        score = max(0, 100 - (10 * len(blockers)))
        return {
            "schema_version": "kaizen7.ecommerce_audit.v1",
            "business": clean_business,
            "score": score,
            "checks": checks,
            "blockers": blockers,
            "next_fix": blockers[0] if blockers else "ready for human approval review",
            "mode": "proposal_only",
            "execution_enabled": False,
            "requires_human_approval": True,
        }

    def propose(
        self,
        objective: str,
        *,
        bridge: ControlBridgeStore,
        business: str = "KAIZEN7 Business",
        audience: str = "buyers with a costly problem",
        channels: tuple[str, ...] | list[str] = (),
        assets: tuple[str, ...] | list[str] = (),
        constraints: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        card = self.command(
            objective,
            business=business,
            audience=audience,
            channels=channels,
            assets=assets,
            constraints=constraints,
        )
        now = _utc_now()
        proposal = {
            "id": f"growth-os-{uuid4().hex}",
            "business": card["business"],
            "objective": card["objective"],
            "route": card["route"],
            "growth_command": card,
            "status": "proposed",
            "execution_enabled": False,
            "requires_human_approval": True,
            "created_at": now,
        }
        bridge.record_receipt(
            {
                "id": proposal["id"],
                "kind": "growth_os_proposal",
                "business": card["business"],
                "objective": card["objective"],
                "route": card["route"],
                "metric": card["receipt_seed"]["metric"],
                "status": "recorded",
                "execution_enabled": False,
                "created_at": now,
            }
        )
        return proposal


def default_growth_os() -> GrowthOS:
    return GrowthOS()


def _clean(value: str, *, field: str) -> str:
    cleaned = " ".join(str(value).strip().split())
    if not cleaned:
        raise ValueError(f"{field} cannot be blank.")
    return cleaned


def _clean_default(value: str, default: str) -> str:
    cleaned = " ".join(str(value).strip().split())
    return cleaned or default


def _clean_list(values: tuple[str, ...] | list[str]) -> list[str]:
    return [" ".join(str(item).strip().split()) for item in values if str(item).strip()]


def _select_route(
    objective: str,
    channels: list[str],
    assets: list[str],
    quick: dict[str, Any],
) -> str:
    text = " ".join([objective, *channels, *assets, str(quick.get("primary_lane", ""))]).lower()
    if any(word in text for word in ("checkout", "store", "shop", "ecommerce", "product")):
        return "ecommerce_launch"
    if any(word in text for word in ("llms.txt", "schema", "mcp", "agentic")):
        return "agentic_commerce"
    if any(word in text for word in ("retention", "upsell", "repeat")):
        return "retention"
    if any(word in text for word in ("distribution", "postiz", "buffer", "schedule")):
        return "distribution"
    return "content_to_offer"


def _priorities_for(route: str) -> list[str]:
    priorities = {
        "content_to_offer": ["one sharp hook", "one proof asset", "one offer CTA"],
        "ecommerce_launch": ["one product page", "one checkout gate", "one measurement path"],
        "distribution": ["one approved draft", "one channel variant", "one metric"],
        "agentic_commerce": ["one llms.txt plan", "one product schema", "one storefront adapter"],
        "retention": ["one success metric", "one upsell trigger", "one reuse prompt"],
    }
    return priorities.get(route, priorities["content_to_offer"])


def _asset_type(route: str, channel: str, objective: str) -> str:
    text = f"{route} {channel} {objective}".lower()
    if any(word in text for word in ("tiktok", "reels", "short", "video", "youtube")):
        return "short_video_script"
    if any(word in text for word in ("email", "newsletter", "lead")):
        return "email"
    if any(word in text for word in ("landing", "page", "ecommerce", "checkout")):
        return "landing_section"
    return "carousel"


def _hook(business: str, audience: str, objective: str) -> str:
    return (
        f"{audience} do not need more noise; they need {business} to turn "
        f"{objective.lower()} into one measurable next move."
    )


def _body(asset_type: str, business: str, audience: str) -> list[str]:
    body = {
        "short_video_script": [
            "Show the scattered before state in one concrete sentence.",
            f"Name how {business} reduces the next decision for {audience}.",
            "End with the smallest proof or founding-list action.",
        ],
        "landing_section": [
            "Headline: one buyer, one painful problem, one promised result.",
            "Proof block: receipt, testimonial, metric or demo evidence.",
            "CTA block: request access, join list or review founding offer.",
        ],
        "email": [
            "Subject: the bottleneck your next offer must remove.",
            "Open with the cost of waiting.",
            "Close with one reply-based CTA.",
        ],
        "carousel": [
            "Slide 1: painful problem.",
            "Slide 2: hidden mechanism.",
            "Slide 3: proof or example.",
            "Slide 4: founding offer CTA.",
        ],
    }
    return body.get(asset_type, body["carousel"])


def _distribution_plan(channels: list[str], asset: dict[str, Any]) -> dict[str, Any]:
    return {
        "channels": channels[:5],
        "variants": [
            {"channel": channel, "asset_type": asset["type"], "status": "draft_needed"}
            for channel in channels[:5]
        ],
        "publishing_enabled": False,
        "requires_human_approval": True,
    }


def _agentic_commerce(audit: dict[str, Any]) -> dict[str, Any]:
    agent_ready = audit["checks"]["agent_readable"]["status"] == "ok"
    return {
        "llms_txt": "ready" if agent_ready else "recommended",
        "structured_product_data": "ready" if agent_ready else "required before agentic commerce",
        "storefront_mcp": "adapter_candidate",
        "checkout": "human approval required",
        "status": "proposal_only",
    }


def _approval_gates() -> list[dict[str, str]]:
    return [
        {"gate": item, "rule": "human approval required before execution"}
        for item in APPROVAL_REQUIRED_FOR
    ] + [
        {"gate": "ad_spend", "rule": "human approval required before paid distribution"},
        {"gate": "claims", "rule": "evidence review required before regulated or scarcity claims"},
    ]


def _status(passed: bool, requirement: str) -> dict[str, str]:
    return {
        "status": "ok" if passed else "missing",
        "requirement": requirement,
    }
