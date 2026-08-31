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
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
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

  it("persists decision receipts locally", () => {
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
    fireEvent.click(screen.getByLabelText("Decision risk"));
    fireEvent.click(screen.getByRole("option", { name: "Needs human approval" }));
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
    fireEvent.click(screen.getByLabelText("Action risk"));
    fireEvent.click(screen.getByRole("option", { name: "Needs approval" }));
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

  it("shows a clean start-to-finish operating flow", () => {
    render(<BusinessView />);

    expect(screen.getByText("Start-to-finish flow")).toBeTruthy();
    expect(screen.getByText("Focus")).toBeTruthy();
    expect(screen.getByText("Do")).toBeTruthy();
    expect(screen.getByText("Review")).toBeTruthy();
    expect(screen.getByText("Receipt")).toBeTruthy();
    expect(
      screen.getAllByText("Capture one verified signal and turn it into a dossier or piece.")
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Capture one verified signal").length).toBeGreaterThan(0);
    expect(screen.getByText("0 of 5 completed")).toBeTruthy();
    expect(screen.getAllByText("2 receipts").length).toBeGreaterThan(0);
  });

  it("tracks real business metrics against numeric targets", () => {
    render(<BusinessView />);

    expect(screen.getByText("Business cockpit")).toBeTruthy();
    expect(screen.getByText("Lead velocity")).toBeTruthy();
    expect(screen.getByText("0 / 25")).toBeTruthy();
    expect(screen.getByText("25 remaining")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Current Lead velocity"), {
      target: { value: "7" },
    });

    expect(screen.getByText("7 / 25")).toBeTruthy();
    expect(screen.getByText("18 remaining")).toBeTruthy();

    act(() => {
      vi.advanceTimersByTime(300);
    });

    const raw = window.localStorage.getItem("jarvis.business.workspace.v1");
    expect(raw).toContain("\"current\":7");
    expect(raw).toContain("\"target\":25");
  });

  it("copies a cockpit report with targets, gaps and next action", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<BusinessView />);

    fireEvent.change(screen.getByLabelText("Current Lead velocity"), {
      target: { value: "7" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Copy cockpit report/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(writeText).toHaveBeenCalledOnce();
    expect(writeText.mock.calls[0][0]).toContain("Business Cockpit Report");
    expect(writeText.mock.calls[0][0]).toContain("Lead velocity: 7/25 leads, 18 remaining");
    expect(writeText.mock.calls[0][0]).toContain("Next action: Capture one verified signal");
    expect(writeText.mock.calls[0][0]).toContain("Approval queue: 1");
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
    expect(screen.getByText("10-point readiness")).toBeTruthy();
    expect(screen.getByText("10 checks")).toBeTruthy();
    expect(screen.getByText("Storage writable")).toBeTruthy();
    expect(screen.getByText("Workspace payload")).toBeTruthy();
    expect(screen.getByText("Service worker")).toBeTruthy();
    expect(screen.getByText("Cache API")).toBeTruthy();
    expect(screen.getByText("Mission defined")).toBeTruthy();
    expect(screen.getByText("Active priorities limited")).toBeTruthy();
    expect(screen.getByText("Metrics defined")).toBeTruthy();
    expect(screen.getByText("Open action available")).toBeTruthy();
    expect(screen.getByText("Approval gate present")).toBeTruthy();
    expect(screen.getByText("Receipts available")).toBeTruthy();
  });

  it("shows the Hermes runtime cockpit with profiles and safe capabilities", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/kaizen7/hermes/status") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                installed: true,
                version: "Hermes Agent v0.20.4",
                profile_count: 5,
                error: "",
              }),
          });
        }
        if (url === "/api/kaizen7/hermes/profiles") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                installed: true,
                count: 5,
                profiles: [
                  { name: "kaizen7", model: "kimi-k2-0905-preview", gateway: "moonshot" },
                  { name: "market", model: "kimi-k2-0905-preview", gateway: "moonshot" },
                  { name: "sales", model: "kimi-k2-0905-preview", gateway: "moonshot" },
                ],
              }),
          });
        }
        if (url === "/api/kaizen7/hermes/capabilities") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                execution_enabled: false,
                approval_required_for: ["payments", "publishing"],
                capabilities: [
                  {
                    id: "profile-chat",
                    title: "Profile chat",
                    command: "hermes profile chat",
                    requires_approval: true,
                  },
                  {
                    id: "cron-list",
                    title: "Cron list",
                    command: "hermes cron list",
                    requires_approval: false,
                  },
                ],
              }),
          });
        }
        if (url === "/api/kaizen7/hermes/bot-mode") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                name: "Personal Jarvis + Hermes Bot",
                execution_enabled: false,
                personal_jarvis: { role: "local_interface" },
                hermes: { role: "agent_runtime" },
                bot_mode: { role: "persistent_specialist_bots" },
                recommended_bots: [
                  { profile: "kaizen7", title: "Mission control", installed: true },
                  { profile: "market", title: "Market scout", installed: true },
                ],
                human_approval_required_for: ["payments", "publishing"],
              }),
          });
        }
        if (url === "/api/kaizen7/codex/status") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                installed: true,
                version: "codex-cli 0.146.0",
                execution_enabled: false,
                requires_git_repo: true,
                requires_pty: true,
                error: "",
              }),
          });
        }
        return Promise.reject(new Error(`unexpected url ${url}`));
      }),
    );

    render(<BusinessView />);

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByText("Hermes runtime")).toBeTruthy();
    expect(screen.getByText("Hermes Agent v0.20.4")).toBeTruthy();
    expect(screen.getByText("3 profiles")).toBeTruthy();
    expect(screen.getAllByText("kaizen7").length).toBeGreaterThan(0);
    expect(screen.getAllByText("market").length).toBeGreaterThan(0);
    expect(screen.getByText("sales")).toBeTruthy();
    expect(screen.getByText("Profile chat")).toBeTruthy();
    expect(screen.getByText("Cron list")).toBeTruthy();
    expect(screen.getByText("Proposal only")).toBeTruthy();
    expect(screen.getByText("Codex CLI")).toBeTruthy();
    expect(screen.getByText("codex-cli 0.146.0")).toBeTruthy();
    expect(screen.getByText("PTY + Git repo")).toBeTruthy();
    expect(screen.getByText("Personal Jarvis + Hermes Bot")).toBeTruthy();
    expect(screen.getByText("Local interface")).toBeTruthy();
    expect(screen.getByText("Persistent bot runtime")).toBeTruthy();
    expect(screen.getAllByText("Human approval").length).toBeGreaterThan(0);
  });

  it("lets a user prepare a simple Jarvis handoff for Hermes, Codex, Buzz or Work Assistant", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/kaizen7/hermes/status") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                installed: true,
                version: "Hermes Agent v0.20.4",
                profile_count: 1,
                error: "",
              }),
          });
        }
        if (url === "/api/kaizen7/hermes/profiles") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                installed: true,
                count: 1,
                profiles: [{ name: "kaizen7", model: "kimi-k2", gateway: "moonshot" }],
              }),
          });
        }
        if (url === "/api/kaizen7/hermes/capabilities") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                execution_enabled: false,
                approval_required_for: [],
                capabilities: [],
              }),
          });
        }
        return Promise.reject(new Error(`unexpected url ${url}`));
      }),
    );

    render(<BusinessView />);

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByText("Jarvis command center")).toBeTruthy();
    expect(screen.getByText("Hermes")).toBeTruthy();
    expect(screen.getByText("Codex")).toBeTruthy();
    expect(screen.getByText("Buzz")).toBeTruthy();
    expect(screen.getByText("Work Assistant")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("What should Jarvis help with?"), {
      target: { value: "Debug the install and make the product easier to use." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Use Codex/i }));
    fireEvent.click(screen.getByRole("button", { name: /Prepare safe handoff/i }));

    expect(screen.getByText("Selected: Codex")).toBeTruthy();
    expect(
      (screen.getByLabelText("Hermes handoff message") as HTMLTextAreaElement).value,
    ).toBe(
      "Route: Codex. Build, debug and verify code changes. Request: Debug the install and make the product easier to use.",
    );

    fireEvent.click(screen.getByRole("button", { name: /Use Buzz/i }));
    fireEvent.click(screen.getByRole("button", { name: /Prepare safe handoff/i }));

    expect(screen.getByText("Selected: Buzz")).toBeTruthy();
    expect(
      (screen.getByLabelText("Hermes handoff message") as HTMLTextAreaElement).value,
    ).toBe(
      "Route: Buzz. Join the shared human and agent workspace through the native Hermes Buzz gateway while preserving approvals. Request: Debug the install and make the product easier to use.",
    );
  });

  it("offers one-click Jarvis quick starts for common user jobs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/kaizen7/hermes/status") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                installed: true,
                version: "Hermes Agent v0.20.4",
                profile_count: 1,
                error: "",
              }),
          });
        }
        if (url === "/api/kaizen7/hermes/profiles") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                installed: true,
                count: 1,
                profiles: [{ name: "kaizen7", model: "kimi-k2", gateway: "moonshot" }],
              }),
          });
        }
        if (url === "/api/kaizen7/hermes/capabilities") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                execution_enabled: false,
                approval_required_for: [],
                capabilities: [],
              }),
          });
        }
        return Promise.reject(new Error(`unexpected url ${url}`));
      }),
    );

    render(<BusinessView />);

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByText("Quick starts")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Debug app/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Plan my day/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Research market/i })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Debug app/i }));

    expect(screen.getByText("Selected: Codex")).toBeTruthy();
    expect(
      (screen.getByLabelText("What should Jarvis help with?") as HTMLTextAreaElement)
        .value,
    ).toBe("Debug the app, find the blocker, fix it, run tests and report proof.");
    expect(
      (screen.getByLabelText("Hermes handoff message") as HTMLTextAreaElement).value,
    ).toBe(
      "Route: Codex. Build, debug and verify code changes. Request: Debug the app, find the blocker, fix it, run tests and report proof.",
    );
  });

  it("records a Hermes handoff proposal without executing it from the browser", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url === "/api/kaizen7/hermes/status") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              installed: true,
              version: "Hermes Agent v0.20.4",
              profile_count: 1,
              error: "",
            }),
        });
      }
      if (url === "/api/kaizen7/hermes/profiles") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              installed: true,
              count: 1,
              profiles: [{ name: "kaizen7", model: "kimi-k2", gateway: "moonshot" }],
            }),
        });
      }
      if (url === "/api/kaizen7/hermes/capabilities") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              execution_enabled: false,
              approval_required_for: [],
              capabilities: [],
            }),
        });
      }
      if (url === "/api/kaizen7/hermes/chat/propose") {
        expect(init?.method).toBe("POST");
        expect(JSON.parse(String(init?.body))).toMatchObject({
          profile: "kaizen7",
          message: "Focus today on the highest leverage action.",
        });
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              accepted: true,
              receipt: { id: "receipt-1" },
            }),
        });
      }
      return Promise.reject(new Error(`unexpected url ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<BusinessView />);

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    fireEvent.change(screen.getByLabelText("Hermes handoff message"), {
      target: { value: "Focus today on the highest leverage action." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Propose handoff/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/kaizen7/hermes/chat/propose",
      expect.objectContaining({ method: "POST" }),
    );
    expect(screen.getByText("Handoff recorded")).toBeTruthy();
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
    expect(writeText.mock.calls[0][0]).toContain("Readiness: ");
    expect(writeText.mock.calls[0][0]).toContain("Readiness checks:");
    expect(writeText.mock.calls[0][0]).toContain("Storage writable: yes");
    expect(writeText.mock.calls[0][0]).toContain("Mission defined: pass");
    expect(writeText.mock.calls[0][0]).toContain("Approval gate present: pass");
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
