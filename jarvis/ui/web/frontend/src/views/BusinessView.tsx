import { type ReactNode, useEffect, useMemo, useState } from "react";
import {
  BadgeCheck,
  Bot,
  BriefcaseBusiness,
  CheckCircle2,
  CircleAlert,
  Clipboard,
  ClipboardCheck,
  Download,
  LockKeyhole,
  Plus,
  RotateCcw,
  Save,
  Send,
  Smartphone,
  Target,
  TrendingUp,
  Wifi,
} from "lucide-react";
import { ViewHeader } from "@/views/ChatsView";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BrandedSelect } from "@/components/ui/select";

const STORAGE_KEY = "jarvis.business.workspace.v1";
const LEGACY_STORAGE_KEY = "jarvis.business.workspace.v1";
const BACKUP_SCHEMA = "jarvis.business.workspace";
const BACKUP_VERSION = 1;
const MAX_ACTIVE_PRIORITIES = 3;

type DecisionRisk = "low" | "approval";
type CopyStatus = "idle" | "copied" | "error";
type BackupStatus = "idle" | "restored" | "invalid";
type HandoffStatus = "idle" | "saving" | "saved" | "error";

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

interface BusinessMetricTarget {
  id: string;
  label: string;
  current: number;
  target: number;
  unit: string;
}

interface LastComplete {
  actionId: string;
  decisionId: string;
}

interface BusinessWorkspace {
  mission: string;
  offer: string;
  audience: string;
  northStar: string;
  weeklyObjective: string;
  priorities: string[];
  metrics: string[];
  metricTargets: BusinessMetricTarget[];
  actions: BusinessAction[];
  decisions: BusinessDecision[];
  lastComplete: LastComplete | null;
}

interface WorkspaceBackup {
  schema: typeof BACKUP_SCHEMA;
  version: typeof BACKUP_VERSION;
  exportedAt: string;
  workspace: BusinessWorkspace;
}

interface BusinessDiagnostics {
  generatedAt: string;
  currentUrl: string;
  storageWritable: boolean;
  workspacePayloadBytes: number;
  serviceWorkerSupport: boolean;
  serviceWorkerControlled: boolean;
  cacheSupport: boolean;
  userAgent: string;
}

interface ReadinessCheck {
  label: string;
  passed: boolean;
  detail: string;
}

interface HermesStatus {
  installed: boolean;
  version: string;
  profile_count: number;
  error: string;
}

interface HermesProfile {
  name: string;
  model?: string;
  gateway?: string;
  alias?: string;
  handle?: string;
}

interface HermesProfilesPayload {
  installed: boolean;
  count: number;
  profiles: HermesProfile[];
  error?: string;
}

interface HermesCapability {
  id: string;
  title: string;
  command: string;
  requires_approval: boolean;
}

interface HermesCapabilitiesPayload {
  capabilities: HermesCapability[];
  execution_enabled: boolean;
  approval_required_for: string[];
}

const DEFAULT_WORKSPACE: BusinessWorkspace = {
  mission:
    "Turn verified attention into THE FOCUX: signal → dossier → founding list → offer test. Own product later. No premature checkout.",
  offer:
    "A content-led digital business: verified signal, a useful piece, a founding list, then a tested offer.",
  audience:
    "Operators who want one focused loop for content, leads and offer tests — not another checkout bot.",
  northStar: "Leads, assets and validated offers. Irreversible actions stay with the human.",
  weeklyObjective:
    "Move one verified signal into a dossier and one founding-list or offer-test step.",
  priorities: [
    "Capture one verified signal and turn it into a dossier or piece.",
    "Grow the founding list without selling.",
    "Test one offer without charging.",
  ],
  metrics: ["Leads", "Assets", "Validated offers"],
  metricTargets: [
    {
      id: "lead-velocity",
      label: "Lead velocity",
      current: 0,
      target: 25,
      unit: "leads",
    },
    {
      id: "asset-output",
      label: "Asset output",
      current: 0,
      target: 5,
      unit: "assets",
    },
    {
      id: "offer-tests",
      label: "Offer tests",
      current: 0,
      target: 1,
      unit: "tests",
    },
  ],
  actions: [
    {
      id: "seed-signal",
      title: "Capture one verified signal",
      risk: "low",
      done: false,
    },
    {
      id: "seed-dossier",
      title: "Turn the signal into a dossier or piece",
      risk: "low",
      done: false,
    },
    {
      id: "seed-list",
      title: "Add people to the founding list",
      risk: "low",
      done: false,
    },
    {
      id: "seed-offer-test",
      title: "Draft one offer test with no checkout",
      risk: "low",
      done: false,
    },
    {
      id: "seed-publish",
      title: "Prepare one publish or outbound message for approval",
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
  lastComplete: null,
};

const GUARDED_ACTIONS = [
  "Payment",
  "Publishing",
  "Outbound message",
  "Credential change",
  "Financial operation",
  "Irreversible file or account change",
];

const ACTION_RISK_OPTIONS = [
  { value: "low", label: "Recommendation" },
  { value: "approval", label: "Needs approval" },
];

const DECISION_RISK_OPTIONS = [
  { value: "low", label: "Recommendation only" },
  { value: "approval", label: "Needs human approval" },
];

function readWorkspace(): BusinessWorkspace {
  if (typeof window === "undefined") return DEFAULT_WORKSPACE;
  try {
    const raw =
      window.localStorage.getItem(STORAGE_KEY) ??
      window.localStorage.getItem(LEGACY_STORAGE_KEY);
    if (!raw) return DEFAULT_WORKSPACE;
    const parsed = JSON.parse(raw) as Partial<BusinessWorkspace>;
    return {
      ...DEFAULT_WORKSPACE,
      ...parsed,
      priorities: normalizeList(parsed.priorities, DEFAULT_WORKSPACE.priorities),
      metrics: normalizeList(parsed.metrics, DEFAULT_WORKSPACE.metrics),
      metricTargets: Array.isArray(parsed.metricTargets)
        ? parsed.metricTargets.filter(isMetricTarget)
        : DEFAULT_WORKSPACE.metricTargets,
      actions: Array.isArray(parsed.actions)
        ? parsed.actions.filter(isAction)
        : DEFAULT_WORKSPACE.actions,
      decisions: Array.isArray(parsed.decisions)
        ? parsed.decisions.filter(isDecision)
        : DEFAULT_WORKSPACE.decisions,
      lastComplete: isLastComplete(parsed.lastComplete) ? parsed.lastComplete : null,
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

function isMetricTarget(value: unknown): value is BusinessMetricTarget {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return (
    typeof item.id === "string" &&
    typeof item.label === "string" &&
    typeof item.current === "number" &&
    Number.isFinite(item.current) &&
    typeof item.target === "number" &&
    Number.isFinite(item.target) &&
    typeof item.unit === "string"
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

function isLastComplete(value: unknown): value is LastComplete {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return typeof item.actionId === "string" && typeof item.decisionId === "string";
}

function persistWorkspace(workspace: BusinessWorkspace): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace));
}

function toWorkspaceBackup(workspace: BusinessWorkspace): WorkspaceBackup {
  return {
    schema: BACKUP_SCHEMA,
    version: BACKUP_VERSION,
    exportedAt: new Date().toISOString(),
    workspace,
  };
}

function parseWorkspaceBackup(raw: string): BusinessWorkspace | null {
  try {
    const parsed = JSON.parse(raw) as Partial<WorkspaceBackup>;
    if (parsed.schema !== BACKUP_SCHEMA || parsed.version !== BACKUP_VERSION) {
      return null;
    }
    if (!parsed.workspace || typeof parsed.workspace !== "object") return null;
    const candidate = parsed.workspace as Partial<BusinessWorkspace>;
    if (
      typeof candidate.mission !== "string" ||
      typeof candidate.offer !== "string" ||
      typeof candidate.audience !== "string" ||
      typeof candidate.northStar !== "string" ||
      typeof candidate.weeklyObjective !== "string" ||
      !Array.isArray(candidate.priorities) ||
      !Array.isArray(candidate.metrics) ||
      !Array.isArray(candidate.actions) ||
      !Array.isArray(candidate.decisions)
    ) {
      return null;
    }
    return {
      ...DEFAULT_WORKSPACE,
      mission: candidate.mission,
      offer: candidate.offer,
      audience: candidate.audience,
      northStar: candidate.northStar,
      weeklyObjective: candidate.weeklyObjective,
      priorities: normalizeList(candidate.priorities, DEFAULT_WORKSPACE.priorities),
      metrics: normalizeList(candidate.metrics, DEFAULT_WORKSPACE.metrics),
      metricTargets: Array.isArray(candidate.metricTargets)
        ? candidate.metricTargets.filter(isMetricTarget)
        : DEFAULT_WORKSPACE.metricTargets,
      actions: candidate.actions.filter(isAction),
      decisions: candidate.decisions.filter(isDecision),
      lastComplete: isLastComplete(candidate.lastComplete) ? candidate.lastComplete : null,
    };
  } catch {
    return null;
  }
}

function formatWhen(value: string): string {
  if (!value || value === "seed") return "Seed";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function todayLabel(): string {
  return new Date().toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function currentAccessUrl(): string {
  if (typeof window === "undefined") return "";
  return `${window.location.origin}${window.location.pathname}`;
}

function storageWritable(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const key = "jarvis.business.debug.check";
    window.localStorage.setItem(key, "ok");
    window.localStorage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

function collectBusinessDiagnostics(workspace: BusinessWorkspace): BusinessDiagnostics {
  const payload = JSON.stringify(workspace);
  return {
    generatedAt: new Date().toISOString(),
    currentUrl: currentAccessUrl(),
    storageWritable: storageWritable(),
    workspacePayloadBytes: payload.length,
    serviceWorkerSupport: typeof navigator !== "undefined" && "serviceWorker" in navigator,
    serviceWorkerControlled:
      typeof navigator !== "undefined" && Boolean(navigator.serviceWorker?.controller),
    cacheSupport: typeof window !== "undefined" && "caches" in window,
    userAgent: typeof navigator !== "undefined" ? navigator.userAgent : "unknown",
  };
}

function yesNo(value: boolean): string {
  return value ? "yes" : "no";
}

function buildReadinessChecks(
  diagnostics: BusinessDiagnostics,
  workspace: BusinessWorkspace,
  activePriorities: string[],
  openActions: BusinessAction[],
): ReadinessCheck[] {
  return [
    {
      label: "Storage writable",
      passed: diagnostics.storageWritable,
      detail: diagnostics.storageWritable ? "Local memory can persist" : "Browser storage blocked",
    },
    {
      label: "Workspace payload",
      passed: diagnostics.workspacePayloadBytes > 0,
      detail: `${diagnostics.workspacePayloadBytes} bytes`,
    },
    {
      label: "Service worker",
      passed: diagnostics.serviceWorkerSupport,
      detail: diagnostics.serviceWorkerControlled ? "Controlling page" : "Supported",
    },
    {
      label: "Cache API",
      passed: diagnostics.cacheSupport,
      detail: diagnostics.cacheSupport ? "Available" : "Unavailable",
    },
    {
      label: "Mission defined",
      passed: workspace.mission.trim().length > 0,
      detail: workspace.mission.trim() ? "Active mission present" : "Mission missing",
    },
    {
      label: "Active priorities limited",
      passed: activePriorities.length > 0 && activePriorities.length <= MAX_ACTIVE_PRIORITIES,
      detail: `${activePriorities.length}/${MAX_ACTIVE_PRIORITIES} active`,
    },
    {
      label: "Metrics defined",
      passed: workspace.metrics.length > 0,
      detail: `${workspace.metrics.length} metrics`,
    },
    {
      label: "Open action available",
      passed: openActions.length > 0,
      detail: `${openActions.length} open`,
    },
    {
      label: "Approval gate present",
      passed: workspace.actions.some((action) => action.risk === "approval"),
      detail: "Guarded execution is separated",
    },
    {
      label: "Receipts available",
      passed: workspace.decisions.length > 0,
      detail: `${workspace.decisions.length} receipts`,
    },
  ];
}

function buildDailyReview({
  workspace,
  activePriorities,
  openActions,
  nextAction,
  approvalActions,
  doneCount,
  totalCount,
}: {
  workspace: BusinessWorkspace;
  activePriorities: string[];
  openActions: BusinessAction[];
  nextAction: BusinessAction | null;
  approvalActions: BusinessAction[];
  doneCount: number;
  totalCount: number;
}): string {
  return [
    "# Daily Review",
    "",
    `Mission: ${workspace.mission}`,
    `Weekly objective: ${workspace.weeklyObjective}`,
    `Progress: ${doneCount}/${totalCount} completed`,
    `Open actions: ${openActions.length}`,
    `Approvals waiting: ${approvalActions.length}`,
    `Next action: ${nextAction?.title ?? "All clear for today"}`,
    "",
    "Active priorities:",
    ...activePriorities.map((priority, index) => `${index + 1}. ${priority}`),
    "",
    "Metrics to inspect:",
    ...workspace.metrics.map((metric) => `- ${metric}`),
  ].join("\n");
}

function buildCockpitReport({
  workspace,
  nextAction,
  approvalActions,
}: {
  workspace: BusinessWorkspace;
  nextAction: BusinessAction | null;
  approvalActions: BusinessAction[];
}): string {
  return [
    "# Business Cockpit Report",
    "",
    `Mission: ${workspace.mission}`,
    `Weekly objective: ${workspace.weeklyObjective}`,
    `Next action: ${nextAction?.title ?? "All clear for today"}`,
    `Approval queue: ${approvalActions.length}`,
    "",
    "Metric targets:",
    ...workspace.metricTargets.map((metric) => {
      const remaining = Math.max(metric.target - metric.current, 0);
      return `- ${metric.label}: ${metric.current}/${metric.target} ${metric.unit}, ${remaining} remaining`;
    }),
  ].join("\n");
}

function buildDebugReport(
  diagnostics: BusinessDiagnostics,
  workspace: BusinessWorkspace,
  readinessChecks: ReadinessCheck[],
): string {
  const passedChecks = readinessChecks.filter((check) => check.passed).length;
  return [
    "# Business OS Debug Report",
    "",
    `Generated at: ${diagnostics.generatedAt}`,
    `Readiness: ${passedChecks}/${readinessChecks.length}`,
    `Current URL: ${diagnostics.currentUrl}`,
    `Storage writable: ${yesNo(diagnostics.storageWritable)}`,
    `Workspace payload bytes: ${diagnostics.workspacePayloadBytes}`,
    `Service worker support: ${yesNo(diagnostics.serviceWorkerSupport)}`,
    `Service worker controlled: ${yesNo(diagnostics.serviceWorkerControlled)}`,
    `Cache API support: ${yesNo(diagnostics.cacheSupport)}`,
    `Actions: ${workspace.actions.length}`,
    `Receipts: ${workspace.decisions.length}`,
    `Priorities: ${workspace.priorities.length}`,
    `Metrics: ${workspace.metrics.length}`,
    `User agent: ${diagnostics.userAgent}`,
    "",
    "Readiness checks:",
    ...readinessChecks.map(
      (check) => `- ${check.label}: ${check.passed ? "pass" : "check"} (${check.detail})`,
    ),
  ].join("\n");
}

export function BusinessView() {
  const [workspace, setWorkspace] = useState<BusinessWorkspace>(() => readWorkspace());
  const [saved, setSaved] = useState(false);
  const [copyStatus, setCopyStatus] = useState<CopyStatus>("idle");
  const [showDone, setShowDone] = useState(false);
  const [showPlan, setShowPlan] = useState(false);
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [completeDraft, setCompleteDraft] = useState({ evidence: "", result: "" });
  const [backupDraft, setBackupDraft] = useState("");
  const [backupStatus, setBackupStatus] = useState<BackupStatus>("idle");
  const [priorityDraft, setPriorityDraft] = useState("");
  const [metricDraft, setMetricDraft] = useState("");
  const [actionDraft, setActionDraft] = useState("");
  const [actionRisk, setActionRisk] = useState<DecisionRisk>("low");
  const [diagnosticTick, setDiagnosticTick] = useState(0);
  const [hermesStatus, setHermesStatus] = useState<HermesStatus | null>(null);
  const [hermesProfiles, setHermesProfiles] = useState<HermesProfile[]>([]);
  const [hermesCapabilities, setHermesCapabilities] = useState<HermesCapability[]>([]);
  const [hermesExecutionEnabled, setHermesExecutionEnabled] = useState(false);
  const [hermesError, setHermesError] = useState("");
  const [handoffProfile, setHandoffProfile] = useState("kaizen7");
  const [handoffMessage, setHandoffMessage] = useState(
    "Focus today on the highest leverage action.",
  );
  const [handoffStatus, setHandoffStatus] = useState<HandoffStatus>("idle");
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

  useEffect(() => {
    if (typeof fetch !== "function") return;
    let cancelled = false;

    const loadHermes = async () => {
      try {
        const [statusResponse, profilesResponse, capabilitiesResponse] = await Promise.all([
          fetch("/api/kaizen7/hermes/status"),
          fetch("/api/kaizen7/hermes/profiles"),
          fetch("/api/kaizen7/hermes/capabilities"),
        ]);
        if (!statusResponse.ok || !profilesResponse.ok || !capabilitiesResponse.ok) {
          throw new Error("Hermes API unavailable");
        }
        const status = (await statusResponse.json()) as HermesStatus;
        const profilesPayload = (await profilesResponse.json()) as HermesProfilesPayload;
        const capabilitiesPayload =
          (await capabilitiesResponse.json()) as HermesCapabilitiesPayload;
        if (cancelled) return;
        const profiles = Array.isArray(profilesPayload.profiles)
          ? profilesPayload.profiles
          : [];
        setHermesStatus(status);
        setHermesProfiles(profiles);
        setHermesCapabilities(
          Array.isArray(capabilitiesPayload.capabilities)
            ? capabilitiesPayload.capabilities
            : [],
        );
        setHermesExecutionEnabled(Boolean(capabilitiesPayload.execution_enabled));
        setHermesError(status.error || profilesPayload.error || "");
        setHandoffProfile((current) => {
          if (profiles.some((profile) => profile.name === current)) return current;
          return profiles[0]?.name ?? "kaizen7";
        });
      } catch {
        if (!cancelled) setHermesError("Hermes API unavailable");
      }
    };

    void loadHermes();

    return () => {
      cancelled = true;
    };
  }, []);

  const activePriorities = useMemo(
    () => workspace.priorities.slice(0, MAX_ACTIVE_PRIORITIES),
    [workspace.priorities],
  );
  const parkedPriorities = useMemo(
    () => workspace.priorities.slice(MAX_ACTIVE_PRIORITIES),
    [workspace.priorities],
  );
  const openActions = useMemo(
    () => workspace.actions.filter((action) => !action.done),
    [workspace.actions],
  );
  const doneActions = useMemo(
    () => workspace.actions.filter((action) => action.done),
    [workspace.actions],
  );
  const nextAction = useMemo(
    () => openActions.find((action) => action.risk === "low") ?? openActions[0] ?? null,
    [openActions],
  );
  const approvalActions = useMemo(
    () => openActions.filter((action) => action.risk === "approval"),
    [openActions],
  );
  const doneCount = doneActions.length;
  const totalCount = workspace.actions.length;
  const diagnostics = useMemo(
    () => collectBusinessDiagnostics(workspace),
    [workspace, diagnosticTick],
  );
  const readinessChecks = useMemo(
    () => buildReadinessChecks(diagnostics, workspace, activePriorities, openActions),
    [diagnostics, workspace, activePriorities, openActions],
  );
  const passedReadinessChecks = readinessChecks.filter((check) => check.passed).length;

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

  const updateMetricTarget = (
    id: string,
    field: "current" | "target",
    rawValue: string,
  ) => {
    const parsed = Number.parseInt(rawValue, 10);
    const value = Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
    setWorkspace((current) => ({
      ...current,
      metricTargets: current.metricTargets.map((metric) =>
        metric.id === id ? { ...metric, [field]: value } : metric,
      ),
    }));
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

  const startComplete = (action: BusinessAction) => {
    if (action.risk === "approval" || action.done) return;
    setCompletingId(action.id);
    setCompleteDraft({ evidence: "", result: "" });
  };

  const saveComplete = (action: BusinessAction) => {
    if (action.risk === "approval") return;
    const evidence = completeDraft.evidence.trim();
    const result = completeDraft.result.trim();
    if (!evidence || !result) return;
    const decisionId = `action-${Date.now()}`;
    setWorkspace((current) => ({
      ...current,
      actions: current.actions.map((candidate) =>
        candidate.id === action.id ? { ...candidate, done: true } : candidate,
      ),
      decisions: [
        {
          id: decisionId,
          title: `Completed action: ${action.title}`,
          evidence,
          result,
          risk: "low",
          createdAt: new Date().toISOString(),
        },
        ...current.decisions,
      ],
      lastComplete: { actionId: action.id, decisionId },
    }));
    setCompletingId(null);
    setCompleteDraft({ evidence: "", result: "" });
  };

  const undoLastComplete = () => {
    const last = workspace.lastComplete;
    if (!last) return;
    setWorkspace((current) => ({
      ...current,
      actions: current.actions.map((action) =>
        action.id === last.actionId ? { ...action, done: false } : action,
      ),
      decisions: current.decisions.filter((decision) => decision.id !== last.decisionId),
      lastComplete: null,
    }));
    setCompletingId(null);
  };

  const writeClipboard = async (text: string): Promise<boolean> => {
    try {
      if (!navigator.clipboard?.writeText) {
        setCopyStatus("error");
        return false;
      }
      await navigator.clipboard.writeText(text);
      setCopyStatus("copied");
      window.setTimeout(() => setCopyStatus("idle"), 1800);
      return true;
    } catch {
      setCopyStatus("error");
      return false;
    }
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
      ...openActions.map(
        (action) =>
          `- ${action.title}${action.risk === "approval" ? " [approval required]" : ""}`,
      ),
      "",
      "Metrics:",
      ...workspace.metrics.map((metric) => `- ${metric}`),
    ].join("\n");
    await writeClipboard(briefing);
  };

  const copyDailyReview = async () => {
    await writeClipboard(
      buildDailyReview({
        workspace,
        activePriorities,
        openActions,
        nextAction,
        approvalActions,
        doneCount,
        totalCount,
      }),
    );
  };

  const copyCockpitReport = async () => {
    await writeClipboard(
      buildCockpitReport({
        workspace,
        nextAction,
        approvalActions,
      }),
    );
  };

  const copyDebugReport = async () => {
    await writeClipboard(buildDebugReport(diagnostics, workspace, readinessChecks));
  };

  const saveDailyReview = () => {
    const decisionId = `review-${Date.now()}`;
    setWorkspace((current) => ({
      ...current,
      decisions: [
        {
          id: decisionId,
          title: `Daily review: ${doneCount}/${totalCount} completed`,
          evidence: `Open actions: ${openActions.length}. Approvals waiting: ${approvalActions.length}.`,
          result: `Next action: ${nextAction?.title ?? "All clear for today"}.`,
          risk: "low",
          createdAt: new Date().toISOString(),
        },
        ...current.decisions,
      ],
    }));
  };

  const copyBackup = async () => {
    const backup = JSON.stringify(toWorkspaceBackup(workspace), null, 2);
    await writeClipboard(backup);
  };

  const copyMobileSetup = async () => {
    const accessUrl = currentAccessUrl();
    const instructions = [
      "# Mobile Access",
      "",
      `Current URL: ${accessUrl}`,
      "",
      "Android:",
      "1. Keep the desktop app running on this computer.",
      "2. Open the same URL from Chrome on the phone while both devices are on the same network.",
      "3. Use Add to Home screen when Chrome offers installation.",
      "",
      "Limits:",
      "- No cloud account is required.",
      "- The phone needs network access to the running local web app.",
      "- Business OS data is local to the browser unless you use Copy backup and Restore backup.",
    ].join("\n");
    await writeClipboard(instructions);
  };

  const restoreBackup = () => {
    const restored = parseWorkspaceBackup(backupDraft);
    if (!restored) {
      setBackupStatus("invalid");
      return;
    }
    setWorkspace(restored);
    setBackupDraft("");
    setBackupStatus("restored");
  };

  const copyForApproval = async (action: BusinessAction) => {
    const briefing = [
      "# Approval request",
      "",
      `Action: ${action.title}`,
      "Risk: needs human approval",
      `Mission: ${workspace.mission}`,
      "",
      "Business OS will not execute this. Approve outside the app, then record a receipt.",
    ].join("\n");
    await writeClipboard(briefing);
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

  const proposeHermesHandoff = async () => {
    const message = handoffMessage.trim();
    if (!message || typeof fetch !== "function") return;
    setHandoffStatus("saving");
    try {
      const response = await fetch("/api/kaizen7/hermes/chat/propose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile: handoffProfile,
          message,
        }),
      });
      if (!response.ok) throw new Error("Handoff proposal failed");
      setHandoffStatus("saved");
    } catch {
      setHandoffStatus("error");
    }
  };

  return (
    <div className="flex h-full flex-col">
      <ViewHeader
        icon={<BriefcaseBusiness className="h-4 w-4 text-primary" />}
        title="Business OS"
        subtitle="Today first. Evidence on complete. Human approval stays outside execution."
        right={
          <div className="flex items-center gap-2">
            <Button size="sm" variant="secondary" onClick={copyBriefing}>
              <Clipboard className="mr-1 h-4 w-4" />
              Copy briefing
            </Button>
            {copyStatus === "copied" && <Badge variant="default">Copied</Badge>}
            {copyStatus === "error" && (
              <Badge variant="destructive">Clipboard unavailable</Badge>
            )}
            <Badge variant={saved ? "default" : "outline"} className="gap-1">
              <Save className="h-3 w-3" />
              {saved ? "Saved locally" : "Local workspace"}
            </Badge>
          </div>
        }
      />

      <ScrollArea className="flex-1">
        <div className="grid gap-4 p-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
          <section className="space-y-4">
            <article className="card-outline border-primary/40 bg-primary/5 p-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary">
                {todayLabel()}
              </p>
              <p className="mt-2 text-base font-semibold leading-snug">{workspace.mission}</p>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                <Badge variant="outline">
                  {doneCount}/{totalCount} done
                </Badge>
                <span>{openActions.length} open</span>
              </div>
              {nextAction ? (
                <div className="mt-4 rounded-md border border-primary/40 bg-background/70 p-4">
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-primary">
                    Next
                  </div>
                  <h2 className="mt-1 text-lg font-semibold leading-snug">{nextAction.title}</h2>
                  <ActionControls
                    action={nextAction}
                    completingId={completingId}
                    completeDraft={completeDraft}
                    onStartComplete={startComplete}
                    onDraft={setCompleteDraft}
                    onSaveComplete={saveComplete}
                    onCancelComplete={() => setCompletingId(null)}
                    onCopyApproval={copyForApproval}
                  />
                </div>
              ) : (
                <p className="mt-4 text-sm text-muted-foreground">All clear for today.</p>
              )}
              {workspace.lastComplete && (
                <div className="mt-3">
                  <Button size="sm" variant="ghost" onClick={undoLastComplete}>
                    <RotateCcw className="mr-1 h-4 w-4" />
                    Undo last complete
                  </Button>
                </div>
              )}
            </article>

            <article className="card-outline p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Target className="h-4 w-4 text-primary" />
                  Start-to-finish flow
                </div>
                <Badge variant="outline">One loop</Badge>
              </div>
              <div className="grid gap-2 md:grid-cols-4">
                <FlowStep
                  icon={<Target className="h-4 w-4 text-primary" />}
                  label="Focus"
                  value={activePriorities[0] ?? "Define one priority"}
                />
                <FlowStep
                  icon={<CheckCircle2 className="h-4 w-4 text-primary" />}
                  label="Do"
                  value={nextAction?.title ?? "All clear for today"}
                />
                <FlowStep
                  icon={<ClipboardCheck className="h-4 w-4 text-primary" />}
                  label="Review"
                  value={`${doneCount} of ${totalCount} completed`}
                />
                <FlowStep
                  icon={<BadgeCheck className="h-4 w-4 text-primary" />}
                  label="Receipt"
                  value={`${workspace.decisions.length} saved receipts`}
                />
              </div>
            </article>

            <article className="card-outline p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  Business cockpit
                </div>
                <Badge variant="outline">Targets</Badge>
              </div>
              <div className="grid gap-2 md:grid-cols-3">
                {workspace.metricTargets.map((metric) => (
                  <MetricTargetRow
                    key={metric.id}
                    metric={metric}
                    onChange={updateMetricTarget}
                  />
                ))}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" onClick={copyCockpitReport}>
                  <Clipboard className="mr-1 h-4 w-4" />
                  Copy cockpit report
                </Button>
              </div>
            </article>

            <article className="card-outline p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <CircleAlert className="h-4 w-4 text-primary" />
                  Debug kit
                </div>
                <Badge variant="outline">
                  {passedReadinessChecks}/{readinessChecks.length} ready
                </Badge>
              </div>
              <div className="mb-3 rounded-md border border-primary/30 bg-primary/5 px-3 py-2">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold">10-point readiness</div>
                  <Badge variant="secondary">10 checks</Badge>
                </div>
              </div>
              <div className="grid gap-2 text-sm">
                {readinessChecks.map((check) => (
                  <DebugRow
                    key={check.label}
                    label={check.label}
                    value={check.detail}
                    ok={check.passed}
                  />
                ))}
              </div>
              <div className="mt-3 rounded-md border border-border/70 bg-background/50 px-3 py-2">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Current URL
                </div>
                <div className="mt-1 break-all font-mono text-xs text-muted-foreground">
                  {diagnostics.currentUrl}
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" onClick={copyDebugReport}>
                  <Clipboard className="mr-1 h-4 w-4" />
                  Copy debug report
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setDiagnosticTick((value) => value + 1)}
                >
                  <RotateCcw className="mr-1 h-4 w-4" />
                  Refresh diagnostics
                </Button>
              </div>
            </article>

            <article className="card-outline p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <ClipboardCheck className="h-4 w-4 text-primary" />
                  Daily review
                </div>
                <div className="flex flex-wrap justify-end gap-2">
                  <Badge variant="outline">
                    {doneCount}/{totalCount} completed
                  </Badge>
                  <Badge variant={approvalActions.length > 0 ? "destructive" : "secondary"}>
                    {approvalActions.length}{" "}
                    {approvalActions.length === 1 ? "approval" : "approvals"} waiting
                  </Badge>
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-md border border-border/70 bg-background/50 px-3 py-2">
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                    Next action
                  </div>
                  <div className="mt-1 text-sm font-medium">
                    {nextAction?.title ?? "All clear for today"}
                  </div>
                </div>
                <div className="rounded-md border border-border/70 bg-background/50 px-3 py-2">
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                    Active focus
                  </div>
                  <div className="mt-1 text-sm font-medium">
                    {activePriorities[0] ?? "Define one priority"}
                  </div>
                </div>
                <div className="rounded-md border border-border/70 bg-background/50 px-3 py-2">
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                    Metrics
                  </div>
                  <div className="mt-1 text-sm font-medium">{workspace.metrics.join(", ")}</div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" onClick={copyDailyReview}>
                  <Clipboard className="mr-1 h-4 w-4" />
                  Copy daily review
                </Button>
                <Button size="sm" onClick={saveDailyReview}>
                  <Save className="mr-1 h-4 w-4" />
                  Save daily review
                </Button>
              </div>
            </article>

            <article className="card-outline p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                  Daily execution
                </div>
                <Badge variant="outline">{openActions.length} open</Badge>
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
                <BrandedSelect
                  value={actionRisk}
                  onValueChange={(value) => setActionRisk(value as DecisionRisk)}
                  ariaLabel="Action risk"
                  options={ACTION_RISK_OPTIONS}
                  className="rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
                />
                <Button size="sm" onClick={addAction}>
                  <Plus className="mr-1 h-4 w-4" />
                  Add action
                </Button>
              </div>
              <ul className="mt-3 space-y-2">
                {openActions
                  .filter((action) => action.id !== nextAction?.id)
                  .map((action) => (
                  <li
                    key={action.id}
                    className="rounded-md border border-border/70 bg-card/40 px-3 py-2 text-sm"
                  >
                    <div className="flex items-start gap-2">
                      <span className="min-w-0 flex-1 pt-1">{action.title}</span>
                    </div>
                    <ActionControls
                      action={action}
                      completingId={completingId}
                      completeDraft={completeDraft}
                      onStartComplete={startComplete}
                      onDraft={setCompleteDraft}
                      onSaveComplete={saveComplete}
                      onCancelComplete={() => setCompletingId(null)}
                      onCopyApproval={copyForApproval}
                    />
                  </li>
                ))}
              </ul>
              {doneActions.length > 0 && (
                <div className="mt-3">
                  <Button size="sm" variant="ghost" onClick={() => setShowDone((value) => !value)}>
                    {showDone ? "Hide done" : `Show done (${doneActions.length})`}
                  </Button>
                  {showDone && (
                    <ul className="mt-2 space-y-2">
                      {doneActions.map((action) => (
                        <li
                          key={action.id}
                          className="flex items-center gap-2 rounded-md border border-border/50 px-3 py-2 text-sm text-muted-foreground line-through"
                        >
                          <span className="min-w-0 flex-1">{action.title}</span>
                          <Badge variant="secondary">Done</Badge>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
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
                <BrandedSelect
                  value={decisionDraft.risk}
                  onValueChange={(value) =>
                    setDecisionDraft((current) => ({
                      ...current,
                      risk: value as DecisionRisk,
                    }))
                  }
                  ariaLabel="Decision risk"
                  options={DECISION_RISK_OPTIONS}
                  className="rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
                />
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
                      <span className="text-xs text-muted-foreground">
                        {formatWhen(decision.createdAt)}
                      </span>
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
            <HermesRuntimePanel
              status={hermesStatus}
              profiles={hermesProfiles}
              capabilities={hermesCapabilities}
              executionEnabled={hermesExecutionEnabled}
              error={hermesError}
              handoffProfile={handoffProfile}
              handoffMessage={handoffMessage}
              handoffStatus={handoffStatus}
              onProfileChange={setHandoffProfile}
              onMessageChange={(value) => {
                setHandoffMessage(value);
                setHandoffStatus("idle");
              }}
              onProposeHandoff={proposeHermesHandoff}
            />

            <article className="card-outline border-primary/30 bg-primary/5 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Smartphone className="h-4 w-4 text-primary" />
                  Mobile access
                </div>
                <Badge variant="outline">Local-first</Badge>
              </div>
              <div className="grid gap-2 text-sm">
                <div className="flex items-center gap-2 rounded-md border border-border/70 bg-background/50 px-3 py-2">
                  <Download className="h-4 w-4 text-primary" />
                  <span className="min-w-0 flex-1">Installable PWA</span>
                  <Badge variant="secondary">Ready</Badge>
                </div>
                <div className="flex items-center gap-2 rounded-md border border-border/70 bg-background/50 px-3 py-2">
                  <Wifi className="h-4 w-4 text-primary" />
                  <span className="min-w-0 flex-1">Offline shell</span>
                  <Badge variant="secondary">Cached</Badge>
                </div>
              </div>
              <div className="mt-3 rounded-md border border-border/70 bg-background/50 px-3 py-2">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Current URL
                </div>
                <div className="mt-1 break-all font-mono text-xs text-muted-foreground">
                  {currentAccessUrl()}
                </div>
              </div>
              <Button size="sm" variant="secondary" className="mt-3" onClick={copyMobileSetup}>
                <Clipboard className="mr-1 h-4 w-4" />
                Copy mobile setup
              </Button>
            </article>

            <article className="card-outline p-4">
              <button
                type="button"
                className="mb-3 flex w-full items-center justify-between gap-3 text-left"
                onClick={() => setShowPlan((value) => !value)}
              >
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Target className="h-4 w-4 text-primary" />
                  Active mission
                </div>
                <span className="text-xs text-muted-foreground">
                  {showPlan ? "Hide plan" : "Edit plan"}
                </span>
              </button>
              {showPlan && (
                <>
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
                </>
              )}
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
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Clipboard className="h-4 w-4 text-primary" />
                  Workspace backup
                </div>
                {backupStatus === "restored" && <Badge variant="default">Restored</Badge>}
                {backupStatus === "invalid" && (
                  <Badge variant="destructive">Invalid backup</Badge>
                )}
              </div>
              <label className="block">
                <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Workspace backup JSON
                </span>
                <textarea
                  value={backupDraft}
                  rows={5}
                  onChange={(event) => {
                    setBackupDraft(event.target.value);
                    setBackupStatus("idle");
                  }}
                  aria-label="Workspace backup JSON"
                  className="w-full resize-none rounded-md border border-border bg-background/60 px-3 py-2 font-mono text-xs leading-relaxed outline-none transition-colors focus:border-primary/60"
                />
              </label>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" onClick={copyBackup}>
                  <Clipboard className="mr-1 h-4 w-4" />
                  Copy backup
                </Button>
                <Button size="sm" onClick={restoreBackup}>
                  Restore backup
                </Button>
              </div>
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

function HermesRuntimePanel({
  status,
  profiles,
  capabilities,
  executionEnabled,
  error,
  handoffProfile,
  handoffMessage,
  handoffStatus,
  onProfileChange,
  onMessageChange,
  onProposeHandoff,
}: {
  status: HermesStatus | null;
  profiles: HermesProfile[];
  capabilities: HermesCapability[];
  executionEnabled: boolean;
  error: string;
  handoffProfile: string;
  handoffMessage: string;
  handoffStatus: HandoffStatus;
  onProfileChange: (value: string) => void;
  onMessageChange: (value: string) => void;
  onProposeHandoff: () => void;
}) {
  const profileOptions = profiles.length
    ? profiles.map((profile) => ({ value: profile.name, label: profile.name }))
    : [{ value: "kaizen7", label: "kaizen7" }];
  const visibleCapabilities = capabilities.slice(0, 4);

  return (
    <article className="card-outline border-primary/40 bg-primary/5 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Bot className="h-4 w-4 text-primary" />
          Hermes runtime
        </div>
        <Badge variant={status?.installed ? "default" : "outline"}>
          {status?.installed ? "Connected" : "Checking"}
        </Badge>
      </div>

      <div className="grid gap-2 text-sm">
        <div className="rounded-md border border-border/70 bg-background/50 px-3 py-2">
          <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Runtime
          </div>
          <div className="mt-1 font-medium">
            {status?.version || (error ? "Hermes unavailable" : "Waiting for Hermes")}
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-border/70 bg-background/50 px-3 py-2">
          <span className="min-w-0 flex-1">Safety mode</span>
          <Badge variant={executionEnabled ? "destructive" : "secondary"}>
            {executionEnabled ? "Execution enabled" : "Proposal only"}
          </Badge>
        </div>
        <div className="rounded-md border border-border/70 bg-background/50 px-3 py-2">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="text-sm font-medium">Profiles</span>
            <Badge variant="outline">{profiles.length} profiles</Badge>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {profileOptions.map((profile) => (
              <Badge key={profile.value} variant="secondary">
                {profile.label}
              </Badge>
            ))}
          </div>
        </div>
        {visibleCapabilities.length > 0 && (
          <div className="rounded-md border border-border/70 bg-background/50 px-3 py-2">
            <div className="mb-2 text-sm font-medium">Capabilities</div>
            <div className="space-y-1.5">
              {visibleCapabilities.map((capability) => (
                <div key={capability.id} className="flex items-center gap-2">
                  <span className="min-w-0 flex-1">{capability.title}</span>
                  <Badge variant={capability.requires_approval ? "outline" : "secondary"}>
                    {capability.requires_approval ? "Approval" : "Read-only"}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="mt-3 space-y-2">
        <BrandedSelect
          value={handoffProfile}
          onValueChange={onProfileChange}
          ariaLabel="Hermes handoff profile"
          options={profileOptions}
          className="rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
        />
        <label className="block">
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Handoff
          </span>
          <textarea
            value={handoffMessage}
            rows={3}
            onChange={(event) => onMessageChange(event.target.value)}
            aria-label="Hermes handoff message"
            className="w-full resize-none rounded-md border border-border bg-background/60 px-3 py-2 text-sm leading-relaxed outline-none transition-colors focus:border-primary/60"
          />
        </label>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={onProposeHandoff}
            disabled={handoffStatus === "saving" || !handoffMessage.trim()}
          >
            <Send className="mr-1 h-4 w-4" />
            Propose handoff
          </Button>
          {handoffStatus === "saved" && <Badge variant="default">Handoff recorded</Badge>}
          {handoffStatus === "error" && (
            <Badge variant="destructive">Handoff failed</Badge>
          )}
        </div>
      </div>
      {error && <p className="mt-2 text-xs text-muted-foreground">{error}</p>}
    </article>
  );
}

function FlowStep({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="min-h-[92px] rounded-md border border-border/70 bg-background/50 px-3 py-3">
      <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {icon}
        {label}
      </div>
      <div className="mt-2 text-sm font-medium leading-snug">{value}</div>
    </div>
  );
}

function MetricTargetRow({
  metric,
  onChange,
}: {
  metric: BusinessMetricTarget;
  onChange: (id: string, field: "current" | "target", value: string) => void;
}) {
  const remaining = Math.max(metric.target - metric.current, 0);
  return (
    <div className="rounded-md border border-border/70 bg-background/50 px-3 py-3">
      <div className="flex items-center justify-between gap-2">
        <div className="text-sm font-semibold">{metric.label}</div>
        <Badge variant={remaining === 0 ? "default" : "outline"}>
          {remaining} remaining
        </Badge>
      </div>
      <div className="mt-2 text-lg font-semibold">
        {metric.current} / {metric.target}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <label>
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Current
          </span>
          <input
            type="number"
            min="0"
            value={metric.current}
            onChange={(event) => onChange(metric.id, "current", event.target.value)}
            aria-label={`Current ${metric.label}`}
            className="w-full rounded-md border border-border bg-background/60 px-2 py-1.5 text-sm"
          />
        </label>
        <label>
          <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Target
          </span>
          <input
            type="number"
            min="0"
            value={metric.target}
            onChange={(event) => onChange(metric.id, "target", event.target.value)}
            aria-label={`Target ${metric.label}`}
            className="w-full rounded-md border border-border bg-background/60 px-2 py-1.5 text-sm"
          />
        </label>
      </div>
      <div className="mt-2 text-xs text-muted-foreground">{metric.unit}</div>
    </div>
  );
}

function DebugRow({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-border/70 bg-background/50 px-3 py-2">
      <span className="min-w-0 flex-1">{label}</span>
      <Badge variant={ok ? "secondary" : "outline"}>{value}</Badge>
    </div>
  );
}

function ActionControls({
  action,
  completingId,
  completeDraft,
  onStartComplete,
  onDraft,
  onSaveComplete,
  onCancelComplete,
  onCopyApproval,
}: {
  action: BusinessAction;
  completingId: string | null;
  completeDraft: { evidence: string; result: string };
  onStartComplete: (action: BusinessAction) => void;
  onDraft: (value: { evidence: string; result: string }) => void;
  onSaveComplete: (action: BusinessAction) => void;
  onCancelComplete: () => void;
  onCopyApproval: (action: BusinessAction) => void;
}) {
  if (action.risk === "approval") {
    return (
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <Badge variant="destructive">Approval required</Badge>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onCopyApproval(action)}
          aria-label={`Copy for approval ${action.title}`}
        >
          Copy for approval
        </Button>
      </div>
    );
  }

  if (completingId === action.id) {
    const fieldsId = action.id;
    return (
      <div className="mt-3 space-y-2">
        <input
          value={completeDraft.evidence}
          onChange={(event) =>
            onDraft({ ...completeDraft, evidence: event.target.value })
          }
          placeholder="What did you actually do?"
          aria-label={`Action evidence ${fieldsId}`}
          className="w-full rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
        />
        <input
          value={completeDraft.result}
          onChange={(event) => onDraft({ ...completeDraft, result: event.target.value })}
          placeholder="What changed?"
          aria-label={`Action result ${fieldsId}`}
          className="w-full rounded-md border border-border bg-background/60 px-3 py-2 text-sm"
        />
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={() => onSaveComplete(action)}
            aria-label={`Save receipt ${action.title}`}
          >
            Save receipt
          </Button>
          <Button size="sm" variant="ghost" onClick={onCancelComplete}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-2">
      <Button
        size="sm"
        variant="secondary"
        onClick={() => onStartComplete(action)}
        aria-label={`Complete ${action.title}`}
      >
        Complete
      </Button>
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
