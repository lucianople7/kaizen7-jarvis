# KAIZEN7 Growth OS

Goal: make KAIZEN7 Jarvis more useful as a real business product without adding
heavy dependencies or unsafe execution paths.

Implemented:

- `jarvis.kaizen7.growth_os.GrowthOS`
- one-command growth operating card
- draft-only asset generator
- ecommerce and agent-readable commerce audit
- Growth OS proposal receipts
- FastAPI routes under `/api/kaizen7/growth`
- command registry entries for command, asset, audit and proposal
- doctor and product-readiness coverage

Market patterns absorbed:

- PersonalJarvis product runtime remains the base.
- Hermes/Buzz inspired agent handoff remains adapter/gateway-oriented.
- Postiz informed distribution planning, but no scheduling execution or code was
  copied.
- Shopify storefront/MCP and agentic-commerce patterns informed the
  agent-readable commerce checks.
- LangGraph, Mastra and OpenAI Agents SDK informed workflow/memory/guardrail
  shape without becoming required dependencies.

Safety:

- all Growth OS outputs are `proposal_only`;
- publishing, payments, messages, credentials, financial operations,
  irreversible changes, ad spend and claims require human approval;
- no secrets, tokens or credentials are committed.

Verification:

- focused unit/integration tests cover module behavior, API routes, command
  registry parity, doctor and product readiness.
