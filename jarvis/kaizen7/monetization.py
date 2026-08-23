"""Monetization engine for KAIZEN7 Jarvis.

This module turns a business objective into a proposal-only growth pack:
content, offer, ecommerce readiness, monetization paths, experiments, gates and
receipt memory. It never publishes, charges, spends or collects customer data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from jarvis.kaizen7.bridge import APPROVAL_REQUIRED_FOR, ControlBridgeStore, _utc_now


@dataclass(frozen=True)
class GrowthPlaybook:
    id: str
    title: str
    lane: str
    summary: str
    outputs: tuple[str, ...]
    metric: str
    risk_gates: tuple[str, ...]
    execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "lane": self.lane,
            "summary": self.summary,
            "outputs": list(self.outputs),
            "metric": self.metric,
            "risk_gates": list(self.risk_gates),
            "execution_enabled": self.execution_enabled,
        }


class MonetizationEngine:
    def __init__(self, playbooks: tuple[GrowthPlaybook, ...] = ()) -> None:
        self._playbooks = playbooks or _DEFAULT_PLAYBOOKS

    def playbooks(self) -> list[dict[str, Any]]:
        return [playbook.as_dict() for playbook in self._playbooks]

    def growth_pack(
        self,
        objective: str,
        *,
        business: str = "KAIZEN7 Business",
        audience: str = "buyers with a costly problem",
        assets: tuple[str, ...] | list[str] = (),
        needs: tuple[str, ...] | list[str] = (),
        constraints: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        clean_objective = " ".join(objective.strip().split())
        if not clean_objective:
            raise ValueError("objective cannot be blank.")
        clean_business = " ".join(business.strip().split()) or "KAIZEN7 Business"
        clean_audience = " ".join(audience.strip().split()) or "buyers with a costly problem"
        tokens = _tokens(clean_objective, needs)
        lane = _select_lane(tokens)
        selected_playbooks = _select_playbooks(tokens, lane, self._playbooks)
        priorities = _priorities(lane)
        return {
            "schema_version": "kaizen7.monetization_pack.v1",
            "objective": clean_objective,
            "business": clean_business,
            "audience": clean_audience,
            "primary_lane": lane,
            "priorities": priorities,
            "playbooks": [item.as_dict() for item in selected_playbooks],
            "assets_available": list(assets),
            "viral_content": _viral_content(clean_business, clean_audience, lane),
            "offer": _offer_ladder(clean_business),
            "monetization_paths": _monetization_paths(tokens, lane),
            "ecommerce_readiness": _ecommerce_readiness(),
            "experiments": _experiments(lane),
            "risk_gates": _risk_gates(constraints),
            "next_actions": _next_actions(lane),
            "receipt_seed": {
                "kind": "monetization_proposal",
                "business": clean_business,
                "lane": lane,
                "metric": selected_playbooks[0].metric if selected_playbooks else "revenue signal",
            },
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
        assets: tuple[str, ...] | list[str] = (),
        needs: tuple[str, ...] | list[str] = (),
        constraints: tuple[str, ...] | list[str] = (),
    ) -> dict[str, Any]:
        pack = self.growth_pack(
            objective,
            business=business,
            audience=audience,
            assets=assets,
            needs=needs,
            constraints=constraints,
        )
        now = _utc_now()
        proposal = {
            "id": f"monetization-{uuid4().hex}",
            "business": pack["business"],
            "objective": pack["objective"],
            "primary_lane": pack["primary_lane"],
            "growth_pack": pack,
            "status": "proposed",
            "execution_enabled": False,
            "requires_human_approval": True,
            "created_at": now,
        }
        bridge.record_receipt(
            {
                "id": proposal["id"],
                "kind": "monetization_proposal",
                "business": pack["business"],
                "objective": pack["objective"],
                "primary_lane": pack["primary_lane"],
                "metric": pack["receipt_seed"]["metric"],
                "status": "recorded",
                "execution_enabled": False,
                "created_at": now,
            }
        )
        return proposal


def default_monetization_engine() -> MonetizationEngine:
    return MonetizationEngine()


def _tokens(objective: str, needs: tuple[str, ...] | list[str]) -> set[str]:
    text = " ".join([objective, *[str(item) for item in needs]]).lower()
    normalized = text.replace("-", " ").replace("_", " ")
    return {part.strip(".,:;!?()[]{}") for part in normalized.split() if part.strip()}


def _select_lane(tokens: set[str]) -> str:
    if tokens & {"ecommerce", "store", "checkout", "product", "catalog", "shop"}:
        return "ecommerce"
    if tokens & {"viral", "content", "video", "tiktok", "youtube", "reels", "post"}:
        return "content"
    if tokens & {"offer", "sales", "lead", "funnel", "outreach"}:
        return "sales"
    if tokens & {"monetize", "monetization", "revenue", "pricing", "affiliate"}:
        return "monetization"
    return "business_improvement"


def _select_playbooks(
    tokens: set[str],
    lane: str,
    playbooks: tuple[GrowthPlaybook, ...],
) -> list[GrowthPlaybook]:
    selected = [
        item
        for item in playbooks
        if item.lane == lane or item.lane in {"content", "monetization"}
    ]
    if tokens & {"ecommerce", "checkout", "shop", "store"}:
        selected.extend(item for item in playbooks if item.id == "ecommerce-readiness")
    unique: dict[str, GrowthPlaybook] = {}
    for item in selected:
        unique[item.id] = item
    return list(unique.values())[:4]


def _priorities(lane: str) -> list[str]:
    base = {
        "content": ["one viral angle", "one trust proof", "one lead capture"],
        "sales": ["one painful buyer problem", "one offer promise", "one objection answer"],
        "ecommerce": ["one product page", "one checkout gate", "one conversion metric"],
        "monetization": ["one paid path", "one price test", "one proof asset"],
        "business_improvement": ["one bottleneck", "one metric", "one next experiment"],
    }
    return base.get(lane, base["business_improvement"])


def _viral_content(business: str, audience: str, lane: str) -> dict[str, Any]:
    return {
        "hook_formula": "painful problem + surprising mechanism + concrete payoff",
        "angles": [
            f"Why {audience} lose money before they see the real bottleneck",
            f"The fastest visible win {business} can create this week",
            "Before/after: scattered effort versus one measurable offer",
        ],
        "formats": ["short video script", "carousel", "email story", "landing-page section"],
        "cta": "Join the founding list or request the first offer pack",
        "mode": "draft_only",
    }


def _offer_ladder(business: str) -> dict[str, Any]:
    return {
        "promise": f"{business} turns attention into measurable business progress",
        "ladder": [
            {"name": "Free trust asset", "price": "free", "goal": "capture qualified interest"},
            {"name": "Founding offer", "price": "low-ticket", "goal": "prove willingness to pay"},
            {"name": "Core product", "price": "mid-ticket", "goal": "deliver repeatable outcome"},
            {"name": "Premium implementation", "price": "high-ticket", "goal": "turn proof into service revenue"},
        ],
        "proof_needed": ["clear before/after", "one metric", "one testimonial or internal receipt"],
    }


def _monetization_paths(tokens: set[str], lane: str) -> list[dict[str, str]]:
    paths = [
        {"path": "founding offer", "why": "fastest way to test buyer intent before building more"},
        {"path": "digital product", "why": "scales expertise after the first proof assets exist"},
        {"path": "affiliate", "why": "monetizes curated tool trust without owning inventory"},
    ]
    if lane == "ecommerce" or "ecommerce" in tokens:
        paths.insert(0, {"path": "curated ecommerce", "why": "turns trust and selection into checkout-ready offers"})
    return paths[:4]


def _ecommerce_readiness() -> list[dict[str, str]]:
    return [
        {"category": "product", "check": "one clear product, buyer, promise and proof"},
        {"category": "page", "check": "headline, benefit stack, objections, proof and CTA"},
        {"category": "checkout", "check": "payment, taxes, refund policy and delivery path reviewed"},
        {"category": "claims", "check": "health, legal, financial or scarcity claims require evidence review"},
        {"category": "analytics", "check": "track views, clicks, leads, add-to-cart and purchase intent"},
    ]


def _experiments(lane: str) -> list[dict[str, Any]]:
    experiments = {
        "content": [
            ("3-hook content sprint", "save rate", 7),
            ("founding-list CTA test", "email signups", 7),
            ("proof-first post", "qualified replies", 7),
        ],
        "ecommerce": [
            ("product-page clarity test", "CTA clicks", 7),
            ("founding offer waitlist", "qualified leads", 10),
            ("checkout-risk audit", "blocked risks removed", 3),
        ],
        "sales": [
            ("objection-led offer test", "reply rate", 7),
            ("lead magnet test", "opt-ins", 10),
            ("price-anchor test", "qualified calls", 14),
        ],
        "monetization": [
            ("founding price test", "paid intent", 14),
            ("affiliate shortlist test", "tracked clicks", 10),
            ("bundle test", "offer replies", 7),
        ],
    }
    selected = experiments.get(lane, experiments["monetization"])
    return [
        {"name": name, "metric": metric, "duration_days": days, "mode": "proposal_only"}
        for name, metric, days in selected
    ]


def _risk_gates(constraints: tuple[str, ...] | list[str]) -> list[dict[str, str]]:
    gates = [
        {"gate": "publishing", "rule": "human approval before external publishing"},
        {"gate": "payments", "rule": "human approval before payment setup or charges"},
        {"gate": "credentials", "rule": "never store keys, cookies or tokens in Git"},
        {"gate": "customer_data", "rule": "approved privacy path before collecting customer data"},
        {"gate": "claims", "rule": "evidence review before regulated or scarcity claims"},
    ]
    if any(str(item).lower() == "no_paid_ads" for item in constraints):
        gates.append({"gate": "ad_spend", "rule": "paid ads are blocked for this pack"})
    for item in APPROVAL_REQUIRED_FOR:
        if not any(gate["gate"] == item for gate in gates):
            gates.append({"gate": item, "rule": "requires human approval"})
    return gates


def _next_actions(lane: str) -> list[str]:
    actions = {
        "content": [
            "draft 3 hooks from the strongest buyer pain",
            "choose one proof asset",
            "prepare a lead capture CTA",
        ],
        "ecommerce": [
            "write one product page skeleton",
            "run checkout and claims readiness checks",
            "prepare a founding offer waitlist CTA",
        ],
        "sales": [
            "write one offer card",
            "map top 5 objections",
            "prepare one lead magnet",
        ],
        "monetization": [
            "choose the first paid path",
            "define the price hypothesis",
            "draft the proof asset",
        ],
    }
    return actions.get(lane, actions["monetization"])


_DEFAULT_PLAYBOOKS: tuple[GrowthPlaybook, ...] = (
    GrowthPlaybook(
        id="viral-content-loop",
        title="Viral Content Loop",
        lane="content",
        summary="Turn a buyer pain into repeatable hooks, proof assets and CTAs.",
        outputs=("hooks", "short_script", "carousel", "cta"),
        metric="saves, replies or qualified clicks",
        risk_gates=("publishing", "claims"),
    ),
    GrowthPlaybook(
        id="offer-ladder",
        title="Offer Ladder",
        lane="sales",
        summary="Move from free trust asset to founding offer, core product and premium implementation.",
        outputs=("offer_card", "pricing_hypothesis", "objection_map"),
        metric="qualified replies or paid intent",
        risk_gates=("payments", "claims"),
    ),
    GrowthPlaybook(
        id="ecommerce-readiness",
        title="Ecommerce Readiness",
        lane="ecommerce",
        summary="Check product page, proof, claims, checkout, fulfillment and analytics before launch.",
        outputs=("product_page_checklist", "checkout_gate", "analytics_plan"),
        metric="checkout blockers removed",
        risk_gates=("payments", "credentials", "claims"),
    ),
    GrowthPlaybook(
        id="lead-magnet-funnel",
        title="Lead Magnet Funnel",
        lane="monetization",
        summary="Convert attention into owned audience before paid offers.",
        outputs=("lead_magnet", "signup_cta", "followup_email"),
        metric="qualified leads",
        risk_gates=("customer_data", "publishing"),
    ),
    GrowthPlaybook(
        id="affiliate-monetization",
        title="Affiliate Monetization",
        lane="monetization",
        summary="Monetize trusted tool/product curation without owning inventory.",
        outputs=("shortlist", "disclosure", "tracked_link_plan"),
        metric="tracked clicks or affiliate revenue",
        risk_gates=("publishing", "claims"),
    ),
    GrowthPlaybook(
        id="retention-upsell",
        title="Retention Upsell",
        lane="business_improvement",
        summary="Turn delivered value into repeat purchases, upgrades and referrals.",
        outputs=("success_metric", "upsell_trigger", "referral_prompt"),
        metric="repeat purchase or upgrade intent",
        risk_gates=("outbound_messages", "customer_data"),
    ),
)
