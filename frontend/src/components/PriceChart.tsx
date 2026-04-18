import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, CandlestickSeries, type UTCTimestamp } from "lightweight-charts";
import { fetchOHLCV, type OHLCVBar } from "../api";

const PERIODS = [
    { label: "1D", period: "1d", interval: "5m" },
    { label: "5D", period: "5d", interval: "15m" },
    { label: "1M", period: "1mo", interval: "1h" },
    { label: "3M", period: "3mo", interval: "1d" },
    { label: "6M", period: "6mo", interval: "1d" },
    { label: "1Y", period: "1y", interval: "1wk" },
];

interface PriceChartProps {
    symbol: string;
}

export function PriceChart({ symbol }: PriceChartProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [selectedIdx, setSelectedIdx] = useState(3); // default: 3M
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [bars, setBars] = useState<OHLCVBar[]>([]);

    // Fetch OHLCV whenever symbol or selected period changes
    useEffect(() => {
        let cancelled = false;
        const { period, interval } = PERIODS[selectedIdx];
        setLoading(true);
        setError(null);
        fetchOHLCV(symbol, period, interval)
            .then((data) => {
                if (!cancelled) setBars(data);
            })
            .catch((e: Error) => {
                if (!cancelled) setError(e.message);
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        return () => { cancelled = true; };
    }, [symbol, selectedIdx]);

    // Build / update chart whenever bars change
    useEffect(() => {
        const el = containerRef.current;
        if (!el || bars.length === 0) return;

        const chart = createChart(el, {
            layout: {
                background: { type: ColorType.Solid, color: "transparent" },
                textColor: "#64748b",
                fontSize: 11,
            },
            grid: {
                vertLines: { color: "rgba(255,255,255,0.04)" },
                horzLines: { color: "rgba(255,255,255,0.04)" },
            },
            crosshair: {
                vertLine: { color: "rgba(100,255,218,0.3)", labelBackgroundColor: "#0f2027" },
                horzLine: { color: "rgba(100,255,218,0.3)", labelBackgroundColor: "#0f2027" },
            },
            rightPriceScale: {
                borderColor: "rgba(255,255,255,0.08)",
                textColor: "#64748b",
            },
            timeScale: {
                borderColor: "rgba(255,255,255,0.08)",
                timeVisible: true,
                secondsVisible: false,
            },
            width: el.clientWidth,
            height: el.clientHeight,
        });

        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: "#34d399",
            downColor: "#f87171",
            borderUpColor: "#34d399",
            borderDownColor: "#f87171",
            wickUpColor: "#34d399",
            wickDownColor: "#f87171",
        });

        // lightweight-charts v4+ wants time as UTCTimestamp (seconds)
        candleSeries.setData(
            bars.map((b) => ({
                time: b.time as UTCTimestamp,
                open: b.open,
                high: b.high,
                low: b.low,
                close: b.close,
            }))
        );

        chart.timeScale().fitContent();

        // Resize observer
        const ro = new ResizeObserver(() => {
            chart.applyOptions({ width: el.clientWidth, height: el.clientHeight });
        });
        ro.observe(el);

        return () => {
            ro.disconnect();
            chart.remove();
        };
    }, [bars]);

    return (
        <div className="flex flex-col gap-0">
            {/* Period selector */}
            <div className="flex items-center gap-1 px-6 pt-4 pb-2">
                {PERIODS.map((p, i) => (
                    <button
                        key={p.label}
                        type="button"
                        onClick={() => setSelectedIdx(i)}
                        className={`rounded px-2 py-0.5 text-[10px] transition-colors ${selectedIdx === i
                                ? "bg-cyan-400/20 text-cyan-400"
                                : "bg-terminal-border text-terminal-muted hover:text-slate-300"
                            }`}
                    >
                        {p.label}
                    </button>
                ))}
                {loading && (
                    <span className="ml-2 text-[10px] text-terminal-muted animate-pulse">loading…</span>
                )}
            </div>

            {/* Chart area */}
            <div className="relative px-6 pb-4">
                {error ? (
                    <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-terminal-border bg-terminal-bg/50">
                        <p className="text-xs text-red-400/70">{error}</p>
                    </div>
                ) : bars.length === 0 && !loading ? (
                    <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-terminal-border bg-terminal-bg/50">
                        <p className="text-xs text-terminal-muted/60">No data</p>
                    </div>
                ) : (
                    <div
                        ref={containerRef}
                        className="h-52 w-full rounded-lg overflow-hidden"
                        style={{ opacity: loading ? 0.4 : 1, transition: "opacity 0.15s" }}
                    />
                )}
            </div>
        </div>
    );
}
