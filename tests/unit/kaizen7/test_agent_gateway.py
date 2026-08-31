from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis.kaizen7.agent_gateway import (
    AgentGateway,
    AgentPassport,
    default_agent_gateway,
)
from jarvis.kaizen7.bridge import ControlBridgeStore


def _config(tmp_path):
    return SimpleNamespace(memory=SimpleNamespace(data_dir=tmp_path))


def test_default_agent_passports_cover_real_runtime_surfaces() -> None:
    gateway = default_agent_gateway()

    agents = gateway.list()
    ids = {agent["id"] for agent in agents}

    assert {
        "kaizen7-local-cli",
        "hermes-runtime",
        "codex-cli",
        "openhands-worker",
        "mcp-tool-server",
        "openai-compatible-model",
        "generic-cloud-agent",
    } <= ids
    assert all(agent["execution_enabled"] is False for agent in agents)
    assert all(agent["requires_human_approval"] is True for agent in agents)
    assert all("capabilities" in agent for agent in agents)


def test_agent_manifest_is_vendor_agnostic_and_secret_free() -> None:
    manifest = default_agent_gateway().manifest()

    assert manifest["schema_version"] == "kaizen7.agent_gateway.v1"
    assert manifest["runtime_policy"] == "agent/model/cloud agnostic"
    assert manifest["execution_enabled"] is False
    assert "OPENAI_API_KEY" in {
        env for agent in manifest["agents"] for env in agent["required_env"]
    }
    assert "sk-" not in str(manifest)


def test_recommendation_prefers_local_coding_agent_for_private_code() -> None:
    recommendation = default_agent_gateway().recommend(
        "Fix tests in a private local repository",
        needs=("code", "tests", "local"),
        constraints=("local_only", "no_paid_api"),
    )

    assert recommendation["selected"]["id"] == "codex-cli"
    assert recommendation["selected"]["privacy"] == "local"
    assert all(item["privacy"] == "local" for item in recommendation["ranked"])
    assert any(item["id"] == "generic-cloud-agent" for item in recommendation["rejected"])


def test_bench_is_dry_run_and_detects_missing_env() -> None:
    bench = default_agent_gateway().bench("openai-compatible-model", env={})

    assert bench["agent_id"] == "openai-compatible-model"
    assert bench["status"] == "not_configured"
    assert bench["dry_run"] is True
    assert bench["execution_enabled"] is False
    assert "OPENAI_API_KEY" in bench["missing_env"]
    assert bench["checks"][0]["status"] == "missing"


def test_bench_reports_ready_when_env_contract_is_present() -> None:
    bench = default_agent_gateway().bench(
        "openai-compatible-model",
        env={"OPENAI_API_KEY": "present", "OPENAI_BASE_URL": "present"},
    )

    assert bench["status"] == "ready_for_proposal"
    assert bench["missing_env"] == []
    assert all(check["status"] == "ok" for check in bench["checks"])


def test_agent_proposal_records_receipt_without_execution(tmp_path) -> None:
    bridge = ControlBridgeStore.from_config(_config(tmp_path))
    proposal = default_agent_gateway().propose(
        "codex-cli",
        "Repair the failing tests in this repository",
        bridge=bridge,
        context={"workdir": "C:/repo"},
    )

    assert proposal["agent_id"] == "codex-cli"
    assert proposal["status"] == "proposed"
    assert proposal["execution_enabled"] is False
    assert proposal["requires_human_approval"] is True
    receipt = bridge.receipts()[0]
    assert receipt["kind"] == "agent_proposal"
    assert receipt["agent_id"] == "codex-cli"


def test_gateway_rejects_passport_with_enabled_execution() -> None:
    gateway = AgentGateway()

    with pytest.raises(ValueError, match="execution_disabled"):
        gateway.register(
            AgentPassport(
                id="unsafe-agent",
                label="Unsafe Agent",
                kind="api",
                adapter_id="generic-http-api",
                description="Unsafe live executor.",
                capabilities=("chat",),
                required_env=("UNSAFE_TOKEN",),
                execution_enabled=True,
            )
        )
