import { describe, expect, it } from "vitest";
import { initialSectionFromSearch, SECTION_IDS, SECTION_LABELS } from "./events";

describe("business section registration", () => {
  it("is a valid section with a label and deep link", () => {
    expect(SECTION_IDS).toContain("business");
    expect(SECTION_LABELS.business).toBe("Business");
    expect(initialSectionFromSearch("?view=business")).toBe("business");
  });
});
