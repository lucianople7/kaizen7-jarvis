from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis.kaizen7.bridge import ControlBridgeStore


def _config(tmp_path):
    return SimpleNamespace(memory=SimpleNamespace(data_dir=tmp_path))


def test_status_is_recommendation_only_and_persistent(tmp_path) -> None:
    store = ControlBridgeStore.from_config(_config(tmp_path))

    status = store.status()

    assert status["ready"] is True
    assert status["mode"] == "recommendation_only"
    assert status["execution_enabled"] is False
    assert "payments" in status["approval_required_for"]
    assert status["receipts_count"] == 0
    assert str(tmp_path) in status["storage_path"]


def test_proposal_records_a_receipt_without_execution(tmp_path) -> None:
    store = ControlBridgeStore.from_config(_config(tmp_path))

    proposal = store.propose("Review the weekly sales plan")
    receipts = store.receipts()

    assert proposal["status"] == "proposed"
    assert proposal["execution_enabled"] is False
    assert proposal["requires_human_approval"] is True
    assert proposal["message"] == "Review the weekly sales plan"
    assert proposal["recommendation"]
    assert len(receipts) == 1
    assert receipts[0]["id"] == proposal["id"]
    assert receipts[0]["kind"] == "proposal"
    assert receipts[0]["status"] == "recorded"


def test_receipts_survive_a_new_store_instance(tmp_path) -> None:
    ControlBridgeStore.from_config(_config(tmp_path)).propose("First move")

    fresh = ControlBridgeStore.from_config(_config(tmp_path))

    assert fresh.status()["receipts_count"] == 1
    assert fresh.receipts()[0]["message"] == "First move"


def test_blank_proposals_are_rejected(tmp_path) -> None:
    store = ControlBridgeStore.from_config(_config(tmp_path))

    with pytest.raises(ValueError):
        store.propose("   ")
