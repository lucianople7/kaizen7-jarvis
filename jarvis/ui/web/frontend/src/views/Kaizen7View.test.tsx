import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Kaizen7View } from "@/views/Kaizen7View";

const capsule = {
  owner: "Luciano Lopez Barba",
  identity: {
    name: "KAIZEN7",
    role: "Focus and execution layer for Luciano",
    kernel: [
      "Luciano decides.",
      "KAIZEN7 focuses.",
      "Agents execute through approved routes.",
      "Projects grow.",
      "Life does not disperse.",
    ],
  },
  business: {
    name: "THE FOCUX",
    positioning: "A disciplined focus system for digital business growth.",
    north_star: "Turn attention into trusted content.",
  },
  active_mission: {
    name: "Personalized Jarvis for focused execution",
    outcome: "A local operating assistant that keeps one mission visible.",
  },
  priorities: [
    "Keep one active mission visible.",
    "Convert intent into the smallest verified next action.",
    "Record receipts for decisions, actions, tests, and results.",
  ],
  operating_loop: ["Clarify the mission.", "Recommend the next move."],
  approval_required_for: ["payments", "public posts", "credentials"],
  assets: {
    mark: "/kaizen7/the-focux-mark-512.png",
    poster: "/kaizen7/the-focux-logo-poster.png",
  },
};

describe("Kaizen7View", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => capsule,
      })),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders the personalized business capsule from the API", async () => {
    render(<Kaizen7View />);

    expect(await screen.findByText("THE FOCUX")).toBeTruthy();
    expect(screen.getByText("Personalized Jarvis for focused execution")).toBeTruthy();
    expect(screen.getByText("Luciano decides.")).toBeTruthy();
    expect(screen.getByText("payments")).toBeTruthy();

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith("/api/kaizen7/capsule");
    });
  });
});
