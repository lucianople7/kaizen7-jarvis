import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("mobile web scripts", () => {
  it("exposes LAN-ready dev and preview commands", () => {
    const packageJson = JSON.parse(readFileSync("package.json", "utf8"));

    expect(packageJson.scripts["dev:mobile"]).toBe("vite --host 0.0.0.0");
    expect(packageJson.scripts["preview:mobile"]).toBe(
      "vite preview --host 0.0.0.0",
    );
  });
});
