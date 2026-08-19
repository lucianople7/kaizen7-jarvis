# Jarvis Personal Core Design

## Goal

Make the first real customization path feel like setting up a personal operating
assistant, not filling a generic persona form. A new user should be able to
define what their assistant is for, how direct it should be, what it must never
do without approval, and which few priorities it should keep visible.

The outcome is a persistent assistant mode that can be reviewed, edited, saved,
and used by the existing chat and voice flows.

## Product Shape

Add a guided "Personal Core" builder to the existing Modes surface. It should
sit above or replace the current custom Jarvis recipe panel, keeping the manual
mode editor available as the final review step.

The builder asks for:

- assistant mission;
- owner name or preferred reference;
- active life/business focus;
- tone: executive, warm, direct, or strict;
- energy: calm, focused, or high focus;
- hard approval boundaries;
- maximum active priorities.

The generated mode remains editable before saving. Saving continues to use the
existing `/api/modes` endpoint, so the feature does not introduce a new runtime,
new credentials, or a parallel persistence path.

## User Flow

1. The user opens Modes.
2. The Personal Core panel shows a small guided form.
3. The user fills mission, focus, tone, energy, boundaries, and priority limit.
4. The user clicks "Build personal Jarvis".
5. The mode draft is generated in the existing editor.
6. Focus moves to the draft name field and a toast explains the next step.
7. The user reviews and saves.
8. The saved mode appears in the mode shelf and can be activated normally.

## Architecture

Keep the first implementation frontend-only and deterministic.

- `ModesView.tsx` owns the builder state and draft generation.
- Existing `saveMode` remains the only persistence boundary.
- Existing `BrandedSelect` is used for all option sets.
- Generated text is produced by a pure helper so it can be tested without a
  backend.
- No secrets, keys, cookies, payments, publishing, or irreversible actions are
  touched.

This fits the current mode architecture because modes already define persistent
assistant behavior with `name`, `description`, `character`, `verbosity`, and
`proactivity`.

## Data Contract

The builder maps to the existing mode draft:

- `name`: generated from tone and role, for example `Jarvis Personal Operator`;
- `emoji`: short ASCII marker, for example `K7`;
- `description`: concise summary of the selected operating style;
- `character`: structured instructions containing mission, owner, focus,
  approval boundaries, priority cap, recommendation/execution separation, and
  next-action discipline;
- `verbosity`: derived from energy;
- `proactivity`: derived from energy.

The priority cap is explicit in the prompt text. The default is three active
priorities. A value below one or above five should be rejected by the UI.

## Safety And Guardrails

The generated mode must always include:

- one active mission or focus at a time;
- limited active priorities;
- recommendation separated from execution;
- human approval before publishing, payments, messages, credentials, financial
  operations, external sends, destructive changes, or irreversible actions;
- no claim that the assistant can spend money, publish content, or contact
  people unless a separate approved execution path exists.

The feature is customization only. It does not grant new capabilities.

## Error Handling

If required fields are empty, the builder should not generate a draft. It should
show a warning toast and keep focus inside the builder.

If the backend fails while saving, the existing `saveMode` error path remains in
place and the draft stays editable.

If the mode catalog fails to load, the builder and manual editor should still be
usable where possible, matching the current graceful behavior.

## Testing

Add or extend focused tests for:

- required builder fields block draft generation;
- a complete Personal Core input generates the expected draft content;
- priority cap appears in `character`;
- approval boundaries are always present;
- focus moves to the draft name field after generation;
- saving still POSTs to `/api/modes`.

Run the existing related tests:

- `npm.cmd test -- src/views/ModesView.test.tsx src/components/ui/no-native-selects.test.ts src/components/ui/select.test.tsx`
- `npx.cmd tsc -b`
- `npm.cmd run build`
- `npm.cmd audit --audit-level=high`

Finish with an HTTP smoke test against the local Vite app.

## Out Of Scope

This pass does not add:

- model-provider changes;
- new backend persistence;
- mobile app packaging;
- voice interview changes;
- tool execution permissions;
- external publishing or account actions;
- GitHub push unless explicitly requested.

## Acceptance Criteria

- A user can build a personal Jarvis mode from a guided form.
- The generated mode is editable and saved through the existing mode API.
- Approval boundaries are present in every generated mode.
- Priority limit and active focus are explicit.
- Tests, TypeScript, production build, audit, and smoke test pass.
- The implementation changes only the Modes surface and its focused tests.
