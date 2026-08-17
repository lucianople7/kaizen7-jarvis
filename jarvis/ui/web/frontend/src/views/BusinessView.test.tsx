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
});
