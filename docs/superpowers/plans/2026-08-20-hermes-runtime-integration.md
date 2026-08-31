# Hermes Runtime Integration

## What Is Installed

Hermes Agent is installed locally at:

`C:\Users\lucia\AppData\Local\hermes\hermes-agent`

Verified CLI:

`Hermes Agent v0.20.4 (2026.8.18)`

## Local Profile Fleet

Created Hermes profiles:

- `kaizen7`: central operating brain.
- `market`: market intelligence.
- `sales`: offer and revenue.
- `content`: content creation.
- `ops`: execution, planning, receipts, and review.

Each profile has a customized `SOUL.md`. No credentials were written by this
work. Profiles currently need `setup`/auth before they can run paid or
authenticated providers.

## Product Contract

KAIZEN7 is the brain and coordination layer. Hermes is the runtime surface:
profiles, profile chat, cron routines, peers, and desktop Bot Mode.

Implemented read-only bridge:

- `/api/kaizen7/hermes/status`
- `/api/kaizen7/hermes/profiles`
- `/api/kaizen7/hermes/capabilities`
- `/api/kaizen7/hermes/cron`
- `/api/kaizen7/hermes/peers`
- `/api/kaizen7/hermes/chat/propose`

The bridge inspects the local Hermes CLI, profile roster, cron surface, peer
surface, and profile-chat command shape. Chat handoff is proposal-only at this
layer: it records the exact safe command pattern and message intent without
starting a profile, sending messages, scheduling jobs, editing peers, or
touching credentials.

## Remaining Manual Step

Run profile setup/auth when Luciano is ready:

- `kaizen7 setup`
- `market setup`
- `sales setup`
- `content setup`
- `ops setup`

Human approval is required before connecting providers, messaging platforms,
payment systems, publishing surfaces, or external peers.
