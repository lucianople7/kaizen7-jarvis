from __future__ import annotations

from types import SimpleNamespace

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.monetization import (
    MonetizationEngine,
    default_monetization_engine,
)


def _config(tmp_path):
    return SimpleNamespace(memory=SimpleNamespace(data_dir=tmp_path))


def test_default_engine_exposes_growth_playbooks() -> None:
    engine = default_monetization_engine()

    playbooks = engine.playbooks()
    ids = {item["id"] for item in playbooks}

    assert {
        "viral-content-loop",
        "offer-ladder",
        "ecommerce-readiness",
        "lead-magnet-funnel",
        "affiliate-monetization",
        "retention-upsell",
    } <= ids
    assert all(item["execution_enabled"] is False for item in playbooks)


def test_growth_pack_focuses_viral_content_ecommerce_and_monetization() -> None:
    pack = default_monetization_engine().growth_pack(
        "Monetize THE FOCUX with viral content and ecommerce",
        business="THE FOCUX",
        audience="premium buyers interested in focused products",
        assets=("logo", "founding story"),
        constraints=("no_paid_ads", "approval_required"),
    )

    assert pack["schema_version"] == "kaizen7.monetization_pack.v1"
    assert pack["business"] == "THE FOCUX"
    assert pack["primary_lane"] == "ecommerce"
    assert pack["viral_content"]["formats"]
    assert pack["offer"]["ladder"][0]["name"] == "Free trust asset"
    assert pack["monetization_paths"][0]["path"] in {
        "curated ecommerce",
        "founding offer",
        "digital product",
        "affiliate",
    }
    assert any(item["gate"] == "publishing" for item in pack["risk_gates"])
    assert any(check["category"] == "checkout" for check in pack["ecommerce_readiness"])
    assert pack["execution_enabled"] is False
    assert pack["requires_human_approval"] is True


def test_growth_pack_limits_priorities_and_creates_measurable_experiments() -> None:
    pack = default_monetization_engine().growth_pack(
        "Create a monetization path for a personal AI agent",
        needs=("content", "sales", "monetization"),
    )

    assert len(pack["priorities"]) <= 3
    assert len(pack["experiments"]) == 3
    assert all(experiment["metric"] for experiment in pack["experiments"])
    assert all(experiment["duration_days"] <= 14 for experiment in pack["experiments"])


def test_quick_start_returns_one_clear_next_move_and_score() -> None:
    quick = default_monetization_engine().quick_start(
        "Monetize THE FOCUX with viral content and ecommerce",
        business="THE FOCUX",
        audience="premium buyers",
    )

    assert quick["schema_version"] == "kaizen7.monetization_quick_start.v1"
    assert quick["business"] == "THE FOCUX"
    assert quick["opportunity_score"] >= 80
    assert quick["next_move"]["title"]
    assert quick["next_move"]["why"]
    assert len(quick["quick_actions"]) == 3
    assert quick["quick_actions"][0]["minutes"] <= 30
    assert quick["ready_prompt"].startswith("Create a proposal-only growth asset")
    assert quick["execution_enabled"] is False
    assert quick["requires_human_approval"] is True


def test_quick_start_detects_lower_readiness_when_buyer_is_generic() -> None:
    quick = default_monetization_engine().quick_start("make money")

    assert quick["opportunity_score"] < 80
    assert "Define the buyer" in quick["quick_actions"][0]["action"]


def test_growth_proposal_records_receipt_without_execution(tmp_path) -> None:
    engine = default_monetization_engine()
    bridge = ControlBridgeStore.from_config(_config(tmp_path))

    proposal = engine.propose(
        "Build a viral launch pack",
        bridge=bridge,
        business="KAIZEN7 Jarvis",
        audience="founders and builders",
    )

    assert proposal["status"] == "proposed"
    assert proposal["growth_pack"]["business"] == "KAIZEN7 Jarvis"
    assert proposal["execution_enabled"] is False
    receipt = bridge.receipts()[0]
    assert receipt["kind"] == "monetization_proposal"
    assert receipt["business"] == "KAIZEN7 Jarvis"


def test_engine_rejects_blank_objective() -> None:
    engine = MonetizationEngine()

    try:
        engine.growth_pack("   ")
    except ValueError as exc:
        assert "objective cannot be blank" in str(exc)
    else:
        raise AssertionError("blank objective should fail")
