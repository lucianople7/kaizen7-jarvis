import type { ReactNode } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ModesView } from "./ModesView";

const pushToast = vi.fn();
const setActiveSection = vi.fn();
const toggleCall = vi.fn();

vi.mock("@/views/ChatsView", () => ({
  ViewHeader: ({
    title,
    subtitle,
  }: {
    title: string;
    subtitle?: string;
    right?: ReactNode;
  }) => (
    <header>
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
    </header>
  ),
}));

vi.mock("@/store/events", () => ({
  useEventStore: (selector: (state: unknown) => unknown) =>
    selector({
      pushToast,
      setActiveSection,
    }),
}));

vi.mock("@/components/agentic/useVoiceCall", () => ({
  useVoiceCall: () => ({
    active: false,
    busy: false,
    connecting: false,
    toggleCall,
  }),
}));

vi.mock("@/lib/chat", () => ({
  sendChatMessage: vi.fn().mockResolvedValue(true),
}));

const initialState = {
  active: "default",
  section_override: "",
  verbosities: ["brief", "normal", "rich"],
  proactivities: ["reactive", "normal", "forward"],
  modes: [
    {
      slug: "default",
      name: "Jarvis",
      emoji: "J",
      description: "Default mode",
      character: "Helpful and direct.",
      built_in: true,
      voice: "",
      verbosity: "normal",
      proactivity: "normal",
    },
  ],
};

describe("ModesView", () => {
  beforeEach(() => {
    pushToast.mockClear();
    setActiveSection.mockClear();
    toggleCall.mockClear();
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/api/modes" && init?.method === "POST") {
        const body = JSON.parse(String(init.body));
        return Response.json({
          ...initialState,
          active: "jarvis-focus-operator",
          modes: [
            ...initialState.modes,
            {
              slug: "jarvis-focus-operator",
              name: body.name,
              emoji: body.emoji,
              description: body.description,
              character: body.character,
              built_in: false,
              voice: "",
              verbosity: body.verbosity,
              proactivity: body.proactivity,
            },
          ],
        });
      }
      return Response.json(initialState);
    }));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("builds a tailored Jarvis mode from mission, tone, energy and guardrails", async () => {
    render(<ModesView />);

    await screen.findByText("Jarvis");
    expect(screen.getByText("Jarvis a la carta")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Jarvis mission"), {
      target: { value: "Keep Luciano focused on one business move at a time" },
    });
    fireEvent.click(screen.getByLabelText("Jarvis tone"));
    fireEvent.click(screen.getByRole("option", { name: "Executive" }));
    fireEvent.click(screen.getByLabelText("Jarvis energy"));
    fireEvent.click(screen.getByRole("option", { name: "High focus" }));
    fireEvent.change(screen.getByLabelText("Jarvis guardrails"), {
      target: { value: "Never publish, pay or message without approval" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Build my Jarvis/i }));

    const modeName = screen.getByLabelText("Mode name") as HTMLInputElement;
    expect(modeName.value).toBe("Jarvis Focus Operator");
    expect(document.activeElement).toBe(modeName);
    expect(pushToast).toHaveBeenCalledWith(
      "info",
      "Jarvis draft ready. Review it, then save the mode.",
    );
    expect((screen.getByLabelText("One-line description") as HTMLInputElement).value).toBe(
      "Executive operating mode for one focused business move at a time.",
    );
    const behavior = (screen.getByLabelText("How it behaves") as HTMLTextAreaElement).value;
    expect(behavior).toContain("Keep Luciano focused on one business move at a time");
    expect(behavior).toContain("Never publish, pay or message without approval");

    fireEvent.click(screen.getByRole("button", { name: /Save mode/i }));

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      "/api/modes",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("Jarvis Focus Operator"),
      }),
    ));
    expect(pushToast).toHaveBeenCalledWith("success", "Jarvis Focus Operator saved.");
  });
});
