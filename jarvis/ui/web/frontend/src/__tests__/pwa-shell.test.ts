import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";

const frontendRoot = resolve(__dirname, "..", "..");

describe("mobile PWA shell", () => {
  test("advertises an installable mobile companion from the HTML shell", () => {
    const html = readFileSync(resolve(frontendRoot, "index.html"), "utf8");

    expect(html).toContain('<link rel="manifest" href="/manifest.webmanifest" />');
    expect(html).toContain('<meta name="theme-color" content="#0a0e14" />');
    expect(html).toContain('<meta name="mobile-web-app-capable" content="yes" />');
    expect(html).toContain('<meta name="apple-mobile-web-app-capable" content="yes" />');
  });

  test("registers a mobile service worker for the installable shell", () => {
    const html = readFileSync(resolve(frontendRoot, "index.html"), "utf8");
    const worker = readFileSync(resolve(frontendRoot, "public", "mobile-sw.js"), "utf8");

    expect(html).toContain('navigator.serviceWorker.register("/mobile-sw.js")');
    expect(worker).toContain('url.pathname.startsWith("/api/")');
    expect(worker).toContain("return;");
    expect(worker).toContain("cache.addAll");
  });

  test("ships a manifest that opens Jarvis on the mobile view", () => {
    const manifest = JSON.parse(
      readFileSync(resolve(frontendRoot, "public", "manifest.webmanifest"), "utf8"),
    );

    expect(manifest.name).toBe("KAIZEN7 Personal Jarvis");
    expect(manifest.short_name).toBe("Jarvis");
    expect(manifest.start_url).toBe("/?view=mobile");
    expect(manifest.display).toBe("standalone");
    expect(manifest.orientation).toBe("portrait-primary");
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
});
