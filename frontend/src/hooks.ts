import { useState, useEffect, useCallback, useRef } from "react";
import { fetchWatchlist, fetchAnalysis, subscribeAnalysisStream, checkHealth } from "./api";
import type { WatchlistItem, StockDetail, SignalFeedItem } from "./types";

export function useMarketData() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("");
  const [stockDetail, setStockDetail] = useState<StockDetail | null>(null);
  const [signals, setSignals] = useState<SignalFeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState(false);

  const selectedSymbolRef = useRef(selectedSymbol);
  useEffect(() => { selectedSymbolRef.current = selectedSymbol; }, [selectedSymbol]);

  const POLL_MS = 30_000;

  // Health check on mount + every 30s
  useEffect(() => {
    checkHealth().then(setBackendOnline);
    const id = setInterval(() => checkHealth().then(setBackendOnline), POLL_MS);
    return () => clearInterval(id);
  }, []);

  // Load watchlist — stable (uses ref for selectedSymbol)
  const loadWatchlist = useCallback(async () => {
    try {
      const items = await fetchWatchlist();
      setWatchlist(items);
      if (!selectedSymbolRef.current && items.length > 0) {
        setSelectedSymbol(items[0].symbol);
      }
      setError(null);
    } catch (err) {
      setError(`Failed to load watchlist: ${err}`);
    }
  }, []);

  // Load stock detail when symbol changes
  const loadStockDetail = useCallback(async (symbol: string) => {
    if (!symbol) return;
    setLoading(true);
    try {
      const detail = await fetchAnalysis(symbol);
      // Merge change % from watchlist
      setStockDetail((_prev) => {
        const watchItem = watchlist.find((w) => w.symbol === symbol);
        return {
          ...detail,
          change: watchItem?.change ?? detail.change,
        };
      });
      setError(null);
    } catch (err) {
      setError(`Failed to load ${symbol}: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [watchlist]);

  // Initial load
  useEffect(() => {
    loadWatchlist().then(() => setLoading(false));
  }, [loadWatchlist]);

  // Fetch detail when symbol changes
  useEffect(() => {
    if (selectedSymbol) {
      loadStockDetail(selectedSymbol);
    }
  }, [selectedSymbol, loadStockDetail]);

  // Poll watchlist every 30s
  useEffect(() => {
    if (!backendOnline) return;
    const id = setInterval(loadWatchlist, POLL_MS);
    return () => clearInterval(id);
  }, [backendOnline, loadWatchlist]);

  // SSE stream — updates stock detail and watchlist badges in real time
  // whenever the backend scheduler completes an analysis cycle.
  useEffect(() => {
    if (!backendOnline) return;
    const es = subscribeAnalysisStream((result) => {
      // Keep watchlist price + signal badge current for this symbol
      setWatchlist((prev) =>
        prev.map((w) =>
          w.symbol === result.symbol
            ? {
              ...w,
              price: result.price,
              aiScore: result.signal ? Math.round(result.signal.confidence * 100) : w.aiScore,
              signal: (
                result.signal?.signal === "BUY" ? "UP"
                  : result.signal?.signal === "SELL" ? "DOWN"
                    : "NEUTRAL"
              ) as WatchlistItem["signal"],
            }
            : w
        )
      );
      // Refresh stock detail panel if this is the currently selected symbol
      setStockDetail((prev) =>
        prev?.symbol === result.symbol ? { ...result, change: prev.change } : prev
      );
      // Append to signal feed for BUY / SELL (skip HOLD to reduce noise)
      // Use LLM recommendation if available, otherwise fall back to rule-based signal.
      const llmRec = result.llmResults?.[0]?.recommendation?.toUpperCase();
      const ruleSignal = result.signal?.signal;
      const effectiveSignal = (llmRec === "BUY" || llmRec === "SELL") ? llmRec : ruleSignal;

      if (effectiveSignal && effectiveSignal !== "HOLD") {
        const sig = effectiveSignal;
        const severity: SignalFeedItem["severity"] =
          (result.signal?.confidence ?? 0) >= 0.7 ? "HIGH"
            : (result.signal?.confidence ?? 0) >= 0.4 ? "MEDIUM"
              : "LOW";
        const llmSummary = result.llmResults?.[0]?.summary;
        const message = llmSummary
          ? `${sig}: ${llmSummary}`
          : `${sig} signal — score ${result.signal?.score}, confidence ${Math.round((result.signal?.confidence ?? 0) * 100)}%`;
        const item: SignalFeedItem = {
          id: `${result.symbol}-${Date.now()}`,
          symbol: result.symbol,
          severity,
          message,
          timeframe: "scheduled",
          timestamp: new Date().toLocaleTimeString(),
        };
        setSignals((prev) => [item, ...prev].slice(0, 50));
      }
    });
    return () => es.close();
  }, [backendOnline]);

  const refresh = useCallback(() => {
    setLoading(true);
    loadWatchlist();
    if (selectedSymbol) {
      loadStockDetail(selectedSymbol);
    }
  }, [loadWatchlist, loadStockDetail, selectedSymbol]);

  const searchSymbol = useCallback(
    (symbol: string) => {
      const upper = symbol.toUpperCase();
      setSelectedSymbol(upper);
      // Add to watchlist temporarily if not present
      if (!watchlist.find((w) => w.symbol === upper)) {
        setWatchlist((prev) => [
          ...prev,
          {
            symbol: upper,
            name: upper,
            price: 0,
            change: 0,
            aiScore: 0,
            signal: "NEUTRAL" as const,
          },
        ]);
      }
    },
    [watchlist],
  );

  return {
    watchlist,
    selectedSymbol,
    setSelectedSymbol,
    stockDetail,
    signals,
    loading,
    error,
    backendOnline,
    refresh,
    searchSymbol,
  };
}
