import type { WatchlistItem, StockDetail, SignalFeedItem, AppConfig, PromptRef } from "./types";

const BASE = "";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, init);
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// ── Types matching backend schemas ────────────────────

interface WatchlistApiItem {
  symbol: string;
  price: number;
  change: number;
  signal: string | null;
  score: number | null;
  confidence: number | null;
}

interface AnalysisApiResponse {
  symbol: string;
  indicators: {
    close: number;
    sma_short: number;
    sma_long: number;
    rsi?: number | null;
    macd?: number | null;
    macd_signal?: number | null;
    macd_diff?: number | null;
    bb_upper?: number | null;
    bb_middle?: number | null;
    bb_lower?: number | null;
    bb_pband?: number | null;
  } | null;
  signal: {
    signal: string;
    score: number;
    confidence: number;
    reasons: string[];
  } | null;
  llm_results: { prompt_name: string; summary: string; recommendation: string }[] | null;
  error: string | null;
}

// ── Symbol name map (static for now) ──────────────────

const SYMBOL_NAMES: Record<string, string> = {
  AAPL: "Apple Inc.",
  MSFT: "Microsoft",
  TSLA: "Tesla Inc.",
  SPY: "S&P 500 ETF",
  NVDA: "NVIDIA Corp.",
  AMZN: "Amazon.com",
  GOOG: "Alphabet Inc.",
  META: "Meta Platforms",
  NFLX: "Netflix Inc.",
};

const SYMBOL_SECTORS: Record<string, string> = {
  SPY: "ETF",
  TSLA: "AUTOMOTIVE",
};

function signalToDirection(signal: string | null): "UP" | "DOWN" | "NEUTRAL" {
  if (signal === "BUY") return "UP";
  if (signal === "SELL") return "DOWN";
  return "NEUTRAL";
}

// ── Public API ────────────────────────────────────────

export async function fetchWatchlist(): Promise<WatchlistItem[]> {
  const items = await fetchJSON<WatchlistApiItem[]>("/api/market/watchlist");
  return items.map((item) => ({
    symbol: item.symbol,
    name: SYMBOL_NAMES[item.symbol] ?? item.symbol,
    price: item.price,
    change: item.change,
    aiScore: Math.round((item.confidence ?? 0.5) * 100),
    signal: signalToDirection(item.signal),
    tag: item.signal
      ? `Signal: ${item.signal} (score ${item.score})`
      : undefined,
  }));
}

function mapAnalysis(data: AnalysisApiResponse): StockDetail {
  if (data.error) throw new Error(data.error);
  const ind = data.indicators!;
  const sig = data.signal;
  return {
    symbol: data.symbol,
    name: SYMBOL_NAMES[data.symbol] ?? data.symbol,
    sector: SYMBOL_SECTORS[data.symbol] ?? "TECHNOLOGY",
    price: ind.close,
    change: 0, // will be merged from watchlist data
    lastClose: ind.close,
    sessionHigh: ind.bb_upper ?? ind.close,
    sessionLow: ind.bb_lower ?? ind.close,
    volume: 0,
    indicators: {
      smaShort: ind.sma_short,
      smaLong: ind.sma_long,
      rsi: ind.rsi ?? undefined,
      macd: ind.macd ?? undefined,
      macdSignal: ind.macd_signal ?? undefined,
      macdHist: ind.macd_diff ?? undefined,
      bbUpper: ind.bb_upper ?? undefined,
      bbMiddle: ind.bb_middle ?? undefined,
      bbLower: ind.bb_lower ?? undefined,
      bbPband: ind.bb_pband ?? undefined,
    },
    signal: sig
      ? { signal: sig.signal, score: sig.score, confidence: sig.confidence, reasons: sig.reasons }
      : undefined,
    llmResults: data.llm_results ?? undefined,
  };
}

export async function fetchAnalysis(symbol: string): Promise<StockDetail> {
  const data = await fetchJSON<AnalysisApiResponse>("/api/analysis", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol: symbol.toUpperCase(), include_llm: true }),
  });
  return mapAnalysis(data);
}

export async function fetchScheduledResults(): Promise<StockDetail[]> {
  const items = await fetchJSON<AnalysisApiResponse[]>("/api/analysis/scheduled");
  return items.flatMap((d) => {
    try { return [mapAnalysis(d)]; } catch { return []; }
  });
}

/**
 * Open an SSE connection to the backend analysis stream.
 * `onResult` is called immediately whenever the scheduler completes a cycle
 * for any symbol — no polling delay.
 *
 * Returns the underlying EventSource so the caller can close it on cleanup.
 */
export function subscribeAnalysisStream(
  onResult: (detail: StockDetail) => void,
): EventSource {
  const es = new EventSource("/api/analysis/stream");
  es.onmessage = (event) => {
    try {
      const raw = JSON.parse(event.data) as AnalysisApiResponse;
      onResult(mapAnalysis(raw));
    } catch {
      // ignore malformed or error-only events
      console.warn("Failed to parse SSE event:", event.data);
    }
  };
  return es;
}

export async function fetchSignals(): Promise<SignalFeedItem[]> {
  // Signal feed will come from AI analysis in the future.
  // For now, return empty — the UI will show a placeholder.
  return [];
}

export async function checkHealth(): Promise<boolean> {
  try {
    const data = await fetchJSON<{ status: string }>("/health");
    return data.status === "ok";
  } catch {
    return false;
  }
}

// ── OHLCV / chart data ────────────────────────────────

export interface OHLCVBar {
  time: number;   // unix timestamp (seconds)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export async function fetchOHLCV(
  symbol: string,
  period = "3mo",
  interval = "1d",
): Promise<OHLCVBar[]> {
  const params = new URLSearchParams({ period, interval });
  const data = await fetchJSON<{ bars: OHLCVBar[] }>(
    `/api/market/ohlcv/${encodeURIComponent(symbol.toUpperCase())}?${params}`,
  );
  return data.bars ?? [];
}

// ── Config API ────────────────────────────────────────

export async function fetchConfig(): Promise<AppConfig> {
  return fetchJSON<AppConfig>("/api/config");
}

export async function fetchAvailablePrompts(): Promise<PromptRef[]> {
  return fetchJSON<PromptRef[]>("/api/config/prompts");
}

export async function saveConfig(config: AppConfig): Promise<AppConfig> {
  return fetchJSON<AppConfig>("/api/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
}

// ── Symbol search ─────────────────────────────────────────────────────────────

export interface TickerSearchResult {
  symbol: string;
  name: string;
  type: string;
  exchange: string;
}

export async function searchTickers(query: string): Promise<TickerSearchResult[]> {
  if (!query.trim()) return [];
  return fetchJSON<TickerSearchResult[]>(
    `/api/market/search?q=${encodeURIComponent(query.trim())}`
  );
}
