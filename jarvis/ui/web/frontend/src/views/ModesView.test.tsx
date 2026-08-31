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

  it("blocks personal core generation without mission and focus", async () => {
    render(<ModesView />);

    await screen.findByText("Jarvis");
    expect(screen.getByText("Jarvis Personal Core")).toBeTruthy();

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
    expect((screen.getByLabelText("Mode name") as HTMLInputElement).value).toBe("");
  });

  it("builds a personal core mode with mission, focus, priority cap and approval gates", async () => {
    render(<ModesView />);

    await screen.findByText("Jarvis");
    expect(screen.getByText("Jarvis Personal Core")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Assistant mission"), {
      target: { value: "Keep Luciano focused on one business move at a time" },
    });
    fireEvent.change(screen.getByLabelText("Owner"), {
      target: { value: "Luciano" },
    });
    fireEvent.change(screen.getByLabelText("Active focus"), {
      target: { value: "Build a clean PersonalJarvis product" },
    });
    fireEvent.click(screen.getByLabelText("Jarvis tone"));
    fireEvent.click(screen.getByRole("option", { name: "Executive" }));
    fireEvent.click(screen.getByLabelText("Jarvis energy"));
    fireEvent.click(screen.getByRole("option", { name: "High focus" }));
    fireEvent.change(screen.getByLabelText("Approval boundaries"), {
      target: { value: "Never publish, pay or message without approval" },
    });
    fireEvent.change(screen.getByLabelText("Max active priorities"), {
      target: { value: "3" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Build personal Jarvis/i }));

    const modeName = screen.getByLabelText("Mode name") as HTMLInputElement;
    expect(modeName.value).toBe("Jarvis Personal Operator");
    expect(document.activeElement).toBe(modeName);
    expect(pushToast).toHaveBeenCalledWith(
      "info",
      "Jarvis Personal Core ready. Review it, then save the mode.",
    );
    expect((screen.getByLabelText("One-line description") as HTMLInputElement).value).toBe(
      "Executive personal operating mode for Luciano with one active focus.",
    );
    const behavior = (screen.getByLabelText("How it behaves") as HTMLTextAreaElement).value;
    expect(behavior).toContain("Keep Luciano focused on one business move at a time");
    expect(behavior).toContain("Owner: Luciano");
    expect(behavior).toContain("Active focus: Build a clean PersonalJarvis product");
    expect(behavior).toContain("Priority cap: keep at most 3 active priorities visible.");
    expect(behavior).toContain("Never publish, pay or message without approval");
    expect(behavior).toContain("Always separate recommendation from execution.");
    expect(behavior).toContain(
      "Human approval is required before publishing, payments, messages, credentials, financial operations, external sends, destructive changes, or irreversible actions.",
    );

    fireEvent.click(screen.getByRole("button", { name: /Save mode/i }));

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      "/api/modes",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("Jarvis Personal Operator"),
      }),
    ));
    expect(pushToast).toHaveBeenCalledWith("success", "Jarvis Personal Operator saved.");
  });
});
