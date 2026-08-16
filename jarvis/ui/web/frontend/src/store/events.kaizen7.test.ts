import { describe, expect, it } from "vitest";
import { isSectionId, SECTION_IDS, SECTION_LABELS } from "@/store/events";

describe("KAIZEN7 section registration", () => {
  it("registers the personalized Jarvis capsule as a real section", () => {
    expect(SECTION_IDS).toContain("kaizen7");
    expect(isSectionId("kaizen7")).toBe(true);
    expect(SECTION_LABELS.kaizen7).toBe("KAIZEN7");
  });
});
