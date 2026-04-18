export interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  aiScore: number;
  signal: "UP" | "DOWN" | "NEUTRAL";
  tag?: string;
}

export interface StockDetail {
  symbol: string;
  name: string;
  sector: string;
  price: number;
  change: number;
  lastClose: number;
  sessionHigh: number;
  sessionLow: number;
  volume: number;
  indicators: {
    smaShort: number;
    smaLong: number;
    rsi?: number | null;
    macd?: number | null;
    macdSignal?: number | null;
    macdHist?: number | null;
    bbUpper?: number | null;
    bbMiddle?: number | null;
    bbLower?: number | null;
    bbPband?: number | null;
  };
  signal?: {
    signal: string;
    score: number;
    confidence: number;
    reasons: string[];
  };
  llmResults?: { prompt_name: string; summary: string; recommendation: string }[];
}

export interface SignalFeedItem {
  id: string;
  message: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  symbol: string;
  timeframe: string;
  timestamp: string;
}

// ── Config types ───────────────────────────────────────────────────────────────

export interface SMAConfig {
  short_period: number;
  long_period: number;
}

export interface RSIConfig {
  enabled: boolean;
  period: number;
  oversold: number;
  overbought: number;
}

export interface MACDConfig {
  enabled: boolean;
  fast: number;
  slow: number;
  signal: number;
}

export interface BBConfig {
  enabled: boolean;
  period: number;
  std: number;
}

export interface IndicatorConfig {
  sma: SMAConfig;
  rsi: RSIConfig;
  macd: MACDConfig;
  bb: BBConfig;
}

export interface PromptRef {
  file: string;
  name: string;
}

/** Exactly one interval field should be set; most granular wins: seconds > minutes > hours > days. */
export interface WatchlistEntryConfig {
  name: string;
  enabled: boolean;
  symbols: string[];
  interval_seconds?: number | null;
  interval_minutes?: number | null;
  interval_hours?: number | null;
  interval_days?: number | null;
  include_llm: boolean;
  prompts: PromptRef[];
  indicators: IndicatorConfig;
}

export interface LLMConfig {
  provider: string;
  base_url: string;
  model: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
}

export interface AppConfig {
  llm: LLMConfig;
  watchlist: WatchlistEntryConfig[];
}
