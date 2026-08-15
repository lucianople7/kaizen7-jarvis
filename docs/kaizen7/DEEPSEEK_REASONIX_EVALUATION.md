# DeepSeek Harness And Reasonix Evaluation

Date: 2026-08-15
Purpose: identify whether new DeepSeek ecosystem tooling should influence the
KAIZEN7 private Jarvis direction.

## Source Findings

### `deepseek-harness`

Primary source: https://github.com/HenryZ838978/deepseek-harness

Observed from the project README:

- MIT-licensed public repository.
- Published forms: Python library `deepseek-harness`, CLI `deepseek-harness-cli`, MCP server `@deepseek-harness/mcp`, and a SKILL.md package.
- Purpose: protocol-aware adapters for DeepSeek V4-Pro and V4-Flash.
- It codifies DeepSeek-specific protocol rules: preserving `reasoning_content`,
  handling parallel tool-call streaming by index, setting `max_tokens`, avoiding
  `/beta` for tool calls, validating the 1,048,576-token ceiling, and keeping a
  cache-stable prefix.
- It is not primarily a desktop agent platform. It is a compatibility harness
  for safer DeepSeek API usage.

Potential KAIZEN7 use:

- Add as an optional adapter only if we select DeepSeek V4 as a provider path.
- Prefer MCP form first for isolation: `npx -y @deepseek-harness/mcp` with
  `DEEPSEEK_API_KEY` supplied by environment or credential store, never Git.
- Use its validation tools without API spend where possible.

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
