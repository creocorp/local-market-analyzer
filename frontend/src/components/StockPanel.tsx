import {
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { StockDetail } from "../types";
import { PriceChart } from "./PriceChart";

interface StockPanelProps {
  stock: StockDetail;
  loading?: boolean;
}

export function StockPanel({ stock, loading }: StockPanelProps) {
  const isUp = stock.change >= 0;

  return (
    <main className="flex-1 flex flex-col overflow-y-auto">
      {/* Price header */}
      <div className="border-b border-terminal-border px-6 py-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-cyan-400 font-medium tracking-wider uppercase">
                {stock.sector}
              </span>
              <span className="text-terminal-muted text-xs">•</span>
              <span className="text-xs text-terminal-muted">
                {stock.name} — {stock.symbol}
              </span>
            </div>
            <div className="mt-2 flex items-baseline gap-3">
              <span className="text-4xl font-bold text-white">
                ${stock.price.toFixed(2)}
              </span>
              <span
                className={`flex items-center gap-1 text-sm font-medium ${isUp ? "text-emerald-400" : "text-red-400"}`}
              >
                {isUp ? (
                  <ArrowUpRight className="h-4 w-4" />
                ) : (
                  <ArrowDownRight className="h-4 w-4" />
                )}
                {isUp ? "+" : ""}
                {stock.change.toFixed(2)}% today
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/20 px-3 py-1 text-xs text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live
            </span>
          </div>
        </div>
      </div>

      {/* Price chart */}
      <div className="border-b border-terminal-border">
        <PriceChart symbol={stock.symbol} />
      </div>

      {/* Session stats */}
      <div className="border-b border-terminal-border px-6 py-4">
        <div className="grid grid-cols-4 gap-4">
          <StatCard
            label="Last Close"
            value={`$${stock.lastClose.toFixed(2)}`}
            icon={<Clock className="h-4 w-4" />}
          />
          <StatCard
            label="Session High"
            value={`$${stock.sessionHigh.toFixed(2)}`}
            icon={<TrendingUp className="h-4 w-4" />}
            valueClass="text-emerald-400"
          />
          <StatCard
            label="Session Low"
            value={`$${stock.sessionLow.toFixed(2)}`}
            icon={<TrendingDown className="h-4 w-4" />}
            valueClass="text-red-400"
          />
          <StatCard
            label="Volume"
            value={formatVolume(stock.volume)}
            icon={<Activity className="h-4 w-4" />}
          />
        </div>
      </div>

      {/* Indicators */}
      <div className="px-6 py-4">
        <h3 className="text-xs font-semibold tracking-widest text-terminal-muted uppercase mb-3">
          Technical Indicators
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <IndicatorRow label="SMA Short" value={stock.indicators.smaShort} />
          <IndicatorRow label="SMA Long" value={stock.indicators.smaLong} />
          {stock.indicators.rsi != null && (
            <IndicatorRow label="RSI" value={stock.indicators.rsi} />
          )}
          {stock.indicators.macd != null && (
            <IndicatorRow label="MACD" value={stock.indicators.macd} />
          )}
          {stock.indicators.macdSignal != null && (
            <IndicatorRow label="MACD Signal" value={stock.indicators.macdSignal} />
          )}
          {stock.indicators.macdHist != null && (
            <IndicatorRow label="MACD Hist" value={stock.indicators.macdHist} colored />
          )}
          {stock.indicators.bbUpper != null && (
            <IndicatorRow label="BB Upper" value={stock.indicators.bbUpper} />
          )}
          {stock.indicators.bbMiddle != null && (
            <IndicatorRow label="BB Middle" value={stock.indicators.bbMiddle} />
          )}
          {stock.indicators.bbLower != null && (
            <IndicatorRow label="BB Lower" value={stock.indicators.bbLower} />
          )}
          {stock.indicators.bbPband != null && (
            <IndicatorRow label="BB %B" value={stock.indicators.bbPband} />
          )}
        </div>
      </div>

      {/* Signal Reasoning */}
      {stock.signal && (
        <div className="border-t border-terminal-border px-6 py-4">
          <h3 className="text-xs font-semibold tracking-widest text-terminal-muted uppercase mb-3">
            Signal Analysis
          </h3>
          <div className="flex items-center gap-3 mb-3">
            <span
              className={`rounded px-2 py-1 text-xs font-bold ${stock.signal.signal === "BUY"
                ? "bg-emerald-400/20 text-emerald-400"
                : stock.signal.signal === "SELL"
                  ? "bg-red-400/20 text-red-400"
                  : "bg-yellow-400/20 text-yellow-400"
                }`}
            >
              {stock.signal.signal}
            </span>
            <span className="text-xs text-terminal-muted">
              Score: {stock.signal.score} | Confidence:{" "}
              {(stock.signal.confidence * 100).toFixed(0)}%
            </span>
          </div>
          <ul className="space-y-1">
            {stock.signal.reasons.map((reason, i) => (
              <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                <span className="text-terminal-muted mt-0.5">•</span>
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* LLM Analysis */}
      {stock.llmResults && stock.llmResults.length > 0 && (
        <div className="border-t border-terminal-border px-6 py-4">
          <h3 className="text-xs font-semibold tracking-widest text-terminal-muted uppercase mb-3">
            AI Analysis
          </h3>
          <div className="space-y-3">
            {stock.llmResults.map((result, i) => (
              <div
                key={i}
                className="rounded-lg border border-terminal-border bg-terminal-bg/50 px-4 py-3 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase tracking-wider text-terminal-muted">
                    {result.prompt_name.replace(/_/g, " ")}
                  </span>
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] font-bold ${result.recommendation === "BUY"
                      ? "bg-emerald-400/20 text-emerald-400"
                      : result.recommendation === "SELL"
                        ? "bg-red-400/20 text-red-400"
                        : "bg-yellow-400/20 text-yellow-400"
                      }`}
                  >
                    {result.recommendation}
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{result.summary}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div className="border-t border-terminal-border px-6 py-3">
          <p className="text-xs text-terminal-muted animate-pulse">Refreshing data...</p>
        </div>
      )}
    </main>
  );
}

function StatCard({
  label,
  value,
  icon,
  valueClass = "text-slate-200",
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  valueClass?: string;
}) {
  return (
    <div className="rounded-lg border border-terminal-border bg-terminal-bg p-3">
      <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
        {icon}
        <span className="text-[10px] uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-lg font-semibold ${valueClass}`}>{value}</div>
    </div>
  );
}

function IndicatorRow({
  label,
  value,
  colored = false,
}: {
  label: string;
  value: number;
  colored?: boolean;
}) {
  let valueColor = "text-slate-300";
  if (colored) {
    valueColor = value >= 0 ? "text-emerald-400" : "text-red-400";
  }

  return (
    <div className="flex items-center justify-between rounded border border-terminal-border bg-terminal-bg/50 px-3 py-2">
      <span className="text-xs text-terminal-muted">{label}</span>
      <span className={`text-xs font-medium ${valueColor}`}>
        {value.toFixed(4)}
      </span>
    </div>
  );
}

function formatVolume(vol: number): string {
  if (vol >= 1_000_000) return `${(vol / 1_000_000).toFixed(1)}M`;
  if (vol >= 1_000) return `${(vol / 1_000).toFixed(0)}K`;
  return vol.toString();
}
