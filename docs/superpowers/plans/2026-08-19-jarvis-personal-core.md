# Jarvis Personal Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing custom Jarvis recipe into a guided Personal Core builder that persists a focused, approval-gated assistant mode.

**Architecture:** Keep the change inside the existing Modes surface. Add deterministic builder state and validation in `ModesView.tsx`, reuse the current mode draft editor, and keep `/api/modes` as the only persistence boundary.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, existing `BrandedSelect`, existing `saveMode`.

## Global Constraints

- Every committed artifact is English.
- Do not add new model providers, credentials, backend persistence, mobile packaging, or external publishing in this pass.
- Generated modes must always separate recommendation from execution.
- Generated modes must always require human approval before publishing, payments, messages, credentials, financial operations, external sends, destructive changes, or irreversible actions.
- Priority cap defaults to 3 and must reject values below 1 or above 5.
- Stage only touched files and do not push unless explicitly requested.

---

### Task 1: Personal Core Validation Tests

**Files:**
- Modify: `jarvis/ui/web/frontend/src/views/ModesView.test.tsx`

**Interfaces:**
- Consumes: Existing `ModesView` render and mocked `/api/modes`.
- Produces: Failing expectations for required mission, focus, priority cap, approval text, and save behavior.

- [ ] **Step 1: Write failing tests**

Add tests that verify:

```tsx
it("blocks personal core generation without mission and focus", async () => {
  render(<ModesView />);
  await screen.findByText("Jarvis");
  fireEvent.click(screen.getByRole("button", { name: /Build personal Jarvis/i }));
  expect(pushToast).toHaveBeenCalledWith(
    "warning",
    "Jarvis needs a mission and active focus before it can become operational.",
  );
  expect((screen.getByLabelText("Mode name") as HTMLInputElement).value).toBe("");
});

it("rejects personal core priority caps outside one to five", async () => {
  render(<ModesView />);
  await screen.findByText("Jarvis");
  fireEvent.change(screen.getByLabelText("Assistant mission"), {
    target: { value: "Keep Luciano focused on the highest leverage move" },
  });
  fireEvent.change(screen.getByLabelText("Active focus"), {
    target: { value: "Ship the personal Jarvis product" },
  });
  fireEvent.change(screen.getByLabelText("Max active priorities"), {
    target: { value: "8" },
  });
  fireEvent.click(screen.getByRole("button", { name: /Build personal Jarvis/i }));
  expect(pushToast).toHaveBeenCalledWith(
    "warning",
    "Jarvis keeps one to five active priorities. Set a tighter cap.",
  );
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm.cmd test -- src/views/ModesView.test.tsx`

Expected: FAIL because labels and validation do not exist yet.

---

### Task 2: Personal Core Builder Implementation

**Files:**
- Modify: `jarvis/ui/web/frontend/src/views/ModesView.tsx`

**Interfaces:**
- Consumes: Existing `draft`, `setDraft`, `draftNameRef`, `pushToast`, `BrandedSelect`.
- Produces: `buildPersonalJarvisDraft(core)` and `buildPersonalCore()`.

- [ ] **Step 1: Implement minimal code**

Add these concepts in `ModesView.tsx`:

```ts
type JarvisTone = "executive" | "warm" | "direct" | "strict";

type PersonalCore = {
  mission: string;
  owner: string;
  focus: string;
  tone: JarvisTone;
  energy: JarvisEnergy;
  guardrails: string;
  priorityLimit: number;
};
```

Replace the current recipe builder with fields labelled:

```text
Assistant mission
Owner
Active focus
Approval boundaries
Max active priorities
Jarvis tone
Jarvis energy
```

Generate `character` containing:

```text
Owner: Luciano
Active focus: Ship the personal Jarvis product
Priority cap: keep at most 3 active priorities visible.
Always separate recommendation from execution.
Human approval is required before publishing, payments, messages, credentials, financial operations, external sends, destructive changes, or irreversible actions.
```

- [ ] **Step 2: Run focused test**

Run: `npm.cmd test -- src/views/ModesView.test.tsx`

Expected: PASS.

---

### Task 3: Verification And Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-08-19-jarvis-personal-core.md`
- Modify: `jarvis/ui/web/frontend/src/views/ModesView.tsx`
- Modify: `jarvis/ui/web/frontend/src/views/ModesView.test.tsx`

**Interfaces:**
- Consumes: Green focused tests.
- Produces: Verified local commit.

- [ ] **Step 1: Run full related verification**

Run:

```powershell
npm.cmd test -- src/views/ModesView.test.tsx src/components/ui/no-native-selects.test.ts src/components/ui/select.test.tsx
npx.cmd tsc -b
npm.cmd run build
npm.cmd audit --audit-level=high
```

- [ ] **Step 2: Run smoke test**

Run Vite on `127.0.0.1:5173` and confirm `/` returns HTTP 200.

- [ ] **Step 3: Commit**

Run:

```powershell
git add -- docs/superpowers/plans/2026-08-19-jarvis-personal-core.md jarvis/ui/web/frontend/src/views/ModesView.tsx jarvis/ui/web/frontend/src/views/ModesView.test.tsx
git commit -m "feat: add Jarvis personal core builder"
```
