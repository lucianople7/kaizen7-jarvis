import { useEffect, useState } from "react";
import { CheckCircle2, Link2, Send, ShieldCheck, Smartphone } from "lucide-react";

type MobileStatus = {
  product: string;
  mode: string;
  capabilities: string[];
  human_approval_required_for: string[];
  execution: {
    can_execute: boolean;
    reason: string;
  };
};

type PairingChallenge = {
  challenge_id: string;
  code: string;
  pairing_url: string;
  expires_in_seconds: number;
};

type IntentReceipt = {
  status: string;
  approval_required_for: string[];
  receipt: {
    id: string;
    source: string;
    created_at: string;
  };
};

const FALLBACK_STATUS: MobileStatus = {
  product: "KAIZEN7 Mobile Companion",
  mode: "companion",
  capabilities: ["chat", "voice_input", "approvals", "tasks", "receipts"],
  human_approval_required_for: [
    "payments",
    "public posts",
    "outbound messages",
    "credentials",
    "financial operations",
  ],
  execution: {
    can_execute: false,
    reason: "mobile_companion_recommend_only",
  },
};

export function MobileCompanionView() {
  const [status, setStatus] = useState<MobileStatus>(FALLBACK_STATUS);
  const [pairing, setPairing] = useState<PairingChallenge | null>(null);
  const [intent, setIntent] = useState("");
  const [receipt, setReceipt] = useState<IntentReceipt | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void fetch("/api/mobile/status", { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as MobileStatus;
      })
      .then((data) => {
        if (!cancelled) setStatus(data);
      })
      .catch((exc: unknown) => {
        if (!cancelled) setError(exc instanceof Error ? exc.message : "Unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function createPairing() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/mobile/pairing/challenge", {
        method: "POST",
        cache: "no-store",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setPairing((await res.json()) as PairingChallenge);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Pairing unavailable");
    } finally {
      setBusy(false);
    }
  }

  async function sendIntent() {
    const text = intent.trim();
    if (!text) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/mobile/intents", {
        method: "POST",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setReceipt((await res.json()) as IntentReceipt);
      setIntent("");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Intent unavailable");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="h-full overflow-auto px-4 py-4 text-foreground md:px-8">
      <div className="mx-auto grid max-w-6xl gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
        <section className="rounded-lg border border-border/70 bg-card/90 p-5 shadow-sm backdrop-blur">
          <div className="flex items-start gap-4">
            <div className="rounded-md bg-primary/10 p-3 text-primary">
              <Smartphone className="h-6 w-6" aria-hidden />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-normal text-primary">
                Mobile Gateway
              </p>
              <h1 className="mt-1 text-2xl font-semibold tracking-normal">
                {status.product}
              </h1>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Android becomes the command surface for Jarvis while execution
                stays gated on the desktop runtime.
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <InfoTile title="Mode" value={status.mode} />
            <InfoTile
              title="Execution"
              value={status.execution.can_execute ? "Can execute" : "Recommend only"}
            />
          </div>

          <div className="mt-5">
            <h2 className="text-sm font-semibold">Companion capabilities</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {status.capabilities.map((capability) => (
                <span
                  key={capability}
                  className="rounded border border-border bg-background/70 px-2 py-1 text-xs text-muted-foreground"
                >
                  {capability.replaceAll("_", " ")}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-5 rounded-md border border-border/70 bg-background/55 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Send className="h-4 w-4 text-primary" aria-hidden />
              <span>Send mobile intent</span>
            </div>
            <textarea
              className="mt-3 min-h-28 w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              placeholder="Ask Jarvis what to prepare. Sensitive actions stay pending for approval."
              value={intent}
              onChange={(event) => setIntent(event.target.value)}
            />
            <button
              className="mt-3 inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
              type="button"
              disabled={!intent.trim() || busy}
              onClick={() => void sendIntent()}
            >
              <Send className="h-4 w-4" aria-hidden />
              Queue for approval
            </button>
            {receipt ? (
              <p className="mt-3 text-xs text-muted-foreground">
                Receipt {receipt.receipt.id}: {receipt.status}
              </p>
            ) : null}
          </div>
        </section>

        <aside className="flex flex-col gap-5">
          <section className="rounded-lg border border-border/70 bg-card/90 p-5 shadow-sm backdrop-blur">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Link2 className="h-4 w-4 text-primary" aria-hidden />
              <span>Pair Android</span>
            </div>
            <button
              className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
              type="button"
              disabled={busy}
              onClick={() => void createPairing()}
            >
              <Link2 className="h-4 w-4" aria-hidden />
              Create pairing code
            </button>
            {pairing ? (
              <div className="mt-4 rounded-md border border-border bg-background/70 p-3">
                <p className="text-2xl font-semibold tracking-normal">{pairing.code}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Expires in {pairing.expires_in_seconds} seconds
                </p>
              </div>
            ) : null}
          </section>

          <section className="rounded-lg border border-border/70 bg-card/90 p-5 shadow-sm backdrop-blur">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <ShieldCheck className="h-4 w-4 text-primary" aria-hidden />
              <span>Human approval</span>
            </div>
            <ul className="mt-3 space-y-2">
              {status.human_approval_required_for.map((item) => (
                <li key={item} className="flex gap-2 text-sm text-foreground">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          {error ? (
            <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </p>
          ) : null}
        </aside>
      </div>
    </main>
  );
}

function InfoTile({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-md border border-border/70 bg-background/55 p-4">
      <p className="text-xs font-semibold uppercase tracking-normal text-muted-foreground">
        {title}
      </p>
      <p className="mt-1 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}
