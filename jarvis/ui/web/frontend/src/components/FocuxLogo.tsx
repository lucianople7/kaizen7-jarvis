import { useEffect, useState } from "react";

/**
 * THE FOCUX brand mark. Fetches the mark from the KAIZEN7 brand endpoint
 * (served by kaizen7_routes.py) and renders it with the caller's sizing.
 * Falls back to the stylized wordmark if the asset is unavailable.
 */
export function FocuxLogo({
  className = "h-16 w-16",
  alt = "THE FOCUX",
}: {
  className?: string;
  alt?: string;
}) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const res = await fetch("/api/kaizen7/brand/mark");
        if (res.ok && active) setSrc(res.url);
      } catch {
        // fall through to the wordmark
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  if (src) {
    return (
      <img
        src={src}
        alt={alt}
        className={`${className} object-contain`}
        data-testid="focux-logo"
      />
    );
  }
  return (
    <div
      className={`${className} flex items-center justify-center rounded-full border border-primary/40 bg-gradient-to-br from-primary/15 to-primary/5 font-display text-sm font-bold tracking-widest text-primary`}
      data-testid="focux-logo-fallback"
    >
      FOCUX
    </div>
  );
}
