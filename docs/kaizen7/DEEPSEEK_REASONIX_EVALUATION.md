# DeepSeek Harness And Reasonix Evaluation

Date: 2026-08-15
Purpose: identify whether new DeepSeek ecosystem tooling should influence the
KAIZEN7 private Jarvis direction.

## Evidence Discipline

This note must not treat conversational search summaries as verified facts.
Claims about launch dates, star counts, community size, official status,
supported tools, pricing, authentication, or enterprise readiness are unstable
and must be checked against primary sources before they drive implementation.

The useful signal from the conversation is the target shape Luciano wants:

- a personal and business Jarvis that actually performs tasks;
- desktop control, web UI, CLI, voice, plugins, MCP, and community extensions;
- e-commerce and content workflows;
- long-term memory, approvals, receipts, and rollback/checkpoints;
- modular providers instead of being locked into one model vendor.

Do not internalize claims such as "just launched", exact GitHub popularity, or
"official DeepSeek Work" unless they are verified from the project owner,
release notes, documentation, or repository metadata at execution time.

## Source Findings

### `deepseek-harness`

Primary source: https://github.com/deepseek-ai/deepseek-harness

Verified from the official repository and README on 2026-08-16:

- Official public repository under `deepseek-ai/deepseek-harness`.
- The README describes DeepSeek Harness (`dsh`) as an open-source agent harness
  developed by DeepSeek AI.
- License: MIT.
- Status: developer preview with rapid iteration and expected compatibility
  breaks.
- Architecture: "everything is a plugin", powered by Cordis.
- Runtime entry: `npx @deepseek-ai/dsh web`.
- Default Web UI: `http://127.0.0.1:3080`.
- Source run path: clone, `pnpm install`, `pnpm run build`, `pnpm dsh web`.
- Plugin discovery signal: repositories can use the `dsh-plugin` topic.
- Community/support surfaces: GitHub Discussions and DeepSeek Harness Discord.
- The repository has large public traction in the visible GitHub metadata.

Architecture notes from `docs/architecture.md`:

- Cordis plugins contribute services, typed events, and reversible effects to a
  shared context.
- Model adapters, tool registry, session log, and agent loop are all replaceable
  from configuration.
- Profiles compose ordered plugin bundles at boot; `web` and `headless` ship as
  templates.
- `dsh-base` contributes model adapters, tools, persistence, sandbox, approval
  policy, settings, credentials, and telemetry.
- Tool execution has `tools/pre-execute`, `tools/execute`, and
  `tools/post-execute` events.
- New behavior should attach to documented extension points rather than patching
  the loop directly.

Correction: an earlier note incorrectly treated another `deepseek-harness`
repository as the main source. The official source for KAIZEN7 evaluation is now
`deepseek-ai/deepseek-harness`.

Potential KAIZEN7 use:

- Treat it as a serious peer runtime to inspect, not merely a DeepSeek API
  adapter.
- Run a read-only local smoke test first with `npx @deepseek-ai/dsh web`, no
  API keys committed and no paid calls.
- Study whether its Cordis plugin/event model can inspire a KAIZEN7 plugin
  bridge for Jarvis.
- If adopted, pin the npm package version or repository commit before executing
  real tasks.
- Keep all credentials in environment or OS credential storage, never Git.

### `DeepSeek-Reasonix`

Primary source: https://github.com/esengine/DeepSeek-Reasonix

Observed from the project README:

- MIT-licensed public repository.
- Single Go binary, open source.
- Four entry surfaces: terminal/TUI, desktop app, browser, and editor integration
  over ACP.
- Config-driven provider, agent, tool, and plugin declarations in `reasonix.toml`.
- DeepSeek is a preset, while OpenAI-compatible endpoints can be configured
  without new code.
- Plugin-driven via MCP servers and an Extension Protocol v1 with sidecars,
  runtime event interception, provider contribution, structured UI, and versioned
  plugin packages.
- Includes workspace sandbox, permissions, per-turn checkpoints, and rewind.
- Community signal in the README is materially larger than `deepseek-harness`:
  thousands of forks, many issues and pull requests, and Discord community link.

Potential KAIZEN7 use:

- Treat Reasonix as a peer runtime to study, not as code to copy into Jarvis yet.
- Mine the architecture for KAIZEN7 ideas: config-first providers, plugin package
  manifest, sidecar event protocol, checkpoints/rewind, desktop/ACP surfaces.
- If integrating, prefer one of these low-risk routes:
  1. Register Reasonix as an external CLI tool through Jarvis's CLI catalog.
  2. Run Reasonix MCP-compatible tools through Jarvis MCP loader.
  3. Build a KAIZEN7 bridge that can dispatch selected tasks to Reasonix only
     after approval and log receipts back into Jarvis memory.

## Recommendation

Do not replace Jarvis with either project now.

Use Jarvis as the local voice/desktop/private operating shell, because it already
has risk tiers, secret handling, mission workers, MCP, marketplace loaders, web UI,
and local voice. Study Reasonix for the plugin/desktop/checkpoint model. Use
`deepseek-harness` only when DeepSeek API compatibility becomes a concrete provider
need.

The best KAIZEN7 move is a thin adapter layer:

```text
Luciano decides.
KAIZEN7 focuses.
Jarvis coordinates local voice, memory, approvals, and desktop state.
Codex / Claude / Reasonix / DeepSeek tools execute only through gated adapters.
Receipts return to KAIZEN7 memory.
```

## Integration Guardrails

- No API keys in Git.
- No paid API calls without explicit approval.
- No automatic desktop control through a new runtime until the tool is classified
  by risk tier and gated through the approval path.
- Pin every external runtime by release or commit before execution.
- Start with read-only diagnostics, then one reversible task, then expand.
