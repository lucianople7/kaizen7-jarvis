from __future__ import annotations

from types import SimpleNamespace

import pytest

import jarvis.core.config as core_config
from jarvis.brain import modes
from jarvis.kaizen7.bots import BotRoster


@pytest.fixture(autouse=True)
def _isolate_modes(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_config, "DATA_DIR", tmp_path)
    modes.set_section_override(None)


def _config(tmp_path):
    return SimpleNamespace(memory=SimpleNamespace(data_dir=tmp_path))


def test_roster_turns_modes_into_bots(tmp_path) -> None:
    modes.save_mode(
        slug="sales-operator",
        name="Sales Operator",
        description="Turns offers into daily sales moves.",
        character="Focus on pipeline, evidence, and next actions.",
    )

    payload = BotRoster.from_config(_config(tmp_path)).list()
    bots = {bot["slug"]: bot for bot in payload["bots"]}

    assert payload["source"] == "assistant_modes"
    assert payload["profile_primitive"] == "mode"
    assert payload["execution_enabled"] is False
    assert bots["sales-operator"]["handle"] == "@sales-operator"
    assert bots["sales-operator"]["title"] == "Sales Operator"
    assert bots["sales-operator"]["routine_namespace"] == "[bot:sales-operator]"
    assert bots["sales-operator"]["implemented"]["canonical_chat"] is False


def test_roster_marks_the_active_mode(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    modes.save_mode(
        slug="focus-agent",
        name="Focus Agent",
        character="Keep the day narrow.",
    )
    monkeypatch.setattr(modes, "_configured_slug", lambda: "focus-agent")

    payload = BotRoster.from_config(_config(tmp_path)).list()

    assert payload["active"] == "focus-agent"
    assert next(bot for bot in payload["bots"] if bot["slug"] == "focus-agent")[
        "active"
    ] is True


def test_create_proposal_records_receipt_without_creating_a_mode(tmp_path) -> None:
    roster = BotRoster.from_config(_config(tmp_path))

    proposal = roster.propose_create(
        name="Market Scout",
        title="Market Scout",
        description="Researches market evidence before action.",
    )

    assert proposal["status"] == "proposed"
    assert proposal["execution_enabled"] is False
    assert proposal["requires_human_approval"] is True
    assert proposal["draft"]["slug"] == "market-scout"
    assert modes.get_mode("market-scout") is None
