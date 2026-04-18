import { useState, useEffect, useRef } from "react";
import { Save, Plus, Trash2, Check, ChevronDown, ChevronRight } from "lucide-react";
import { fetchConfig, saveConfig, fetchAvailablePrompts } from "../api";
import type { AppConfig, WatchlistEntryConfig, IndicatorConfig, PromptRef } from "../types";

// ── Shared primitives ──────────────────────────────────────────────────────────

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      className={`relative h-5 w-9 flex-shrink-0 rounded-full transition-colors focus:outline-none ${enabled ? "bg-cyan-400" : "bg-terminal-border"
        }`}
    >
      <span
        className={`absolute left-0 top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${enabled ? "translate-x-[1.125rem]" : "translate-x-0.5"
          }`}
      />
    </button>
  );
}

function NumInput({
  label,
  value,
  onChange,
  min = 0,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  step?: number;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] uppercase tracking-wider text-terminal-muted">{label}</label>
      <input
        type="number"
        value={value}
        min={min}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full rounded border border-terminal-border bg-terminal-bg px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-400/50"
      />
    </div>
  );
}

// ── Interval presets ───────────────────────────────────────────────────────────

type IntervalUnit = "seconds" | "minutes" | "hours" | "days";

const INTERVAL_PRESETS: { label: string; unit: IntervalUnit; value: number }[] = [
  { label: "5s", unit: "seconds", value: 5 },
  { label: "15s", unit: "seconds", value: 15 },
  { label: "30s", unit: "seconds", value: 30 },
  { label: "5m", unit: "minutes", value: 5 },
  { label: "15m", unit: "minutes", value: 15 },
  { label: "1h", unit: "hours", value: 1 },
  { label: "4h", unit: "hours", value: 4 },
  { label: "1d", unit: "days", value: 1 },
];

/** Return the active {unit, value} for an entry, falling back to 1 hour. */
function activeInterval(entry: WatchlistEntryConfig): { unit: IntervalUnit; value: number } {
  if (entry.interval_seconds != null) return { unit: "seconds", value: entry.interval_seconds };
  if (entry.interval_minutes != null) return { unit: "minutes", value: entry.interval_minutes };
  if (entry.interval_hours != null) return { unit: "hours", value: entry.interval_hours };
  if (entry.interval_days != null) return { unit: "days", value: entry.interval_days };
  return { unit: "hours", value: 1 };
}

/** Set one interval field and clear all others. */
function setInterval(unit: IntervalUnit, value: number): Partial<WatchlistEntryConfig> {
  return {
    interval_seconds: unit === "seconds" ? value : null,
    interval_minutes: unit === "minutes" ? value : null,
    interval_hours: unit === "hours" ? value : null,
    interval_days: unit === "days" ? value : null,
  };
}



// ── Per-entry indicator section ────────────────────────────────────────────────

function IndicatorSection({
  ind,
  onChange,
}: {
  ind: IndicatorConfig;
  onChange: (patch: Partial<IndicatorConfig>) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded border border-terminal-border/50">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-[10px] uppercase tracking-wider text-terminal-muted hover:text-slate-300 transition-colors"
      >
        <span>Indicators</span>
        {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
      </button>

      {open && (
        <div className="border-t border-terminal-border/50 px-3 pb-3 pt-2 space-y-3">
          {/* SMA — always on */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-cyan-400/80">SMA (always on)</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <NumInput
                label="Short period"
                value={ind.sma.short_period}
                onChange={(v) => onChange({ sma: { ...ind.sma, short_period: v } })}
                min={1}
              />
              <NumInput
                label="Long period"
                value={ind.sma.long_period}
                onChange={(v) => onChange({ sma: { ...ind.sma, long_period: v } })}
                min={1}
              />
            </div>
          </div>

          {/* RSI */}
          <div className={!ind.rsi.enabled ? "opacity-60" : ""}>
            <div className="mb-2 flex items-center gap-2">
              <Toggle enabled={ind.rsi.enabled} onChange={(v) => onChange({ rsi: { ...ind.rsi, enabled: v } })} />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-300">RSI</span>
            </div>
            {ind.rsi.enabled && (
              <div className="grid grid-cols-2 gap-2">
                <NumInput label="Period" value={ind.rsi.period} onChange={(v) => onChange({ rsi: { ...ind.rsi, period: v } })} min={1} />
                <NumInput label="Oversold" value={ind.rsi.oversold} onChange={(v) => onChange({ rsi: { ...ind.rsi, oversold: v } })} step={0.5} />
                <NumInput label="Overbought" value={ind.rsi.overbought} onChange={(v) => onChange({ rsi: { ...ind.rsi, overbought: v } })} step={0.5} />
              </div>
            )}
          </div>

          {/* MACD */}
          <div className={!ind.macd.enabled ? "opacity-60" : ""}>
            <div className="mb-2 flex items-center gap-2">
              <Toggle enabled={ind.macd.enabled} onChange={(v) => onChange({ macd: { ...ind.macd, enabled: v } })} />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-300">MACD</span>
            </div>
            {ind.macd.enabled && (
              <div className="grid grid-cols-2 gap-2">
                <NumInput label="Fast EMA" value={ind.macd.fast} onChange={(v) => onChange({ macd: { ...ind.macd, fast: v } })} min={1} />
                <NumInput label="Slow EMA" value={ind.macd.slow} onChange={(v) => onChange({ macd: { ...ind.macd, slow: v } })} min={1} />
                <NumInput label="Signal" value={ind.macd.signal} onChange={(v) => onChange({ macd: { ...ind.macd, signal: v } })} min={1} />
              </div>
            )}
          </div>

          {/* Bollinger Bands */}
          <div className={!ind.bb.enabled ? "opacity-60" : ""}>
            <div className="mb-2 flex items-center gap-2">
              <Toggle enabled={ind.bb.enabled} onChange={(v) => onChange({ bb: { ...ind.bb, enabled: v } })} />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-300">Bollinger Bands</span>
            </div>
            {ind.bb.enabled && (
              <div className="grid grid-cols-2 gap-2">
                <NumInput label="Period" value={ind.bb.period} onChange={(v) => onChange({ bb: { ...ind.bb, period: v } })} min={1} />
                <NumInput label="Std Dev" value={ind.bb.std} onChange={(v) => onChange({ bb: { ...ind.bb, std: v } })} min={1} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Watchlist entry card ───────────────────────────────────────────────────────

function EntryCard({
  entry,
  onChange,
  onRemove,
  availablePrompts,
}: {
  entry: WatchlistEntryConfig;
  onChange: (patch: Partial<WatchlistEntryConfig>) => void;
  onRemove: () => void;
  availablePrompts: PromptRef[];
}) {
  const promptKey = (p: PromptRef) => `${p.file}:${p.name}`;
  const isPromptSelected = (p: PromptRef) => entry.prompts.some((ep) => promptKey(ep) === promptKey(p));

  const togglePrompt = (p: PromptRef) => {
    const selected = isPromptSelected(p);
    if (selected && entry.prompts.length === 1) return; // keep at least one
    onChange({
      prompts: selected
        ? entry.prompts.filter((ep) => promptKey(ep) !== promptKey(p))
        : [...entry.prompts, p],
    });
  };

  return (
    <div
      className={`rounded-lg border p-4 space-y-3 transition-opacity ${entry.enabled ? "border-terminal-border" : "border-terminal-border/40 opacity-80"
        }`}
    >
      {/* Row 1: toggle + name + delete */}
      <div className="flex items-center gap-3">
        <Toggle enabled={entry.enabled} onChange={(v) => onChange({ enabled: v })} />
        <input
          value={entry.name}
          onChange={(e) => onChange({ name: e.target.value })}
          placeholder="Group name"
          className="flex-1 rounded border border-terminal-border bg-terminal-bg px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-400/50"
        />
        <button
          type="button"
          onClick={onRemove}
          className="text-terminal-muted transition-colors hover:text-red-400"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Row 2: symbols */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase tracking-wider text-terminal-muted">
          Symbols — comma-separated
        </label>
        <input
          value={entry.symbols.join(", ")}
          onChange={(e) =>
            onChange({
              symbols: e.target.value
                .split(",")
                .map((s) => s.trim().toUpperCase())
                .filter(Boolean),
            })
          }
          placeholder="AAPL, MSFT, TSLA"
          className="rounded border border-terminal-border bg-terminal-bg px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-400/50"
        />
      </div>

      {/* Row 3: interval */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase tracking-wider text-terminal-muted">Interval</label>
        <div className="flex items-center gap-1.5 flex-wrap">
          {/* presets */}
          {INTERVAL_PRESETS.map((p) => {
            const active = activeInterval(entry);
            const isActive = active.unit === p.unit && active.value === p.value;
            return (
              <button
                key={`${p.unit}-${p.value}`}
                type="button"
                onClick={() => onChange(setInterval(p.unit, p.value))}
                className={`rounded px-1.5 py-0.5 text-[10px] transition-colors ${isActive
                    ? "bg-cyan-400/20 text-cyan-400"
                    : "bg-terminal-border text-terminal-muted hover:text-slate-300"
                  }`}
              >
                {p.label}
              </button>
            );
          })}
          {/* custom numeric + unit selector */}
          <span className="text-terminal-muted/40 text-[10px]">or</span>
          <input
            type="number"
            min={1}
            value={activeInterval(entry).value}
            onChange={(e) => onChange(setInterval(activeInterval(entry).unit, Number(e.target.value)))}
            className="w-14 rounded border border-terminal-border bg-terminal-bg px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-400/50"
          />
          <select
            value={activeInterval(entry).unit}
            onChange={(e) => onChange(setInterval(e.target.value as IntervalUnit, activeInterval(entry).value))}
            className="rounded border border-terminal-border bg-terminal-bg px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-400/50"
          >
            <option value="seconds">sec</option>
            <option value="minutes">min</option>
            <option value="hours">hr</option>
            <option value="days">day</option>
          </select>
        </div>
      </div>

      {/* Row 4: LLM toggle */}
      <div className="flex items-center gap-2">
        <Toggle enabled={entry.include_llm} onChange={(v) => onChange({ include_llm: v })} />
        <span className="text-[10px] uppercase tracking-wider text-terminal-muted">LLM</span>
      </div>

      {/* Row 4: prompts */}
      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase tracking-wider text-terminal-muted">Prompts</label>
        <div className="flex gap-2">
          {availablePrompts.map((p) => (
            <button
              key={promptKey(p)}
              type="button"
              onClick={() => togglePrompt(p)}
              className={`rounded px-2 py-1 text-[10px] transition-colors ${isPromptSelected(p)
                ? "bg-cyan-400/20 text-cyan-400 border border-cyan-400/30"
                : "bg-terminal-border text-terminal-muted hover:text-slate-300 border border-transparent"
                }`}
            >
              {p.name}
            </button>
          ))}
        </div>
      </div>

      {/* Row 5: indicators (collapsible) */}
      <IndicatorSection
        ind={entry.indicators}
        onChange={(patch) => onChange({ indicators: { ...entry.indicators, ...patch } })}
      />
    </div>
  );
}

// ── LLM section ───────────────────────────────────────────────────────────────

const PROVIDER_OPTIONS = ["openai_compat", "llamacpp"];

function LLMSection({
  llm,
  onChange,
}: {
  llm: AppConfig["llm"];
  onChange: (patch: Partial<AppConfig["llm"]>) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase tracking-wider text-terminal-muted">Provider</label>
        <select
          value={llm.provider}
          onChange={(e) => onChange({ provider: e.target.value })}
          className="rounded border border-terminal-border bg-terminal-bg px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-400/50"
        >
          {PROVIDER_OPTIONS.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1 col-span-2">
        <label className="text-[10px] uppercase tracking-wider text-terminal-muted">Base URL</label>
        <input
          value={llm.base_url}
          onChange={(e) => onChange({ base_url: e.target.value })}
          className="rounded border border-terminal-border bg-terminal-bg px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-400/50"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-[10px] uppercase tracking-wider text-terminal-muted">Model</label>
        <input
          value={llm.model}
          onChange={(e) => onChange({ model: e.target.value })}
          placeholder="empty = server default"
          className="rounded border border-terminal-border bg-terminal-bg px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-400/50"
        />
      </div>

      <NumInput label="Temperature" value={llm.temperature} onChange={(v) => onChange({ temperature: v })} step={0.05} />
      <NumInput label="Max tokens" value={llm.max_tokens} onChange={(v) => onChange({ max_tokens: v })} min={1} />
      <NumInput label="Timeout (s)" value={llm.timeout} onChange={(v) => onChange({ timeout: v })} min={1} />
    </div>
  );
}

// ── Main ConfigPanel ───────────────────────────────────────────────────────────

export function ConfigPanel() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [availablePrompts, setAvailablePrompts] = useState<PromptRef[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const isFirstLoad = useRef(true);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetchConfig().then(setConfig).catch(console.error);
    fetchAvailablePrompts().then(setAvailablePrompts).catch(console.error);
  }, []);

  // Auto-save 600ms after any config change (skip the initial load)
  useEffect(() => {
    if (!config) return;
    if (isFirstLoad.current) {
      isFirstLoad.current = false;
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setSaving(true);
      setSaveError(null);
      try {
        const updated = await saveConfig(config);
        // Sync server response without re-triggering this effect
        isFirstLoad.current = true;
        setConfig(updated);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      } catch (err) {
        setSaveError(err instanceof Error ? err.message : "Save failed — is the backend running?");
      } finally {
        setSaving(false);
      }
    }, 600);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [config]);

  const addEntry = () => {
    setConfig((prev) =>
      prev
        ? {
          ...prev,
          watchlist: [
            ...prev.watchlist,
            {
              name: "New Group",
              enabled: false,
              symbols: [],
              interval_hours: 1,
              include_llm: true,
              prompts: [{ file: "prompts", name: "trading_analysis" }],
              indicators: {
                sma: { short_period: 20, long_period: 50 },
                rsi: { enabled: false, period: 14, oversold: 30, overbought: 70 },
                macd: { enabled: false, fast: 12, slow: 26, signal: 9 },
                bb: { enabled: false, period: 20, std: 2 },
              },
            },
          ],
        }
        : null
    );
  };

  const removeEntry = (idx: number) =>
    setConfig((prev) =>
      prev ? { ...prev, watchlist: prev.watchlist.filter((_, i) => i !== idx) } : null
    );

  const updateEntry = (idx: number, patch: Partial<WatchlistEntryConfig>) =>
    setConfig((prev) =>
      prev
        ? {
          ...prev,
          watchlist: prev.watchlist.map((e, i) => (i === idx ? { ...e, ...patch } : e)),
        }
        : null
    );

  if (!config) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-terminal-muted">
        Loading configuration…
      </div>
    );
  }

  return (
    <main className="flex-1 overflow-y-auto px-6 py-5 space-y-8">
      {/* ── LLM ──────────────────────────────────────────────────────────────── */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-terminal-muted">
            LLM
          </h2>
          <p className="text-[10px] text-terminal-muted/60">
            API key: set <code className="text-cyan-400/70">LLM_API_KEY</code> in backend/.env
          </p>
        </div>
        <LLMSection
          llm={config.llm}
          onChange={(patch) => setConfig({ ...config, llm: { ...config.llm, ...patch } })}
        />
      </section>

      {/* ── Watchlist entries ─────────────────────────────────────────────────── */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-terminal-muted">
            Watchlist Groups
          </h2>
          <button
            type="button"
            onClick={addEntry}
            className="flex items-center gap-1.5 rounded border border-terminal-border px-3 py-1.5 text-xs text-terminal-muted hover:border-cyan-400/50 hover:text-cyan-400 transition-colors"
          >
            <Plus className="h-3 w-3" />
            Add Group
          </button>
        </div>

        {config.watchlist.length === 0 ? (
          <div className="rounded-lg border border-dashed border-terminal-border p-10 text-center">
            <p className="text-sm text-terminal-muted">No groups configured</p>
            <p className="mt-1 text-xs text-terminal-muted/60">
              Add a group to start scanning symbols
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {config.watchlist.map((entry, idx) => (
              <EntryCard
                key={idx}
                entry={entry}
                onChange={(patch) => updateEntry(idx, patch)}
                onRemove={() => removeEntry(idx)}
                availablePrompts={availablePrompts}
              />
            ))}
          </div>
        )}
      </section>

      {/* ── Save ─────────────────────────────────────────────────────────────── */}
      <div className="sticky bottom-0 border-t border-terminal-border bg-terminal-bg py-3 flex items-center justify-between">
        {saveError ? (
          <p className="text-xs text-red-400">{saveError}</p>
        ) : (
          <span />
        )}
        <span className="flex items-center gap-1.5 text-xs text-terminal-muted">
          {saved ? (
            <><Check className="h-3 w-3 text-emerald-400" /><span className="text-emerald-400">Saved</span></>
          ) : saving ? (
            <><Save className="h-3 w-3 animate-pulse" /> Saving…</>
          ) : (
            <><Save className="h-3 w-3" /> Auto-saves on change</>
          )}
        </span>
      </div>
    </main>
  );
}
