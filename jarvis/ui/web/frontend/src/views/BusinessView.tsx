import { useEffect, useMemo, useState } from "react";
import {
  BadgeCheck,
  BriefcaseBusiness,
  CheckCircle2,
  CircleAlert,
  Clipboard,
  LockKeyhole,
  Plus,
  Save,
  Target,
  TrendingUp,
} from "lucide-react";
import { ViewHeader } from "@/views/ChatsView";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

const STORAGE_KEY = "jarvis.business.workspace.v1";
const MAX_ACTIVE_PRIORITIES = 3;

type DecisionRisk = "low" | "approval";

interface BusinessDecision {
  id: string;
  title: string;
  evidence: string;
  result: string;
  risk: DecisionRisk;
  createdAt: string;
}

interface BusinessAction {
  id: string;
  title: string;
  risk: DecisionRisk;
  done: boolean;
}

interface BusinessWorkspace {
  mission: string;
  offer: string;
  audience: string;
  northStar: string;
  weeklyObjective: string;
  priorities: string[];
  metrics: string[];
  actions: BusinessAction[];
  decisions: BusinessDecision[];
}

const DEFAULT_WORKSPACE: BusinessWorkspace = {
  mission:
    "Build a practical personal agent that turns attention into useful business execution without scattering focus.",
  offer:
    "A local-first assistant for planning, research, content, tasks and controlled execution.",
  audience:
    "Solo builders and digital operators who need one clear operating cockpit across desktop and mobile.",
  northStar: "One active mission, three priorities, visible receipts.",
  weeklyObjective: "Convert the assistant from a technical shell into a daily business operating surface.",
  priorities: [
    "Keep the mobile web shell installable and useful.",
    "Make every business action leave evidence and a result.",
    "Block irreversible execution until a human approves it.",
  ],
  metrics: [
    "Active mission clarity",
    "Completed business receipts",
    "Blocked unsafe actions",
    "Weekly shipped improvements",
  ],
  actions: [
    {
      id: "seed-proof",
      title: "Publish one proof of progress",
      risk: "low",
      done: false,
    },
    {
      id: "seed-offer",
      title: "Review the active offer and next lead path",
      risk: "low",
      done: false,
    },
    {
      id: "seed-risk",
      title: "Prepare one guarded action for human approval",
      risk: "approval",
      done: false,
    },
  ],
  decisions: [
    {
      id: "seed-local-first",
      title: "Keep the first business workspace local-first",
      evidence: "No model API key, payment account or publishing token is required.",
      result: "The section works immediately after install and stores data in this browser profile.",
      risk: "low",
      createdAt: "seed",
    },
    {
      id: "seed-approval-gate",
      title: "Separate recommended actions from execution",
      evidence: "Publishing, payments, credentials and irreversible operations are explicitly gated.",
      result: "The assistant can plan work without silently acting outside the app.",
      risk: "approval",
      createdAt: "seed",
    },
  ],
};

const GUARDED_ACTIONS = [
  "Payment",
  "Publishing",
  "Outbound message",
  "Credential change",
  "Financial operation",
  "Irreversible file or account change",
];

function readWorkspace(): BusinessWorkspace {
  if (typeof window === "undefined") return DEFAULT_WORKSPACE;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_WORKSPACE;
    const parsed = JSON.parse(raw) as Partial<BusinessWorkspace>;
    return {
      ...DEFAULT_WORKSPACE,
      ...parsed,
      priorities: normalizeList(parsed.priorities, DEFAULT_WORKSPACE.priorities),
      metrics: normalizeList(parsed.metrics, DEFAULT_WORKSPACE.metrics),
      actions: Array.isArray(parsed.actions)
        ? parsed.actions.filter(isAction)
        : DEFAULT_WORKSPACE.actions,
      decisions: Array.isArray(parsed.decisions)
        ? parsed.decisions.filter(isDecision)
        : DEFAULT_WORKSPACE.decisions,
    };
  } catch {
    return DEFAULT_WORKSPACE;
  }
}

function normalizeList(value: unknown, fallback: string[]): string[] {
  if (!Array.isArray(value)) return fallback;
  const clean = value.filter((item): item is string => typeof item === "string");
  return clean.length ? clean : fallback;
}

function isAction(value: unknown): value is BusinessAction {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return (
    typeof item.id === "string" &&
    typeof item.title === "string" &&
    (item.risk === "low" || item.risk === "approval") &&
    typeof item.done === "boolean"
  );
}

function isDecision(value: unknown): value is BusinessDecision {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return (
    typeof item.id === "string" &&
    typeof item.title === "string" &&
    typeof item.evidence === "string" &&
    typeof item.result === "string" &&
    (item.risk === "low" || item.risk === "approval") &&
    typeof item.createdAt === "string"
  );
}

function persistWorkspace(workspace: BusinessWorkspace): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace));
}

export function BusinessView() {
  const [workspace, setWorkspace] = useState<BusinessWorkspace>(() => readWorkspace());
  const [saved, setSaved] = useState(false);
  const [priorityDraft, setPriorityDraft] = useState("");
  const [metricDraft, setMetricDraft] = useState("");
  const [actionDraft, setActionDraft] = useState("");
  const [actionRisk, setActionRisk] = useState<DecisionRisk>("low");
  const [decisionDraft, setDecisionDraft] = useState({
    title: "",
    evidence: "",
    result: "",
    risk: "low" as DecisionRisk,
  });

  useEffect(() => {
    const timer = window.setTimeout(() => {
      persistWorkspace(workspace);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 1200);
    }, 250);
    return () => window.clearTimeout(timer);
  }, [workspace]);

  const activePriorities = useMemo(
    () => workspace.priorities.slice(0, MAX_ACTIVE_PRIORITIES),
    [workspace.priorities],
  );
  const parkedPriorities = useMemo(
    () => workspace.priorities.slice(MAX_ACTIVE_PRIORITIES),
    [workspace.priorities],
  );

  const addPriority = () => {
    const value = priorityDraft.trim();
    if (!value) return;
    setWorkspace((current) => ({
      ...current,
      priorities: [...current.priorities, value],
    }));
    setPriorityDraft("");
  };

  const addMetric = () => {
    const value = metricDraft.trim();
    if (!value) return;
    setWorkspace((current) => ({ ...current, metrics: [...current.metrics, value] }));
    setMetricDraft("");
  };

  const addAction = () => {
    const value = actionDraft.trim();
    if (!value) return;
    setWorkspace((current) => ({
      ...current,
      actions: [
        ...current.actions,
        {
          id: `${Date.now()}`,
          title: value,
          risk: actionRisk,
          done: false,
        },
      ],
    }));
    setActionDraft("");
    setActionRisk("low");
  };

  const completeAction = (action: BusinessAction) => {
    if (action.risk === "approval") return;
    setWorkspace((current) => ({
      ...current,
      actions: current.actions.map((candidate) =>
        candidate.id === action.id ? { ...candidate, done: true } : candidate,
      ),
      decisions: [
        {
          id: `action-${Date.now()}`,
          title: `Completed action: ${action.title}`,
          evidence: "Completed inside the Business OS daily execution list.",
          result: "Action marked done and recorded as an operating receipt.",
          risk: "low",
          createdAt: new Date().toISOString(),
        },
        ...current.decisions,
      ],
    }));
  };

  const copyBriefing = async () => {
    const briefing = [
      "# Business OS Briefing",
      "",
      `Mission: ${workspace.mission}`,
      `Offer: ${workspace.offer}`,
      `Audience: ${workspace.audience}`,
      `North star: ${workspace.northStar}`,
      `This week: ${workspace.weeklyObjective}`,
      "",
      "Active priorities:",
      ...activePriorities.map((priority, index) => `${index + 1}. ${priority}`),
      "",
      "Daily execution:",
      ...workspace.actions
        .filter((action) => !action.done)
        .map(
          (action) =>
            `- ${action.title}${action.risk === "approval" ? " [approval required]" : ""}`,
        ),
      "",
      "Metrics:",
      ...workspace.metrics.map((metric) => `- ${metric}`),
    ].join("\n");
    await navigator.clipboard?.writeText(briefing);
  };

  const addDecision = () => {
    const title = decisionDraft.title.trim();
    const evidence = decisionDraft.evidence.trim();
    const result = decisionDraft.result.trim();
    if (!title || !evidence || !result) return;
    setWorkspace((current) => ({
      ...current,
      decisions: [
        {
          id: `${Date.now()}`,
          title,
          evidence,
          result,
          risk: decisionDraft.risk,
          createdAt: new Date().toISOString(),
        },
        ...current.decisions,
      ],
    }));
    setDecisionDraft({ title: "", evidence: "", result: "", risk: "low" });
  };

  return (
    <div className="flex h-full flex-col">
      <ViewHeader
        icon={<BriefcaseBusiness className="h-4 w-4 text-primary" />}
        title="Business OS"
        subtitle="One mission, limited priorities, local receipts and human approval gates."
        right={
          <div className="flex items-center gap-2">
            <Button size="sm" variant="secondary" onClick={copyBriefing}>
              <Clipboard className="mr-1 h-4 w-4" />
              Copy briefing
            </Button>
            <Badge variant={saved ? "default" : "outline"} className="gap-1">
              <Save className="h-3 w-3" />
              {saved ? "Saved locally" : "Local workspace"}
            </Badge>
          </div>
        }
      />

      <ScrollArea className="flex-1">
        <div className="grid gap-4 p-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
          <section className="space-y-4">
            <article className="card-outline p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
                <Target className="h-4 w-4 text-primary" />
                Active mission
              </div>
              <EditableField
                label="Mission"
                value={workspace.mission}
                onChange={(mission) => setWorkspace((current) => ({ ...current, mission }))}
                rows={3}
              />
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <EditableField
                  label="Offer"
                  value={workspace.offer}
                  onChange={(offer) => setWorkspace((current) => ({ ...current, offer }))}
                />
                <EditableField
                  label="Audience"
                  value={workspace.audience}
                  onChange={(audience) =>
                    setWorkspace((current) => ({ ...current, audience }))
                  }
                />
              </div>
            </article>

            <article className="card-outline p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
                <TrendingUp className="h-4 w-4 text-primary" />
                Objective and metrics
              </div>
              <EditableField
                label="North star"
                value={workspace.northStar}
                onChange={(northStar) =>
                  setWorkspace((current) => ({ ...current, northStar }))
                }
              />
              <EditableField
                label="This week"
                value={workspace.weeklyObjective}
                onChange={(weeklyObjective) =>
                  setWorkspace((current) => ({ ...current, weeklyObjective }))
                }
                className="mt-3"
              />
              <ListEditor
                label="Metrics"
                values={workspace.metrics}
                draft={metricDraft}
                onDraft={setMetricDraft}
                onAdd={addMetric}
                onRemove={(index) =>
                  setWorkspace((current) => ({
                    ...current,
                    metrics: current.metrics.filter((_, i) => i !== index),
                  }))
                }
              />
            </article>

            <article className="card-outline p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <BadgeCheck className="h-4 w-4 text-primary" />
                  Decision receipts
                </div>
                <Badge variant="outline">{workspace.decisions.length} receipts</Badge>
              </div>
              <div className="grid gap-2 md:grid-cols-3">
                <input
                  value={decisionDraft.title}
                  onChange={(event) =>
                    setDecisionDraft((current) => ({
                      ...current,
                      title: event.target.value,
                    }))
                  }
                  placeholder="Decision"
                  aria-label="Decision"
                  className="rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
                />
                <input
                  value={decisionDraft.evidence}
                  onChange={(event) =>
                    setDecisionDraft((current) => ({
                      ...current,
                      evidence: event.target.value,
                    }))
                  }
                  placeholder="Evidence"
                  aria-label="Evidence"
                  className="rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
                />
                <input
                  value={decisionDraft.result}
                  onChange={(event) =>
                    setDecisionDraft((current) => ({
                      ...current,
                      result: event.target.value,
                    }))
                  }
                  placeholder="Result"
                  aria-label="Result"
                  className="rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
                />
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <select
                  value={decisionDraft.risk}
                  onChange={(event) =>
                    setDecisionDraft((current) => ({
                      ...current,
                      risk: event.target.value as DecisionRisk,
                    }))
                  }
                  aria-label="Decision risk"
                  className="rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
                >
                  <option value="low">Recommendation only</option>
                  <option value="approval">Needs human approval</option>
                </select>
                <Button size="sm" onClick={addDecision}>
                  <Plus className="mr-1 h-4 w-4" />
                  Add receipt
                </Button>
              </div>
              <div className="mt-4 space-y-2">
                {workspace.decisions.map((decision) => (
                  <article
                    key={decision.id}
                    className="rounded-md border border-border/70 bg-card/50 p-3"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-semibold">{decision.title}</h3>
                      <Badge
                        variant={decision.risk === "approval" ? "destructive" : "secondary"}
                      >
                        {decision.risk === "approval"
                          ? "Approval required"
                          : "Recommendation"}
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Evidence: {decision.evidence}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Result: {decision.result}
                    </p>
                  </article>
                ))}
              </div>
            </article>
          </section>

          <aside className="space-y-4">
            <article className="card-outline p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                  Daily execution
                </div>
                <Badge variant="outline">
                  {workspace.actions.filter((action) => !action.done).length} open
                </Badge>
              </div>
              <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_150px_auto]">
                <input
                  value={actionDraft}
                  onChange={(event) => setActionDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") addAction();
                  }}
                  aria-label="New action"
                  className="rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
                />
                <select
                  value={actionRisk}
                  onChange={(event) => setActionRisk(event.target.value as DecisionRisk)}
                  aria-label="Action risk"
                  className="rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
                >
                  <option value="low">Recommendation</option>
                  <option value="approval">Needs approval</option>
                </select>
                <Button size="sm" onClick={addAction}>
                  <Plus className="mr-1 h-4 w-4" />
                  Add action
                </Button>
              </div>
              <ul className="mt-3 space-y-2">
                {workspace.actions.map((action) => (
                  <li
                    key={action.id}
                    className="flex items-center gap-2 rounded-md border border-border/70 bg-card/40 px-3 py-2 text-sm"
                  >
                    <span
                      className={
                        action.done
                          ? "min-w-0 flex-1 line-through text-muted-foreground"
                          : "min-w-0 flex-1"
                      }
                    >
                      {action.title}
                    </span>
                    {action.risk === "approval" ? (
                      <Badge variant="destructive">Approval required</Badge>
                    ) : action.done ? (
                      <Badge variant="secondary">Done</Badge>
                    ) : (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => completeAction(action)}
                        aria-label={`Complete ${action.title}`}
                      >
                        Complete
                      </Button>
                    )}
                  </li>
                ))}
              </ul>
            </article>

            <article className="card-outline p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="text-sm font-semibold">Priority filter</div>
                <Badge variant="outline">Max {MAX_ACTIVE_PRIORITIES} active</Badge>
              </div>
              <ListEditor
                label="Priorities"
                values={workspace.priorities}
                draft={priorityDraft}
                onDraft={setPriorityDraft}
                onAdd={addPriority}
                onRemove={(index) =>
                  setWorkspace((current) => ({
                    ...current,
                    priorities: current.priorities.filter((_, i) => i !== index),
                  }))
                }
              />
              <div className="mt-4 rounded-md border border-primary/30 bg-primary/10 p-3">
                <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-primary">
                  Active now
                </div>
                <ol className="space-y-1.5 text-sm">
                  {activePriorities.map((priority, index) => (
                    <li key={`${priority}-${index}`}>
                      {index + 1}. {priority}
                    </li>
                  ))}
                </ol>
              </div>
              {parkedPriorities.length > 0 && (
                <div className="mt-3 rounded-md border border-border bg-background/40 p-3">
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Parked
                  </div>
                  <ul className="space-y-1.5 text-sm text-muted-foreground">
                    {parkedPriorities.map((priority, index) => (
                      <li key={`${priority}-${index}`}>{priority}</li>
                    ))}
                  </ul>
                </div>
              )}
            </article>

            <article className="card-outline p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
                <LockKeyhole className="h-4 w-4 text-primary" />
                Execution boundary
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">
                This surface can recommend and record work. It does not execute guarded
                actions from the business workspace.
              </p>
              <div className="mt-3 space-y-2">
                {GUARDED_ACTIONS.map((action) => (
                  <div
                    key={action}
                    className="flex items-center gap-2 rounded-md border border-border/70 bg-background/40 px-3 py-2 text-sm"
                  >
                    <CircleAlert className="h-4 w-4 text-amber-500" />
                    <span>{action}</span>
                    <Badge variant="outline" className="ml-auto">
                      Human approval
                    </Badge>
                  </div>
                ))}
              </div>
            </article>
          </aside>
        </div>
      </ScrollArea>
    </div>
  );
}

function EditableField({
  label,
  value,
  onChange,
  rows = 2,
  className = "",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  className?: string;
}) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <textarea
        value={value}
        rows={rows}
        onChange={(event) => onChange(event.target.value)}
        className="w-full resize-none rounded-md border border-border bg-background/60 px-3 py-2 text-sm leading-relaxed outline-none transition-colors focus:border-primary/60"
      />
    </label>
  );
}

function ListEditor({
  label,
  values,
  draft,
  onDraft,
  onAdd,
  onRemove,
}: {
  label: string;
  values: string[];
  draft: string;
  onDraft: (value: string) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
}) {
  return (
    <div className="mt-4">
      <div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className="flex gap-2">
        <input
          value={draft}
          onChange={(event) => onDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") onAdd();
          }}
          aria-label={`New ${label.toLowerCase()}`}
          className="min-w-0 flex-1 rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
        />
        <Button type="button" size="sm" variant="secondary" onClick={onAdd}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <ul className="mt-3 space-y-1.5">
        {values.map((value, index) => (
          <li
            key={`${value}-${index}`}
            className="flex items-center gap-2 rounded-md border border-border/70 bg-card/40 px-3 py-2 text-sm"
          >
            <span className="min-w-0 flex-1">{value}</span>
            <button
              type="button"
              onClick={() => onRemove(index)}
              className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-background/60 hover:text-foreground"
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
