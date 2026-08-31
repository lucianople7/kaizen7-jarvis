/**
 * Modes — pick the character the assistant answers in, or build a new one.
 *
 * Two halves, in the order the decision actually gets made: the shelf you
 * choose from, and the workshop where you make another one. Switching applies
 * from the next turn in voice AND in chat, with no restart, because both brains
 * read the persona through one function on the backend.
 *
 * The workshop offers two ways in, because describing a personality out loud
 * and typing one are genuinely different tasks. "Talk it through" opens a real
 * voice conversation: the assistant interviews you and writes the mode itself
 * with its `save_mode` tool. The written path hands the same job to the chat.
 * Either way the mode lands in the same place and shows up on this screen.
 *
 * Colours come from theme tokens only, so the view is correct in light and dark
 * without a second palette to keep in step.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Mic, MicOff, Plus, RotateCcw, Sparkles, Trash2, Check } from "lucide-react";

import { ViewHeader } from "@/views/ChatsView";
import { useEventStore } from "@/store/events";
import { useVoiceCall } from "@/components/agentic/useVoiceCall";
import { BrandedSelect } from "@/components/ui/select";
import { sendChatMessage } from "@/lib/chat";
import { cn } from "@/lib/utils";
import {
  activateMode,
  deleteMode,
  fetchModes,
  restoreBuiltin,
  saveMode,
  type AssistantMode,
  type ModesState,
  type Proactivity,
  type Verbosity,
} from "@/lib/modesApi";

/**
 * What the assistant is told when the user asks for an interview.
 *
 * Deliberately an instruction to ASK rather than to produce: handed "build me a
 * friendly mode", a model writes one immediately and the user gets whatever it
 * guessed. The point of the interview is that the questions surface the things
 * people do not think to say — whether they want to be disagreed with, what the
 * assistant should never do, how it should open a conversation.
 */
const INTERVIEW_BRIEF =
  "I want to create a new assistant mode — a character for you to answer in. " +
  "Interview me first: ask me one question at a time about how you should " +
  "behave. How should you greet me? Should you have opinions and disagree with " +
  "me? How long should your answers be? Should you ask about my day, or stay " +
  "on the task? What should you never do? When you have enough, read the mode " +
  "back to me in a sentence and save it with the save_mode tool.";

const VERBOSITY_LABELS: Record<Verbosity, string> = {
  brief: "Short answers",
  normal: "Normal length",
  rich: "Explains the reasoning",
};

const PROACTIVITY_LABELS: Record<Proactivity, string> = {
  reactive: "Answers only what was asked",
  normal: "Balanced",
  forward: "Thinks a step ahead",
};

type JarvisTone = "executive" | "warm" | "direct" | "strict";
type JarvisEnergy = "focused" | "calm" | "high";
type PersonalCore = {
  mission: string;
  owner: string;
  focus: string;
  tone: JarvisTone;
  energy: JarvisEnergy;
  guardrails: string;
  priorityLimit: number;
};

const JARVIS_TONE_OPTIONS = [
  { value: "executive", label: "Executive" },
  { value: "warm", label: "Warm" },
  { value: "direct", label: "Direct" },
  { value: "strict", label: "Strict" },
] as const;

const JARVIS_ENERGY_OPTIONS = [
  { value: "focused", label: "Focused" },
  { value: "calm", label: "Calm" },
  { value: "high", label: "High focus" },
] as const;

const JARVIS_TONE_COPY = {
  executive: {
    name: "Jarvis Personal Operator",
    description: "Executive personal operating mode",
    voice:
      "Operate like a concise chief of staff: clear priorities, sharp tradeoffs, no theatrical filler.",
  },
  warm: {
    name: "Jarvis Steady Companion",
    description: "Warm operating mode for calm clarity and humane momentum.",
    voice:
      "Stay warm, steady and direct. Help Luciano feel oriented without losing operational edge.",
  },
  direct: {
    name: "Jarvis Precision Driver",
    description: "Direct operating mode for blunt decisions and fast execution.",
    voice:
      "Be blunt, concise and evidence-led. Cut ambiguity and name the next concrete move.",
  },
  strict: {
    name: "Jarvis Mission Governor",
    description: "Strict operating mode for narrow priorities and hard execution gates.",
    voice:
      "Be strict about scope, proof and irreversible actions. Challenge drift before helping with it.",
  },
} satisfies Record<JarvisTone, { name: string; description: string; voice: string }>;

const JARVIS_ENERGY_COPY = {
  focused: {
    verbosity: "normal" as Verbosity,
    proactivity: "normal" as Proactivity,
    voice: "Keep one active mission visible. Limit priorities before adding work.",
  },
  calm: {
    verbosity: "brief" as Verbosity,
    proactivity: "reactive" as Proactivity,
    voice: "Slow the pace down. Reduce options. Ask before widening scope.",
  },
  high: {
    verbosity: "normal" as Verbosity,
    proactivity: "forward" as Proactivity,
    voice:
      "Drive the day with urgency, but keep the mission narrow and approval gates intact.",
  },
} satisfies Record<JarvisEnergy, { verbosity: Verbosity; proactivity: Proactivity; voice: string }>;

const EMPTY_DRAFT = {
  name: "",
  emoji: "",
  description: "",
  character: "",
  verbosity: "normal" as Verbosity,
  proactivity: "normal" as Proactivity,
};

const verbosityOptions = (values: readonly Verbosity[] = []) =>
  values.map((value) => ({
    value,
    label: VERBOSITY_LABELS[value],
  }));

const proactivityOptions = (values: readonly Proactivity[] = []) =>
  values.map((value) => ({
    value,
    label: PROACTIVITY_LABELS[value],
  }));

const DEFAULT_APPROVAL_BOUNDARY =
  "Human approval is required before publishing, payments, messages, credentials, financial operations, external sends, destructive changes, or irreversible actions.";

function buildPersonalJarvisDraft(core: PersonalCore) {
  const tone = JARVIS_TONE_COPY[core.tone];
  const energy = JARVIS_ENERGY_COPY[core.energy];
  const owner = core.owner.trim() || "Luciano";
  const mission = core.mission.trim();
  const focus = core.focus.trim();
  const guardrails =
    core.guardrails.trim() ||
    "Never publish, pay, message, change credentials, operate money, or make irreversible changes without explicit approval.";

  return {
    name: tone.name,
    emoji: "K7",
    description: `${tone.description} for ${owner} with one active focus.`,
    character: [
      tone.voice,
      energy.voice,
      `Owner: ${owner}`,
      `Mission: ${mission}`,
      `Active focus: ${focus}`,
      `Priority cap: keep at most ${core.priorityLimit} active priorities visible.`,
      `Guardrails: ${guardrails}`,
      "Always separate recommendation from execution.",
      DEFAULT_APPROVAL_BOUNDARY,
      "Every answer should end with the smallest useful next action when action is needed.",
    ].join("\n\n"),
    verbosity: energy.verbosity,
    proactivity: energy.proactivity,
  };
}

export function ModesView() {
  const pushToast = useEventStore((s) => s.pushToast);
  const setActiveSection = useEventStore((s) => s.setActiveSection);
  const { active: voiceLive, busy: voiceBusy, connecting, toggleCall } = useVoiceCall();

  const [state, setState] = useState<ModesState | null>(null);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState("");
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [saving, setSaving] = useState(false);
  const [written, setWritten] = useState("");
  const draftNameRef = useRef<HTMLInputElement>(null);
  const missionRef = useRef<HTMLTextAreaElement>(null);
  const focusRef = useRef<HTMLInputElement>(null);
  const priorityRef = useRef<HTMLInputElement>(null);
  const [personalCore, setPersonalCore] = useState<PersonalCore>({
    mission: "",
    owner: "Luciano",
    focus: "",
    tone: "executive" as JarvisTone,
    energy: "focused" as JarvisEnergy,
    guardrails: "",
    priorityLimit: 3,
  });

  const refresh = useCallback(async () => {
    try {
      setState(await fetchModes());
    } catch {
      // Backend still warming, or headless. Keep whatever we had: blanking the
      // shelf on a hiccup would claim the user has no modes, which is a claim
      // about their setup rather than about this one failed read.
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  /*
   * While a voice interview is running, watch for the mode it creates.
   *
   * The assistant saves through its own tool, not through this screen, so there
   * is no response here to react to. Polling is confined to exactly that window
   * — a call in progress — rather than running for the whole session, which is
   * how a background refresh quietly becomes a per-second request forever.
   */
  useEffect(() => {
    if (!voiceLive) return;
    const timer = setInterval(() => void refresh(), 4000);
    return () => clearInterval(timer);
  }, [voiceLive, refresh]);

  const modes = useMemo(() => state?.modes ?? [], [state]);
  const override = state?.section_override ?? "";

  const choose = async (slug: string) => {
    setSwitching(slug);
    try {
      setState(await activateMode(slug));
    } catch (e) {
      pushToast("error", (e as Error).message);
    } finally {
      setSwitching("");
    }
  };

  const remove = async (mode: AssistantMode) => {
    try {
      setState(mode.built_in ? await restoreBuiltin(mode.slug) : await deleteMode(mode.slug));
      pushToast("success", mode.built_in ? `${mode.name} restored.` : `${mode.name} deleted.`);
    } catch (e) {
      pushToast("error", (e as Error).message);
    }
  };

  const create = async () => {
    if (!draft.name.trim() || !draft.character.trim()) {
      pushToast("warning", "A mode needs a name and a description of how it behaves.");
      return;
    }
    setSaving(true);
    try {
      setState(await saveMode(draft));
      pushToast("success", `${draft.name} saved.`);
      setDraft(EMPTY_DRAFT);
    } catch (e) {
      pushToast("error", (e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const buildPersonalCore = () => {
    if (!personalCore.mission.trim() || !personalCore.focus.trim()) {
      pushToast(
        "warning",
        "Jarvis needs a mission and active focus before it can become operational.",
      );
      if (!personalCore.mission.trim()) missionRef.current?.focus();
      else focusRef.current?.focus();
      return;
    }
    if (personalCore.priorityLimit < 1 || personalCore.priorityLimit > 5) {
      pushToast("warning", "Jarvis keeps one to five active priorities. Set a tighter cap.");
      priorityRef.current?.focus();
      return;
    }
    setDraft(buildPersonalJarvisDraft(personalCore));
    draftNameRef.current?.focus();
    pushToast("info", "Jarvis Personal Core ready. Review it, then save the mode.");
  };

  const startInterview = async () => {
    // Ending a call needs no brief — only the opening of one does.
    if (!voiceLive) pushToast("info", "Say what kind of assistant you want. I'll ask the rest.");
    await toggleCall();
  };

  const describeInWriting = async () => {
    const text = written.trim();
    if (!text) return;
    const sent = await sendChatMessage(`${INTERVIEW_BRIEF}\n\nTo start: ${text}`);
    if (!sent) {
      pushToast("error", "The chat connection is not up yet.");
      return;
    }
    setWritten("");
    // The conversation happens in Chats, so go where the answer will appear
    // rather than leaving the user watching a screen that will not change.
    setActiveSection("chats");
  };

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <ViewHeader
        icon={<Sparkles className="h-4 w-4 text-muted-foreground" />}
        title="Modes"
        subtitle="How the assistant behaves. Applies to voice and chat from the next turn."
      />

      {loading ? (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="flex flex-col gap-8 px-6 py-6">
          {override && (
            <p className="rounded-lg border border-border bg-secondary/40 px-4 py-3 text-sm text-muted-foreground">
              The <span className="font-medium text-foreground">{override}</span> mode is in force
              while that section is open. Your own choice comes back when you leave it.
            </p>
          )}

          <section className="flex flex-col gap-3">
            <h3 className="font-display text-sm font-semibold tracking-tight">Your modes</h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {modes.map((mode) => {
                const isActive = mode.slug === state?.active;
                return (
                  <button
                    key={mode.slug}
                    type="button"
                    onClick={() => void choose(mode.slug)}
                    disabled={switching !== ""}
                    aria-pressed={isActive}
                    data-testid={`mode-card-${mode.slug}`}
                    className={cn(
                      "group relative flex flex-col gap-2 rounded-xl border p-4 text-left transition-colors",
                      isActive
                        ? "border-primary bg-primary/10"
                        : "border-border bg-secondary/30 hover:bg-secondary/60",
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg leading-none">{mode.emoji || "•"}</span>
                      <span className="font-medium">{mode.name}</span>
                      {isActive && <Check className="ml-auto h-4 w-4 text-primary" />}
                      {switching === mode.slug && (
                        <Loader2 className="ml-auto h-4 w-4 animate-spin text-muted-foreground" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{mode.description}</p>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{VERBOSITY_LABELS[mode.verbosity]}</span>
                      <span aria-hidden>·</span>
                      <span>{PROACTIVITY_LABELS[mode.proactivity]}</span>
                    </div>
                    {/*
                      Built-ins offer "restore", user modes offer "delete" — the
                      same button position, because to the user both mean "undo
                      what I did to this card".
                    */}
                    <span
                      role="button"
                      tabIndex={0}
                      aria-label={mode.built_in ? `Restore ${mode.name}` : `Delete ${mode.name}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        void remove(mode);
                      }}
                      onKeyDown={(e) => {
                        if (e.key !== "Enter" && e.key !== " ") return;
                        e.stopPropagation();
                        e.preventDefault();
                        void remove(mode);
                      }}
                      className="absolute right-3 top-3 hidden rounded p-1 text-muted-foreground hover:bg-destructive/20 hover:text-destructive group-hover:block"
                    >
                      {mode.built_in ? (
                        <RotateCcw className="h-3.5 w-3.5" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="flex flex-col gap-4">
            <div>
              <h3 className="font-display text-sm font-semibold tracking-tight">Build a mode</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Describe the assistant you want and let it write the mode, or fill it in yourself.
              </p>
            </div>

            <article className="flex flex-col gap-4 rounded-xl border border-primary/30 bg-primary/5 p-4">
              <div className="flex flex-col gap-1">
                <h4 className="font-display text-sm font-semibold tracking-tight">
                  Jarvis Personal Core
                </h4>
                <p className="text-sm text-muted-foreground">
                  Build a ready-to-save personal operating mode with focus, priorities and approval gates.
                </p>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <label className="flex flex-col gap-1 text-xs font-medium text-muted-foreground">
                  Assistant mission
                  <textarea
                    ref={missionRef}
                    aria-label="Assistant mission"
                    value={personalCore.mission}
                    onChange={(e) =>
                      setPersonalCore({ ...personalCore, mission: e.target.value })
                    }
                    rows={3}
                    placeholder="Keep Luciano focused on one business move at a time"
                    className="resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                  />
                </label>
                <label className="flex flex-col gap-1 text-xs font-medium text-muted-foreground">
                  Approval boundaries
                  <textarea
                    aria-label="Approval boundaries"
                    value={personalCore.guardrails}
                    onChange={(e) =>
                      setPersonalCore({ ...personalCore, guardrails: e.target.value })
                    }
                    rows={3}
                    placeholder="Never publish, pay or message without approval"
                    className="resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                  />
                </label>
                <label className="flex flex-col gap-1 text-xs font-medium text-muted-foreground">
                  Owner
                  <input
                    aria-label="Owner"
                    value={personalCore.owner}
                    onChange={(e) =>
                      setPersonalCore({ ...personalCore, owner: e.target.value })
                    }
                    placeholder="Luciano"
                    className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                  />
                </label>
                <label className="flex flex-col gap-1 text-xs font-medium text-muted-foreground">
                  Active focus
                  <input
                    ref={focusRef}
                    aria-label="Active focus"
                    value={personalCore.focus}
                    onChange={(e) =>
                      setPersonalCore({ ...personalCore, focus: e.target.value })
                    }
                    placeholder="Build a clean PersonalJarvis product"
                    className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                  />
                </label>
                <div className="flex flex-col gap-1 text-xs font-medium text-muted-foreground">
                  Jarvis tone
                  <BrandedSelect
                    value={personalCore.tone}
                    onValueChange={(value) =>
                      setPersonalCore({ ...personalCore, tone: value as JarvisTone })
                    }
                    ariaLabel="Jarvis tone"
                    options={JARVIS_TONE_OPTIONS}
                    className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                  />
                </div>
                <div className="flex flex-col gap-1 text-xs font-medium text-muted-foreground">
                  Jarvis energy
                  <BrandedSelect
                    value={personalCore.energy}
                    onValueChange={(value) =>
                      setPersonalCore({ ...personalCore, energy: value as JarvisEnergy })
                    }
                    ariaLabel="Jarvis energy"
                    options={JARVIS_ENERGY_OPTIONS}
                    className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                  />
                </div>
                <label className="flex flex-col gap-1 text-xs font-medium text-muted-foreground">
                  Max active priorities
                  <input
                    ref={priorityRef}
                    aria-label="Max active priorities"
                    type="number"
                    min={1}
                    max={5}
                    value={personalCore.priorityLimit}
                    onChange={(e) =>
                      setPersonalCore({
                        ...personalCore,
                        priorityLimit: Number(e.target.value),
                      })
                    }
                    className="rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                  />
                </label>
              </div>
              <button
                type="button"
                onClick={buildPersonalCore}
                className="self-start rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
              >
                Build personal Jarvis
              </button>
            </article>

            <div className="grid gap-4 lg:grid-cols-2">
              <div className="flex flex-col gap-3 rounded-xl border border-border bg-secondary/30 p-4">
                <button
                  type="button"
                  onClick={() => void startInterview()}
                  disabled={voiceBusy || connecting}
                  data-testid="mode-interview-button"
                  className={cn(
                    "flex items-center justify-center gap-2 rounded-lg px-4 py-3 font-medium transition-colors",
                    voiceLive
                      ? "bg-destructive/15 text-destructive hover:bg-destructive/25"
                      : "bg-primary text-primary-foreground hover:opacity-90",
                    (voiceBusy || connecting) && "opacity-60",
                  )}
                >
                  {connecting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : voiceLive ? (
                    <MicOff className="h-4 w-4" />
                  ) : (
                    <Mic className="h-4 w-4" />
                  )}
                  {voiceLive ? "End the conversation" : "Talk it through"}
                </button>
                <p className="text-sm text-muted-foreground">
                  {voiceLive
                    ? "Listening. Describe the assistant you want — it will ask the rest and save the mode when you agree."
                    : "Opens a voice conversation. It interviews you, then writes the mode itself."}
                </p>

                <div className="mt-2 flex flex-col gap-2 border-t border-border pt-3">
                  <label className="text-xs font-medium text-muted-foreground" htmlFor="mode-written">
                    Rather type it?
                  </label>
                  <textarea
                    id="mode-written"
                    value={written}
                    onChange={(e) => setWritten(e.target.value)}
                    rows={3}
                    placeholder="A version of you that is blunt and never softens bad news…"
                    className="resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                  />
                  <button
                    type="button"
                    onClick={() => void describeInWriting()}
                    disabled={!written.trim()}
                    className="self-start rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-secondary/60 disabled:opacity-50"
                  >
                    Ask in chat
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-3 rounded-xl border border-border bg-secondary/30 p-4">
                <div className="flex gap-2">
                  <input
                    aria-label="Emoji"
                    value={draft.emoji}
                    onChange={(e) => setDraft({ ...draft, emoji: e.target.value })}
                    placeholder="🦉"
                    className="w-16 rounded-lg border border-border bg-background px-3 py-2 text-center text-sm outline-none focus:border-primary"
                  />
                  <input
                    aria-label="Mode name"
                    ref={draftNameRef}
                    value={draft.name}
                    onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                    placeholder="Night Owl"
                    className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                  />
                </div>
                <input
                  aria-label="One-line description"
                  value={draft.description}
                  onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                  placeholder="Quiet and short. Refuses to start new work late."
                  className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                />
                <textarea
                  aria-label="How it behaves"
                  value={draft.character}
                  onChange={(e) => setDraft({ ...draft, character: e.target.value })}
                  rows={5}
                  placeholder="Speak quietly. It is late and I am winding down…"
                  className="resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                />
                <div className="flex flex-wrap gap-2">
                  <BrandedSelect
                    value={draft.verbosity}
                    onValueChange={(value) =>
                      setDraft({ ...draft, verbosity: value as Verbosity })
                    }
                    ariaLabel="Answer length"
                    options={verbosityOptions(state?.verbosities)}
                    className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                  />
                  <BrandedSelect
                    value={draft.proactivity}
                    onValueChange={(value) =>
                      setDraft({ ...draft, proactivity: value as Proactivity })
                    }
                    ariaLabel="How much it volunteers"
                    options={proactivityOptions(state?.proactivities)}
                    className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => void create()}
                  disabled={saving}
                  data-testid="mode-save-button"
                  className="flex items-center justify-center gap-2 self-start rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
                >
                  {saving ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                  Save mode
                </button>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
