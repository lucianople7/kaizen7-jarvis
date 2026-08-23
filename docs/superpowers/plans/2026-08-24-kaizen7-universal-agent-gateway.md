# KAIZEN7 Universal Agent Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a proposal-only Universal Agent Gateway so KAIZEN7 Jarvis can route work to any model, CLI, MCP server, runtime or cloud agent without vendor lock-in.

**Architecture:** Add `AgentPassport` as the stable contract for real agent surfaces, `AgentGateway` as the registry/router/bench/proposal service, and REST routes under `/api/kaizen7/agents`. Keep adapters as connection primitives and providers as broader connector recommendations.

**Tech Stack:** Python dataclasses, FastAPI, existing `ControlBridgeStore`, existing command registry, pytest.

## Global Constraints

- Do not execute models, CLIs, APIs, MCP servers, webhooks or cloud agents.
- Do not store secret values; expose only environment variable names and local profile names.
- Keep every passport `proposal_only`, `execution_enabled=False`, and `requires_human_approval=True`.
- Human approval remains mandatory for payments, publishing, outbound messages, credentials, financial operations, irreversible changes and deployments.
- Preserve PersonalJarvis MIT attribution and keep KAIZEN7 additions layered on top.

---

### Task 1: Agent Gateway Core

**Files:**
- Create: `jarvis/kaizen7/agent_gateway.py`
- Test: `tests/unit/kaizen7/test_agent_gateway.py`

**Interfaces:**
- Produces: `AgentPassport`, `AgentGateway`, `default_agent_gateway()`.
- Consumes: `ControlBridgeStore.record_receipt`.

- [x] Write failing tests for default passports, manifest, recommendation, bench, proposal receipt and unsafe passport rejection.
- [x] Verify the tests fail because `jarvis.kaizen7.agent_gateway` does not exist.
- [x] Implement `AgentPassport` and `AgentGateway`.
- [x] Verify the unit tests pass.

### Task 2: REST Routes

**Files:**
- Create: `jarvis/ui/web/kaizen7_agent_gateway_routes.py`
- Modify: `jarvis/ui/web/server.py`
- Test: `tests/integration/test_kaizen7_agent_gateway_routes.py`

**Interfaces:**
- Consumes: `default_agent_gateway()`.
- Produces: `/api/kaizen7/agents`, `/manifest`, `/recommend`, `/{agent_id}/bench`, `/{agent_id}/propose`.

- [x] Write failing integration tests for list, manifest, recommend, bench, propose and receipts.
- [x] Implement FastAPI routes and mount them in the web server.
- [x] Verify integration tests pass.

### Task 3: Product Surfaces

**Files:**
- Modify: `jarvis/kaizen7/doctor.py`
- Modify: `jarvis/kaizen7/product_readiness.py`
- Modify: `jarvis/commands/registry.py`
- Modify: `README.md`
- Modify: `.env.example`
- Test: `tests/unit/kaizen7/test_doctor.py`, `tests/unit/kaizen7/test_product_readiness.py`, `tests/unit/commands/test_registry_parity.py`

**Interfaces:**
- Consumes: `default_agent_gateway().list()`.
- Produces: doctor/readiness visibility and command registry entries.

- [x] Add doctor finding for `agent-gateway`.
- [x] Add readiness count and product check for agent passports.
- [x] Add command registry entries for list, manifest, recommend, bench and propose.
- [x] Document API and env contract.
- [x] Run focused tests and smoke commands.
