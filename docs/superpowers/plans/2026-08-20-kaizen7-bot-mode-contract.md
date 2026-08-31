# KAIZEN7 Bot Mode Contract

## Source Pattern

Hermes Bot Mode treats a bot as a profile: one durable specialist with its own
identity, memory, skills, routines, and chat history. The useful product lesson
is to build a roster over an existing primitive instead of inventing another
runtime.

## First Slice

This repository does not have Hermes profiles as a native primitive. It already
has assistant modes, so KAIZEN7 exposes a read-only Bot roster over modes:

- each mode appears as a bot row;
- each bot has a stable `@handle`;
- each bot reports its backing primitive as `mode`;
- routine/chat/group fields are explicit future capability markers;
- creation is proposal-only and writes a receipt through the Control Bridge.

## Safety Boundary

The current slice does not create profiles, run agents, send messages, schedule
jobs, publish content, spend money, touch credentials, or perform irreversible
actions. Creation remains a proposal until a separate approved execution path
exists.

## Acceptance Tests

- `/api/kaizen7/bots` lists modes as bots.
- `/api/kaizen7/bots/propose` records a bot creation proposal.
- Proposals do not create modes.
- Command registry parity remains green.
