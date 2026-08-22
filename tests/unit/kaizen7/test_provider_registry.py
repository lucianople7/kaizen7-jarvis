from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis.kaizen7.bridge import ControlBridgeStore
from jarvis.kaizen7.providers import (
    AgentProvider,
    ProviderRegistry,
    default_provider_registry,
)


def _config(tmp_path):
    return SimpleNamespace(memory=SimpleNamespace(data_dir=tmp_path))


def test_default_registry_exposes_hermes_codex_and_api_adapter() -> None:
    registry = default_provider_registry()

    providers = registry.list()

    assert {provider["id"] for provider in providers} >= {
        "hermes",
        "codex",
        "api",
    }
    assert all(provider["execution_enabled"] is False for provider in providers)
    assert all(provider["mode"] == "proposal_only" for provider in providers)


def test_registry_rejects_duplicate_provider_ids() -> None:
    registry = ProviderRegistry()
    provider = AgentProvider(
        id="custom",
        label="Custom Agent",
        kind="api",
        description="A custom external agent endpoint.",
        auth_methods=("api_key_env",),
        capabilities=("chat",),
    )

    registry.register(provider)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(provider)


def test_provider_proposal_records_receipt_without_execution(tmp_path) -> None:
    registry = ProviderRegistry()
    registry.register(
        AgentProvider(
            id="open-router",
            label="Open Router",
            kind="api",
            description="External API model router.",
            auth_methods=("api_key_env",),
            capabilities=("chat", "research"),
        )
    )
    bridge = ControlBridgeStore.from_config(_config(tmp_path))

    proposal = registry.propose(
        "open-router",
        "Compare three market options",
        bridge=bridge,
        context={"business": "THE FOCUX"},
    )

    assert proposal["provider_id"] == "open-router"
    assert proposal["execution_enabled"] is False
    assert proposal["requires_human_approval"] is True
    assert proposal["status"] == "proposed"
    assert proposal["context"] == {"business": "THE FOCUX"}
    receipt = bridge.receipts()[0]
    assert receipt["kind"] == "provider_proposal"
    assert receipt["provider_id"] == "open-router"


def test_unknown_provider_is_rejected(tmp_path) -> None:
    registry = ProviderRegistry()
    bridge = ControlBridgeStore.from_config(_config(tmp_path))

    with pytest.raises(KeyError):
        registry.propose("missing", "Do something", bridge=bridge)
