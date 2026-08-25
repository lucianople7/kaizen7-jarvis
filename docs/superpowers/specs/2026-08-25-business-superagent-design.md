# Business Superagent — Design Spec

Date: 2026-08-25
Status: approved (maintainer, autonomous session)
Scope: foundation + intelligence layer + action bodies for a personal business superagent

## 1. Vision

Build a personal **business superagent** — an always-on AI operator that creates
content, operates ecommerce, monetizes, and acts on the machine and the web to
generate money for the maintainer's businesses. It is a "CEO agent" in the
category of OpenClaw / Hermes Prime / QwenPaw: a personal agent that does not
just talk — it **moves and acts** (desktop, browser, business systems) behind
deterministic human-approval gates.

The agent is built as **portable skills + memory + policy** that run on a
shell, not as a fork of a shell. The shell can be swapped (OpenClaw today,
QwenPaw if it matures) without rewriting the business layer.

## 2. Decisions (locked)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| D1 | Shell (today) | **OpenClaw** (MIT, TS) | Mature (9 months, calendar releases, 387k stars), signed Windows app, built-in Exec Approvals, HEARTBEAT cadence, 26 channels, computer-use + browser |
| D2 | Dev lab | **DeepSeek Harness** (MIT) | Reads AGENTS.md, "everything is a plugin", already in daily use by the maintainer; ideal to author/test skills before OpenClaw install |
| D3 | Future shell | **QwenPaw** (Apache-2.0) | Re-evaluate Oct 2026: 2.x rewrite needs 2-3 months to stabilize; skills/MCP portability means migration is cheap if it matures |
| D4 | Brain | **Qwen** (Bailian/DashScope cloud or Qwen3.5 local) + **DeepSeek V4** fallback | Qwen ecosystem covers reasoning + voice + image + video; DeepSeek is the cheap reasoning fallback |
| D5 | Autonomy | **L1 supervised → L2 policy-delegated** | Money/irreversible always gated; policies deterministic, outside the LLM; the agent never knows its own limits |
| D6 | Money boundary | Deterministic policy + human approval (SecondSign pattern) | Falsification test: with the gate off, the agent must NOT be able to move money |
| D7 | Memory | File-based, curated (MEMORY.md, metrics, decisions, receipts) | Auditable, portable, cheap; per-agent workspaces with isolation |
| D8 | Commerce | **Saleor** (Python/GraphQL, official read-only MCP) primary + Stripe MCP + Lago (optional usage billing); Medusa as TypeScript alternative | OSS-solid; matches the maintainer's Python stack; read-only surface for the agent, writes gated |
| D9 | Content | Qwen-Image + Wan 3.0 API (or Wan 2.2 open) + Remotion + Postiz (self-hosted) | LLM plans calendar → assets → draft review gate → publish |
| D10 | Cadence | HEARTBEAT: Daily / Weekly / Monthly tasks, quiet hours, tuned costs | Proven OpenClaw operating pattern |

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  SHELL: OpenClaw (today) · DeepSeek Harness (lab) ·          │
│         QwenPaw (future, if mature)                         │
│  — all read AGENTS.md + SKILL.md + MCP                      │
├──────────────────────────────────────────────────────────────┤
│  INTELLIGENCE LAYER (portable, the actual product)          │
│  • skills/  — money-gate, cadence, content-pipeline,        │
│    commerce-ops, business-memory, research, multi-agent     │
│  • memory/  — MEMORY.md, metrics.md, decisions.md,          │
│    receipts/ (hash-chained evidence), plans/, workspace/    │
│  • policy/  — deterministic money/publish/action rules      │
│    (allow/deny/ask tiers, amount thresholds)                │
├──────────────────────────────────────────────────────────────┤
│  ACTION BODIES (the superagent's hands)                     │
│  • computer-use — desktop mouse/keyboard/apps (gated)       │
│  • browser-use — web navigation, forms, dashboards (gated)  │
│  • business APIs — MCP servers: commerce, payments,         │
│    publishing (Postiz MCP), CRM                             │
├──────────────────────────────────────────────────────────────┤
│  BRAIN: Qwen (Bailian cloud / Qwen3.5 local) + DeepSeek V4  │
│  fallback via OpenAI-compatible endpoints                   │
└──────────────────────────────────────────────────────────────┘
```

## 4. Agent identity & workspaces

- One **agent per business** (content brand, store, CEO orchestrator), each with:
  - `AGENTS.md` — identity, mission, brand voice, hard rules
  - `workspace/` — isolated state, sessions, outputs
- **Multi-agent minimum**: executor + reviewer + logger (per research: the
  minimum viable agent organization). Each agent logs decisions to its own
  workspace for post-mortems.

## 5. Intelligence layer — skills

Format: OpenClaw SKILL.md (YAML frontmatter: name, description, when_to_use,
version) + Markdown body. Authored in a `skills/` directory, portable across
shells (OpenClaw, DeepSeek Harness, QwenPaw).

| Skill | Purpose |
|-------|---------|
| `money-gate` | **Critical.** Every money/publish/irreversible action passes a deterministic policy + expiring human approval. The agent never knows its spending limits. Falsification test enforced. |
| `cadence` | HEARTBEAT loop: Daily (metrics snapshot, health check), Weekly (plan + report), Monthly (financial review, market brief). Cheap model + quiet hours to keep cost ~$18-50/mo. |
| `content-pipeline` | Weekly content plan (hooks, formats, themes) → assets (Qwen-Image, Wan) → deterministic assembly (Remotion) → Postiz scheduling with draft review gate before publish. |
| `commerce-ops` | Store operations via MCP (Saleor/Medusa): reads free, writes gated (pricing, discounts, refunds → approval). Idempotency keys on every mutation. |
| `business-memory` | How to read/write memory: metrics, decisions (ADR-style), receipts (hash-chained evidence, never self-written logs). |
| `research` | Market/product research with verified sources; research records keep source URLs + evidence notes. |
| `multi-agent` | Roles and escalation: executor/reviewer/logger, shared curated memory, explicit escalation paths. |

## 6. Memory architecture

Per business, plain Markdown files (auditable, editable, cheap):

- `MEMORY.md` — curated knowledge, preferences, lessons
- `metrics.md` — KPI snapshots per cadence cycle
- `decisions.md` — decision records (ADR-style: context, decision, consequences)
- `receipts/` — hash-chained evidence of every executed action (tamper-evident)
- `plans/` — weekly plans and execution queues
- `workspace/` — per-agent isolation

Long-term: ReMe (Apache-2.0, file-based, hybrid BM25+vector) as the memory
engine — shell-agnostic, works with OpenClaw, DeepSeek Harness and QwenPaw.

## 7. Money gate (L1 → L2)

- **L1 (start)**: the agent proposes; a deterministic policy engine decides
  ALLOW / REVIEW / DENY; REVIEW routes to a human approval card (recipient,
  amount, diff, audit trail) that expires (30 min default); approval is
  single-use and bound to the exact request; execution is idempotent.
- **L2 (as trust grows)**: policy thresholds loosen per action type (e.g.
  publish ≤ 3/day, refunds ≤ $50, purchases ≤ $100) — policies are declarative,
  outside the LLM, and the agent does not know them.
- **Falsification test** (from SecondSign): with the gate off, the agent must
  not be able to move money. If it can, there is no boundary.
- **Reference implementations**: SecondSign core (Apache-2.0) pattern, Google
  zero-trust ADK ($10k refund test: system prompts are soft constraints —
  hard guarantees live in the policy layer), OpenClaw Exec Approvals.

## 8. Action bodies

| Body | Capability | Gate |
|------|-----------|------|
| **Computer-use** | Desktop mouse/keyboard/apps | Per-app approval; allowlist; sandboxed where possible |
| **Browser-use** | Web nav, forms, dashboards | Action allowlist; session-based approval |
| **Business APIs (MCP)** | Commerce, payments, publishing, CRM | Read-only tokens for reads; scoped write tokens + idempotency; deterministic approval for money/publish |

Platform realities (from research): YouTube ~6 uploads/day default quota,
TikTok 25/day + app approval, X requires paid tier — the agent must respect
platform limits and surface them in the content plan.

## 9. Operating cadence (HEARTBEAT)

- **Continuous**: support checks, inbox triage (guarded)
- **Daily**: metrics snapshot, health check, task execution queue
- **Weekly**: content plan, growth report, feedback synthesis
- **Monthly**: executive summary, financial review, compliance check, market brief
- Costs: cheap model for heartbeat (Qwen3.5-4B/9B local or Flash tier),
  quiet hours for memory consolidation (Dreaming pattern).

## 10. Content engine

1. LLM plans the calendar (weekly themes, hooks, formats)
2. Assets: Qwen-Image 3.0 API (¥0.18/img) or Qwen-Image 2.0 open (7B);
   video: Wan 3.0 API (native 9:16, 30 s, ¥0.30-0.60/s) or Wan 2.2 open weights
3. Assembly: Remotion (deterministic, LLM-driven templates; $0.01/render under
   Automators license)
4. Publish: Postiz self-hosted (28+ channels, official MCP `schedulePostTool`)
   with **draft review gate** before auto-publish (quality gate is mandatory —
   unattended auto-publish risks brand damage)

## 11. Commerce & payments

- Platform: **Saleor** (Python/GraphQL, official read-only MCP); Medusa (TS, MIT) as the alternative if the Node ecosystem is preferred
- Payments: Stripe (official MCP) + Lago only if usage-metered billing is needed
- Agent surface: read-only MCP/keys for reads; separate scoped write token;
  idempotency keys on every mutation; refunds/discounts/pricing → approval queue
- Audit: every financial action writes a hash-chained receipt

## 12. Brain & models

- Primary: Qwen3.7-Plus / Qwen3.8-Max-Preview via Bailian/DashScope
  (OpenAI-compatible), or Qwen3.5 local (4B/9B/35B-A3B) for offline/privacy
- Voice (later): Qwen3.5-Omni-Realtime API (needs GPU for local)
- Fallback: DeepSeek V4 (cheap reasoning, OpenAI-format) — note PRC data
  residency; use for non-sensitive tasks only
- Local inference: llama.cpp/Ollama; hardware-aware model selection

## 13. Security model & mitigations

- **Prompt injection** (Grok/Bankr $150k, Morse-code injection): never let model
  judgment gate money/publishing — deterministic policy + human approval only
- **Excessive agency**: per-tool amount thresholds, deny-by-default background
  tier, fleet spend caps, single-use approvals
- **Malicious skills**: vet every SKILL.md before install (12% of marketplace
  skills reported malicious); pin versions; Skill Scanner pattern
- **Memory poisoning**: write-source provenance, TTL-bounded entries, periodic
  memory audits; treat shared memory as untrusted input
- **Approval UX**: approval cards must show recipient/amount/diff; selective
  gates (money/sends/deletes), not universal friction

## 14. Testing strategy

- Skill unit tests: SKILL.md renders, frontmatter valid, instructions reference
  real tools
- Money-gate tests: falsification test (gate off → no money movement),
  idempotency, expiry, deny paths
- Cadence dry-runs: heartbeat executes Daily/Weekly tasks against fixtures
- MCP contract tests: commerce/payments servers respond per schema
- Shell-agnostic check: skills load in DeepSeek Harness (lab) and OpenClaw
- Content pipeline: fixture assets through plan → draft → approve → publish
  (staging channels)

## 15. Build phases

1. **P0 — Intelligence layer (no shell needed)**: author `skills/`, `memory/`
   skeleton, `policy/` rules, AGENTS.md templates; test in DeepSeek Harness lab
2. **P1 — Install OpenClaw** on Windows; mount skills; wire Qwen brain; verify
   money-gate falsification test
3. **P2 — Content engine**: Qwen-Image/Wan/Remotion/Postiz pipeline with draft gate
4. **P3 — Commerce**: Saleor/Medusa + Stripe MCP; read-only first, gated writes
5. **P4 — Action bodies**: browser-use allowlist, computer-use per-app approval
6. **P5 — Cadence live**: HEARTBEAT daily/weekly/monthly; receipts in production
7. **P6 — L2 policies** per action type as trust grows; re-evaluate QwenPaw

## 16. Out of scope (now)

- Voice interaction (later, via Qwen3-Omni when the shell supports it)
- Mobile companion apps
- Full autonomy (L3)
- QwenPaw as primary shell until October re-evaluation

## 17. Existing assets → conversion

| Asset | Becomes |
|-------|---------|
| `kaizen7-business-agent` (JS/Hermes: capsules, receipts, focus guard) | Source patterns for the business skills (money-gate, cadence, memory) |
| `flowmatik` (video pipeline) | Content-assembly skill (or Remotion replacement) |
| `kaizen7-jarvis` / PersonalJarvis (voice, missions, critic-loop) | Reference for voice + review patterns; skills if useful |
