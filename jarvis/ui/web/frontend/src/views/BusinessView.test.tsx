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
    expect(screen.getByText("Priority filter")).toBeTruthy();
    expect(screen.getAllByText("Human approval").length).toBeGreaterThan(0);
    expect(screen.getByText("Publishing")).toBeTruthy();
    expect(screen.getByText("Financial operation")).toBeTruthy();
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

  it("turns a daily action into a completed receipt", () => {
    render(<BusinessView />);

    expect(screen.getByText("Daily execution")).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", { name: /Complete Publish one proof of progress/i }),
    );

    expect(screen.getByText("Completed action: Publish one proof of progress")).toBeTruthy();
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
  });

  it("copies an operational briefing for use outside the app", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<BusinessView />);

    fireEvent.click(screen.getByRole("button", { name: /Copy briefing/i }));

    expect(writeText).toHaveBeenCalledOnce();
    expect(writeText.mock.calls[0][0]).toContain("Business OS Briefing");
    expect(writeText.mock.calls[0][0]).toContain("Active priorities");
  });
});
