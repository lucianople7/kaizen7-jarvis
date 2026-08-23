from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis.kaizen7.adapters import (
    AgentAdapter,
    AdapterRegistry,
    default_adapter_registry,
)
from jarvis.kaizen7.bridge import ControlBridgeStore


def _config(tmp_path):
    return SimpleNamespace(memory=SimpleNamespace(data_dir=tmp_path))


def test_default_adapters_cover_any_agent_model_or_cloud_surface() -> None:
    registry = default_adapter_registry()

    adapters = registry.list()
    ids = {adapter["id"] for adapter in adapters}
    kinds = {adapter["kind"] for adapter in adapters}

    assert {
        "openai-compatible",
        "generic-http-api",
        "generic-cli-agent",
        "mcp-server",
        "webhook-agent",
        "cloud-agent",
    } <= ids
    assert {"openai_compatible", "api", "cli", "mcp", "webhook", "cloud_agent"} <= kinds
    assert all(adapter["execution_mode"] == "proposal_only" for adapter in adapters)
    assert all(adapter["execution_enabled"] is False for adapter in adapters)


def test_adapter_manifest_is_safe_and_secret_free() -> None:
    registry = default_adapter_registry()

    manifest = registry.manifest()

    assert manifest["schema_version"] == "kaizen7.adapter.v1"
    assert manifest["execution_enabled"] is False
    assert manifest["requires_human_approval"] is True
    assert "OPENAI_API_KEY" in {
        env for adapter in manifest["adapters"] for env in adapter["required_env"]
    }
    assert not any("sk-" in str(adapter) for adapter in manifest["adapters"])


def test_adapter_recommendation_prefers_local_cli_when_local_only() -> None:
    registry = default_adapter_registry()

    recommendation = registry.recommend(
        "Run private local diagnostics",
        needs=("diagnostics", "local"),
        constraints=("local_only", "no_paid_api"),
    )

    assert recommendation["selected"]["id"] == "generic-cli-agent"
    assert recommendation["selected"]["privacy"] == "local"
    assert all(item["privacy"] == "local" for item in recommendation["ranked"])
    assert any(item["id"] == "openai-compatible" for item in recommendation["rejected"])


def test_adapter_proposal_records_receipt_without_execution(tmp_path) -> None:
    registry = default_adapter_registry()
    bridge = ControlBridgeStore.from_config(_config(tmp_path))

    proposal = registry.propose(
        "openai-compatible",
        "Use any OpenAI-compatible model for research",
        bridge=bridge,
        context={"base_url": "https://example.invalid/v1"},
    )

    assert proposal["adapter_id"] == "openai-compatible"
    assert proposal["execution_enabled"] is False
    assert proposal["requires_human_approval"] is True
    assert bridge.receipts()[0]["kind"] == "adapter_proposal"


def test_registry_rejects_adapter_with_enabled_execution() -> None:
    registry = AdapterRegistry()

    with pytest.raises(ValueError, match="execution_disabled"):
        registry.register(
            AgentAdapter(
                id="unsafe",
                label="Unsafe",
                kind="api",
                description="Unsafe execution adapter.",
                capabilities=("chat",),
                auth="api_key_env",
                required_env=("UNSAFE_KEY",),
                execution_mode="approved_run",
                execution_enabled=True,
            )
        )
