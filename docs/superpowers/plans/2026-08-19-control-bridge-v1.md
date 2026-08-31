# Control Bridge v1

## Goal

Add a local, recommendation-only control bridge that lets Jarvis expose safe
status, capabilities, proposals, and activity receipts before any future
execution path exists.

## Boundaries

- No credentials, tokens, payments, messages, publishing, financial operations,
  destructive actions, or irreversible changes.
- Proposals are recorded as receipts; they do not execute tools.
- Any future execution endpoint must be separate from recommendation endpoints
  and require human approval.
- Receipts persist in the existing user data area, not in the Git repository.

## Acceptance Tests

- `/api/kaizen7/bridge/status` reports recommendation-only mode and disabled
  execution.
- `/api/kaizen7/bridge/capabilities` lists only safe bridge capabilities.
- `/api/kaizen7/bridge/propose` stores a durable receipt without executing.
- `/api/kaizen7/bridge/receipts` reads recent receipts.
- Command registry exposes the bridge endpoints and parity tests pass.
