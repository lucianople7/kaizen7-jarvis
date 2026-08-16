import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, CircleDot, ShieldCheck } from "lucide-react";

type Kaizen7Capsule = {
  owner: string;
  identity: {
    name: string;
    role: string;
    kernel: string[];
  };
  business: {
    name: string;
    positioning: string;
    north_star: string;
  };
  active_mission: {
    name: string;
    outcome: string;
  };
  priorities: string[];
  operating_loop: string[];
  approval_required_for: string[];
  assets: {
    mark: string;
    poster: string;
  };
};

const FALLBACK_CAPSULE: Kaizen7Capsule = {
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
    north_star:
      "Turn attention into trusted content, clear offers, sale paths, and verified improvement.",
  },
  active_mission: {
    name: "Personalized Jarvis for focused execution",
    outcome:
      "A local operating assistant that keeps one mission visible, limits priorities, and records evidence before claiming progress.",
  },
  priorities: [
    "Keep one active mission visible.",
    "Convert intent into the smallest verified next action.",
    "Record receipts for decisions, actions, tests, and results.",
  ],
  operating_loop: [
    "Clarify the mission.",
    "Recommend the next move.",
    "Ask approval when risk requires it.",
    "Execute only through approved tools.",
    "Record the receipt.",
    "Review metrics and improve the next cycle.",
  ],
  approval_required_for: [
    "payments",
    "purchases",
    "public posts",
    "outbound messages",
    "credentials",
    "financial operations",
    "deployments",
    "destructive edits",
    "irreversible desktop actions",
  ],
  assets: {
    mark: "/kaizen7/the-focux-mark-512.png",
    poster: "/kaizen7/the-focux-logo-poster.png",
  },
};

export function Kaizen7View() {
  const [capsule, setCapsule] = useState<Kaizen7Capsule>(FALLBACK_CAPSULE);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    void fetch("/api/kaizen7/capsule")
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as Kaizen7Capsule;
      })
      .then((data) => {
        if (!cancelled) setCapsule(data);
      })
      .catch((exc: unknown) => {
        if (!cancelled) setError(exc instanceof Error ? exc.message : "Unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="h-full overflow-auto px-5 py-5 text-foreground md:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-5">
        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="min-w-0 rounded-lg border border-border/70 bg-card/88 p-5 shadow-sm backdrop-blur">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
              <img
                src={capsule.assets.mark}
                alt="THE FOCUX seal"
                className="h-24 w-24 shrink-0 rounded-md border border-primary/30 object-cover shadow"
              />
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-normal text-primary">
                  {capsule.identity.name}
                </p>
                <h1 className="mt-1 text-3xl font-semibold tracking-normal text-foreground">
                  {capsule.business.name}
                </h1>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                  {capsule.business.positioning}
                </p>
              </div>
            </div>

            <div className="mt-6 rounded-md border border-border/70 bg-background/55 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <CircleDot className="h-4 w-4 text-primary" />
                <span>{capsule.active_mission.name}</span>
              </div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {capsule.active_mission.outcome}
              </p>
            </div>
          </div>

          <aside className="rounded-lg border border-border/70 bg-card/88 p-5 shadow-sm backdrop-blur">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <ShieldCheck className="h-4 w-4 text-primary" />
              <span>Human approval</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {capsule.approval_required_for.map((item) => (
                <span
                  key={item}
                  className="rounded border border-border bg-background/70 px-2 py-1 text-xs text-muted-foreground"
                >
                  {item}
                </span>
              ))}
            </div>
            {error ? (
              <div className="mt-4 flex items-center gap-2 text-xs text-amber-500">
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>{error}</span>
              </div>
            ) : null}
          </aside>
        </section>

        <section className="grid gap-5 lg:grid-cols-3">
          <Panel title="Kernel" items={capsule.identity.kernel} />
          <Panel title="Priorities" items={capsule.priorities} />
          <Panel title="Operating loop" items={capsule.operating_loop} />
        </section>
      </div>
    </main>
  );
}

function Panel({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="rounded-lg border border-border/70 bg-card/88 p-5 shadow-sm backdrop-blur">
      <h2 className="text-sm font-semibold uppercase tracking-normal text-muted-foreground">
        {title}
      </h2>
      <ul className="mt-4 space-y-3">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-sm leading-6 text-foreground">
            <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-primary" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
