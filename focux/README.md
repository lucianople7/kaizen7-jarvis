# THE FOCUX DNA — portable business-agent core

The business logic of THE FOCUX Agent as a self-contained, shell-agnostic
layer. It runs on this runtime (KAIZEN7 Jarvis), CowAgent, OpenClaw, or any
future shell — the same DNA everywhere.

## Layout

- `policy/` — deterministic modules, **NO LLM in decision paths**:
  - `money_gate.py` — approval boundary (ALLOW/REVIEW/DENY, falsification test)
  - `constitution.py` — three immutable laws as code + evidence verdicts
  - `focux_soul.py` — SOUL.md model, validation and injection defense
  - `focux_voice.py` — voice profile builder (interview + absence signals)
  - `focux_content.py` — content matrix (pillars x 8 formats) + hook generator
  - `focux_cli.py` — agent-native CLI layer (registry + install/spend gating)
- `skills/` — 17 SKILL.md skills (13 base + voice-builder, content-matrix,
  hook-generator, cli-hub-meta-skill)
- `soul/SOUL.md.template` — evolving identity document skeleton
- `constitution.md` — the three laws (docs form)
- `tools/skill_validator.py` — format validator for `skills/*/SKILL.md`
- `docs/research/` — absorption analyses (Charlie Hills, Automaton, CLI-Anything)
- `docs/plans/2026-08-28-thefocux-agent-design.md` — the design spec

## Test

```bash
python -m pytest -q
python tools/skill_validator.py
```

## Non-negotiables

- The money gate is deterministic. No LLM ever decides a money action.
- Falsification test: with the gate off, the agent must not move money.
- Survival tiers change effort, never authorization.
- Self-improvement is evidence-gated, human-reviewed, append-only audited.
- Every executed action writes a receipt into `memory/receipts/`.

## Absorbed patterns (named sources)

| Source | Pattern | Where it lives |
| --- | --- | --- |
| Conway Automaton (MIT) | Constitution, survival tiers, SOUL validator, audit log | `policy/constitution.py`, `policy/focux_soul.py` |
| Charlie Hills social-media-skills (MIT) | Voice foundation, content matrix, hooks, deterministic scoring | `policy/focux_voice.py`, `policy/focux_content.py` |
| CLI-Anything (Apache-2.0) | Agent-native computer use (CLI-first, --json, SKILL.md per CLI) | `policy/focux_cli.py`, `skills/cli-hub-meta-skill` |
| Prime Agent | `/refine` Continual Harness (evidence-backed, rollback) | `skills/self-improvement` |
