import type { ReactNode } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BusinessView } from "./BusinessView";

vi.mock("@/views/ChatsView", () => ({
  ViewHeader: ({
    title,
    subtitle,
    right,
  }: {
    title: string;
    subtitle?: string;
    right?: ReactNode;
  }) => (
    <header>
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
      {right}
    </header>
  ),
}));

describe("BusinessView", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders a local business workspace with approval boundaries", () => {
    render(<BusinessView />);

    expect(screen.getByText("Business OS")).toBeTruthy();
    expect(screen.getByText("Active mission")).toBeTruthy();
    expect(screen.getByText("Mobile access")).toBeTruthy();
    expect(screen.getByText("Installable PWA")).toBeTruthy();
    expect(screen.getByText("Offline shell")).toBeTruthy();
    expect(screen.getByText("Priority filter")).toBeTruthy();
    expect(screen.getAllByText("Human approval").length).toBeGreaterThan(0);
    expect(screen.getByText("Publishing")).toBeTruthy();
    expect(screen.getByText("Financial operation")).toBeTruthy();
    expect(screen.getByText("Next")).toBeTruthy();
    expect(screen.getAllByText("Capture one verified signal").length).toBeGreaterThan(0);
  });

  it("limits active priorities and parks the rest", () => {
    render(<BusinessView />);

    expect(screen.getByText("Max 3 active")).toBeTruthy();
    expect(screen.getByText("Active now")).toBeTruthy();
    expect(screen.queryByText("Parked")).toBeNull();

    const priorityInput = screen.getByLabelText("New priorities");
    fireEvent.change(priorityInput, { target: { value: "Fourth priority" } });
    fireEvent.keyDown(priorityInput, { key: "Enter" });

    expect(screen.getByText("Parked")).toBeTruthy();
    expect(screen.getAllByText("Fourth priority").length).toBeGreaterThan(0);
  });

  it("persists decision receipts locally", async () => {
    render(<BusinessView />);

    fireEvent.change(screen.getByLabelText("Decision"), {
      target: { value: "Ship mobile onboarding" },
    });
    fireEvent.change(screen.getByLabelText("Evidence"), {
      target: { value: "Android install path is needed" },
    });
    fireEvent.change(screen.getByLabelText("Result"), {
      target: { value: "Added to weekly focus" },
    });
    fireEvent.change(screen.getByLabelText("Decision risk"), {
      target: { value: "approval" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Add receipt/i }));

    act(() => {
      vi.advanceTimersByTime(300);
    });

    const raw = window.localStorage.getItem("jarvis.business.workspace.v1");
    expect(raw).toContain("Ship mobile onboarding");
    expect(raw).toContain("approval");
  });

  it("turns a daily action into a completed receipt with evidence", () => {
    render(<BusinessView />);

    expect(screen.getByText("Daily execution")).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", { name: /Complete Capture one verified signal/i }),
    );
    fireEvent.change(screen.getByLabelText("Action evidence seed-signal"), {
      target: { value: "Saved a real comment thread from today" },
    });
    fireEvent.change(screen.getByLabelText("Action result seed-signal"), {
      target: { value: "Signal is ready for a dossier" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Save receipt Capture one verified signal/i }),
    );

    expect(screen.getByText("Completed action: Capture one verified signal")).toBeTruthy();
    expect(screen.getByText("Evidence: Saved a real comment thread from today")).toBeTruthy();
  });

  it("does not complete a low-risk action without evidence", () => {
    render(<BusinessView />);

    fireEvent.click(
      screen.getByRole("button", { name: /Complete Capture one verified signal/i }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /Save receipt Capture one verified signal/i }),
    );

    expect(screen.queryByText("Completed action: Capture one verified signal")).toBeNull();
    expect(
      screen.getByRole("button", { name: /Save receipt Capture one verified signal/i }),
    ).toBeTruthy();
  });

  it("undoes the last completed action", () => {
    render(<BusinessView />);

    fireEvent.click(
      screen.getByRole("button", { name: /Complete Capture one verified signal/i }),
    );
    fireEvent.change(screen.getByLabelText("Action evidence seed-signal"), {
      target: { value: "Note from a buyer comment" },
    });
    fireEvent.change(screen.getByLabelText("Action result seed-signal"), {
      target: { value: "Queued for dossier" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Save receipt Capture one verified signal/i }),
    );

    expect(screen.getByText("Completed action: Capture one verified signal")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Undo last complete/i }));
    expect(screen.queryByText("Completed action: Capture one verified signal")).toBeNull();
    expect(
      screen.getByRole("button", { name: /Complete Capture one verified signal/i }),
    ).toBeTruthy();
  });

  it("keeps guarded actions recommendation-only until human approval", () => {
    render(<BusinessView />);

    fireEvent.change(screen.getByLabelText("New action"), {
      target: { value: "Publish launch offer" },
    });
    fireEvent.change(screen.getByLabelText("Action risk"), {
      target: { value: "approval" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Add action/i }));

    expect(screen.getByText("Publish launch offer")).toBeTruthy();
    expect(screen.getAllByText("Approval required").length).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /Complete Publish launch offer/i }),
    ).toBeNull();
    expect(
      screen.getByRole("button", { name: /Copy for approval Publish launch offer/i }),
    ).toBeTruthy();
  });

  it("copies an operational briefing for use outside the app", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<BusinessView />);

    fireEvent.click(screen.getByRole("button", { name: /Copy briefing/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(writeText).toHaveBeenCalledOnce();
    expect(writeText.mock.calls[0][0]).toContain("Business OS Briefing");
    expect(writeText.mock.calls[0][0]).toContain("Active priorities");
    expect(screen.getByText("Copied")).toBeTruthy();
  });

  it("shows a daily business review with progress and approval queue", () => {
    render(<BusinessView />);

    expect(screen.getByText("Daily review")).toBeTruthy();
    expect(screen.getByText("0/5 completed")).toBeTruthy();
    expect(screen.getByText("1 approval waiting")).toBeTruthy();
    expect(screen.getByText("Next action")).toBeTruthy();
    expect(screen.getAllByText("Capture one verified signal").length).toBeGreaterThan(0);
  });

  it("copies a daily review digest with next action and priorities", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<BusinessView />);

    fireEvent.click(screen.getByRole("button", { name: /Copy daily review/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(writeText).toHaveBeenCalledOnce();
    expect(writeText.mock.calls[0][0]).toContain("Daily Review");
    expect(writeText.mock.calls[0][0]).toContain("Progress: 0/5 completed");
    expect(writeText.mock.calls[0][0]).toContain(
      "Next action: Capture one verified signal",
    );
    expect(writeText.mock.calls[0][0]).toContain("Approvals waiting: 1");
    expect(writeText.mock.calls[0][0]).toContain("Active priorities");
  });

  it("saves the daily review as a decision receipt", () => {
    render(<BusinessView />);

    fireEvent.click(screen.getByRole("button", { name: /Save daily review/i }));

    expect(screen.getByText("Daily review: 0/5 completed")).toBeTruthy();
    expect(screen.getByText("Evidence: Open actions: 5. Approvals waiting: 1.")).toBeTruthy();
    expect(
      screen.getByText("Result: Next action: Capture one verified signal."),
    ).toBeTruthy();
  });

  it("shows an error when the clipboard is unavailable", async () => {
    Object.assign(navigator, { clipboard: undefined });
    render(<BusinessView />);

    fireEvent.click(screen.getByRole("button", { name: /Copy briefing/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByText("Clipboard unavailable")).toBeTruthy();
  });

  it("copies mobile access instructions with the current URL", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<BusinessView />);

    fireEvent.click(screen.getByRole("button", { name: /Copy mobile setup/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(writeText).toHaveBeenCalledOnce();
    expect(writeText.mock.calls[0][0]).toContain("Mobile Access");
    expect(writeText.mock.calls[0][0]).toContain(window.location.origin);
    expect(writeText.mock.calls[0][0]).toContain("Android");
  });

  it("shows a debug kit with local runtime diagnostics", () => {
    render(<BusinessView />);

    expect(screen.getByText("Debug kit")).toBeTruthy();
    expect(screen.getByText("Storage writable")).toBeTruthy();
    expect(screen.getByText("Workspace payload")).toBeTruthy();
    expect(screen.getByText("Service worker")).toBeTruthy();
    expect(screen.getByText("Cache API")).toBeTruthy();
  });

  it("copies a debug report for support and troubleshooting", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<BusinessView />);

    fireEvent.click(screen.getByRole("button", { name: /Copy debug report/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(writeText).toHaveBeenCalledOnce();
    expect(writeText.mock.calls[0][0]).toContain("Business OS Debug Report");
    expect(writeText.mock.calls[0][0]).toContain("Storage writable: yes");
    expect(writeText.mock.calls[0][0]).toContain("Service worker support:");
    expect(writeText.mock.calls[0][0]).toContain("Workspace payload bytes:");
  });

  it("copies a portable workspace backup as JSON", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<BusinessView />);

    fireEvent.click(screen.getByRole("button", { name: /Copy backup/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(writeText).toHaveBeenCalledOnce();
    const backup = JSON.parse(writeText.mock.calls[0][0]);
    expect(backup.schema).toBe("jarvis.business.workspace");
    expect(backup.version).toBe(1);
    expect(backup.workspace.mission).toContain("THE FOCUX");
    expect(backup.workspace.actions.length).toBeGreaterThan(0);
  });

  it("restores a portable workspace backup from JSON", () => {
    render(<BusinessView />);

    const backup = {
      schema: "jarvis.business.workspace",
      version: 1,
      workspace: {
        mission: "Run one mobile-first Jarvis operating loop.",
        offer: "A personal operating system for daily execution.",
        audience: "Luciano and future operators.",
        northStar: "Daily usable progress.",
        weeklyObjective: "Finish one usable mobile access path.",
        priorities: ["Mobile access", "Voice control", "Receipts"],
        metrics: ["Sessions", "Completed actions"],
        actions: [
          {
            id: "mobile-test",
            title: "Open Jarvis from Android on local network",
            risk: "low",
            done: false,
          },
        ],
        decisions: [
          {
            id: "mobile-route",
            title: "Use local network first",
            evidence: "No publishing or cloud cost needed.",
            result: "Android can validate the product loop safely.",
            risk: "low",
            createdAt: "2026-08-17T09:00:00.000Z",
          },
        ],
        lastComplete: null,
      },
    };

    fireEvent.change(screen.getByLabelText("Workspace backup JSON"), {
      target: { value: JSON.stringify(backup) },
    });
    fireEvent.click(screen.getByRole("button", { name: /Restore backup/i }));

    expect(screen.getByText("Run one mobile-first Jarvis operating loop.")).toBeTruthy();
    expect(
      screen.getAllByText("Open Jarvis from Android on local network").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("Use local network first")).toBeTruthy();
  });

  it("rejects invalid workspace backup JSON without replacing current work", () => {
    render(<BusinessView />);

    fireEvent.change(screen.getByLabelText("Workspace backup JSON"), {
      target: { value: "{\"schema\":\"wrong\"}" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Restore backup/i }));

    expect(screen.getByText("Invalid backup")).toBeTruthy();
    expect(screen.getAllByText("Capture one verified signal").length).toBeGreaterThan(0);
  });
});
