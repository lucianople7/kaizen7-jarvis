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

The bridge inspects the local Hermes CLI and profile roster. It never starts a
chat, runs a profile, sends messages, schedules cron jobs, or edits credentials.

## Remaining Manual Step

Run profile setup/auth when Luciano is ready:

- `kaizen7 setup`
- `market setup`
- `sales setup`
- `content setup`
- `ops setup`

Human approval is required before connecting providers, messaging platforms,
payment systems, publishing surfaces, or external peers.
