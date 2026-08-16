import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MobileCompanionView } from "@/views/MobileCompanionView";

describe("MobileCompanionView", () => {
  it("renders mobile status and approval boundaries", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        product: "KAIZEN7 Mobile Companion",
        mode: "companion",
        capabilities: ["chat", "approvals", "tasks"],
        human_approval_required_for: ["payments", "public posts"],
        execution: {
          can_execute: false,
          reason: "mobile_companion_recommend_only",
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<MobileCompanionView />);

    await waitFor(() => {
      expect(screen.getByText("KAIZEN7 Mobile Companion")).toBeTruthy();
    });
    expect(screen.getByText("payments")).toBeTruthy();
    expect(screen.getByText("public posts")).toBeTruthy();
    expect(screen.getByText("Recommend only")).toBeTruthy();
  });
});
