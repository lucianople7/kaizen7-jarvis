from __future__ import annotations

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.growth_os import default_growth_os


def test_growth_command_returns_one_operating_card() -> None:
    card = default_growth_os().command(
        "Monetize THE FOCUX with viral content and ecommerce",
        business="THE FOCUX",
        audience="premium buyers",
        channels=("instagram", "youtube"),
        assets=("logo", "product", "proof"),
    )

    assert card["schema_version"] == "kaizen7.growth_command.v1"
    assert card["business"] == "THE FOCUX"
    assert card["mode"] == "proposal_only"
    assert card["execution_enabled"] is False
    assert card["requires_human_approval"] is True
    assert card["monetization_quick_start"]["schema_version"] == "kaizen7.monetization_quick_start.v1"
    assert card["next_move"]["title"]
    assert card["asset_to_create"]["mode"] == "draft_only"
    assert len(card["priorities"]) <= 3
    assert card["distribution_plan"]["publishing_enabled"] is False
    assert card["ecommerce_audit"]["score"] >= 70
    assert card["agentic_commerce"]["status"] == "proposal_only"


def test_launch_kit_turns_repo_into_five_minute_product_onboarding() -> None:
    kit = default_growth_os().launch_kit(
        "Help a new user monetize with KAIZEN7 Jarvis",
        business="KAIZEN7 Jarvis",
        audience="solo builders",
    )

    assert kit["schema_version"] == "kaizen7.launch_kit.v1"
    assert kit["github_pitch"]["headline"] == "KAIZEN7 Jarvis"
    assert kit["five_minute_start"][0]["command"]
    assert kit["demo_payload"]["objective"]
    assert kit["first_value"]["success_metric"]
    assert len(kit["community_tasks"]) == 5
    assert kit["mode"] == "proposal_only"
    assert kit["execution_enabled"] is False
    assert kit["requires_human_approval"] is True


def test_growth_asset_is_draft_only_and_channel_specific() -> None:
    asset = default_growth_os().asset(
        "Create a viral launch for THE FOCUX ecommerce offer",
        business="THE FOCUX",
        audience="premium buyers",
        channel="tiktok",
    )

    assert asset["schema_version"] == "kaizen7.growth_asset.v1"
    assert asset["asset"]["type"] == "short_video_script"
    assert asset["asset"]["hook"]
    assert asset["asset"]["cta"]
    assert asset["mode"] == "proposal_only"
    assert asset["execution_enabled"] is False
    assert "publishing" in asset["approval_required_for"]


def test_ecommerce_audit_flags_missing_agent_readable_commerce() -> None:
    audit = default_growth_os().ecommerce_audit(
        business="THE FOCUX",
        assets=("logo", "product"),
    )

    assert audit["schema_version"] == "kaizen7.ecommerce_audit.v1"
    assert audit["score"] < 100
    blockers = " ".join(audit["blockers"])
    assert "proof" in blockers
    assert "agent-readable commerce" in blockers
    assert audit["checks"]["agent_readable"]["status"] == "missing"


def test_growth_proposal_records_receipt(tmp_path) -> None:
    bridge = ControlBridgeStore(root=tmp_path)
    proposal = default_growth_os().propose(
        "Build the first monetization command center",
        bridge=bridge,
        business="THE FOCUX",
        audience="premium buyers",
    )

    receipts = bridge.receipts()

    assert proposal["status"] == "proposed"
    assert proposal["execution_enabled"] is False
    assert receipts[0]["kind"] == "growth_os_proposal"
