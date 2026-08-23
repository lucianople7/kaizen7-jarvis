# KAIZEN7 Monetization Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a proposal-only business growth engine focused on monetization, viral content, ecommerce readiness and measurable revenue experiments.

**Architecture:** Add a focused `MonetizationEngine` in the KAIZEN7 layer, expose it through FastAPI routes, surface it in doctor/readiness and command registry, and record proposals through the existing Control Bridge receipts.

**Tech Stack:** Python dataclasses, FastAPI, existing `ControlBridgeStore`, existing command registry, pytest.

## Global Constraints

- Do not publish content.
- Do not charge, configure payments, spend ad budget or change credentials.
- Do not collect customer data.
- Keep all outputs proposal-only and approval-gated.
- Produce one focused growth pack with limited priorities, metrics and gates.

---

### Task 1: Monetization Core

**Files:**
- Create: `jarvis/kaizen7/monetization.py`
- Test: `tests/unit/kaizen7/test_monetization_engine.py`

**Interfaces:**
- Produces: `GrowthPlaybook`, `MonetizationEngine`, `default_monetization_engine()`.
- Consumes: `ControlBridgeStore.record_receipt`.

- [x] Write failing tests for playbooks, Growth Pack, experiments, proposal receipts and blank objective validation.
- [x] Verify the tests fail because `jarvis.kaizen7.monetization` does not exist.
- [x] Implement the engine.
- [x] Verify unit tests pass.

### Task 2: Monetization API

**Files:**
- Create: `jarvis/ui/web/kaizen7_monetization_routes.py`
- Modify: `jarvis/ui/web/server.py`
- Test: `tests/integration/test_kaizen7_monetization_routes.py`

**Interfaces:**
- Produces: `/api/kaizen7/monetization/playbooks`, `/pack`, `/propose`.

- [x] Write failing route tests for listing playbooks, building a pack and recording a receipt.
- [x] Implement and mount the routes.
- [x] Verify route tests pass.

### Task 3: Product Surfaces

**Files:**
- Modify: `jarvis/kaizen7/doctor.py`
- Modify: `jarvis/kaizen7/product_readiness.py`
- Modify: `jarvis/commands/registry.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `default_monetization_engine().playbooks()`.
- Produces: doctor/readiness visibility and command registry discovery.

- [x] Add doctor finding for monetization.
- [x] Add readiness count and product check for growth playbooks.
- [x] Add command registry entries for playbooks, pack and propose.
- [x] Document the feature.
- [x] Run focused and expanded tests.
