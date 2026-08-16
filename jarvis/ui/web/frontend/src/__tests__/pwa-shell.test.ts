import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";

const frontendRoot = resolve(__dirname, "..", "..");

describe("installable web shell", () => {
  test("advertises a mobile-installable app from the HTML shell", () => {
    const html = readFileSync(resolve(frontendRoot, "index.html"), "utf8");

    expect(html).toContain('<link rel="manifest" href="/manifest.webmanifest" />');
    expect(html).toContain('<meta name="theme-color" content="#0a0e14" />');
    expect(html).toContain('<meta name="mobile-web-app-capable" content="yes" />');
    expect(html).toContain('<meta name="apple-mobile-web-app-capable" content="yes" />');
  });

  test("ships a manifest for the browser app without hardcoding a wake word", () => {
    const manifest = JSON.parse(
      readFileSync(resolve(frontendRoot, "public", "manifest.webmanifest"), "utf8"),
    );

    expect(manifest.name).toBe("Assistant");
    expect(manifest.short_name).toBe("Assistant");
    expect(manifest.start_url).toBe("/");
    expect(manifest.scope).toBe("/");
    expect(manifest.display).toBe("standalone");
    expect(manifest.icons).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          src: "/jarvis-gigi-256.png",
          sizes: "256x256",
          type: "image/png",
        }),
      ]),
    );
  });

  test("registers a service worker that never caches API responses", () => {
    const html = readFileSync(resolve(frontendRoot, "index.html"), "utf8");
    const worker = readFileSync(resolve(frontendRoot, "public", "mobile-sw.js"), "utf8");

    expect(html).toContain('navigator.serviceWorker.register("/mobile-sw.js")');
    expect(worker).toContain('url.pathname.startsWith("/api/")');
    expect(worker).toContain("return;");
    expect(worker).toContain("cache.addAll");
  });
});
