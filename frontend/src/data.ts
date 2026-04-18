import { WatchlistItem, StockDetail, SignalFeedItem } from "./types";

export const watchlist: WatchlistItem[] = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    price: 253.5,
    change: -2.07,
    aiScore: 63,
    signal: "UP",
    tag: "Bull flag consolidation near resi...",
  },
  {
    symbol: "MSFT",
    name: "Microsoft",
    price: 415.8,
    change: 0.73,
    aiScore: 82,
    signal: "DOWN",
    tag: "Breakout continuation pattern form...",
  },
  {
    symbol: "TSLA",
    name: "Tesla Inc.",
    price: 182.5,
    change: -2.14,
    aiScore: 55,
    signal: "NEUTRAL",
    tag: "Range-bound with declining volume",
  },
  {
    symbol: "SPY",
    name: "S&P 500 ETF",
    price: 543.71,
    change: 0.47,
    aiScore: 76,
    signal: "NEUTRAL",
    tag: "Breakout continuation pattern form...",
  },
  {
    symbol: "NVDA",
    name: "NVIDIA Corp.",
    price: 875.3,
    change: 1.25,
    aiScore: 88,
    signal: "UP",
    tag: "Strong momentum above 50-day SMA",
  },
  {
    symbol: "AMZN",
    name: "Amazon.com",
    price: 186.4,
    change: -0.35,
    aiScore: 61,
    signal: "NEUTRAL",
    tag: "Testing support near 185 level",
  },
];

export function getStockDetail(symbol: string): StockDetail {
  const item = watchlist.find((w) => w.symbol === symbol) ?? watchlist[0];
  return {
    symbol: item.symbol,
    name: item.name,
    sector:
      item.symbol === "SPY"
        ? "ETF"
        : item.symbol === "TSLA"
          ? "AUTOMOTIVE"
          : "TECHNOLOGY",
    price: item.price,
    change: item.change,
    lastClose: +(item.price * (1 + Math.random() * 0.02)).toFixed(2),
    sessionHigh: +(item.price * (1 + Math.random() * 0.01)).toFixed(2),
    sessionLow: +(item.price * (1 - Math.random() * 0.02)).toFixed(2),
    volume: Math.floor(500000 + Math.random() * 1500000),
    indicators: {
      rsi: +(40 + Math.random() * 30).toFixed(2),
      macd: +(Math.random() * 4 - 2).toFixed(4),
      macdSignal: +(Math.random() * 3 - 1.5).toFixed(4),
      macdHist: +(Math.random() * 2 - 1).toFixed(4),
      bbUpper: +(item.price * 1.05).toFixed(2),
      bbMiddle: +item.price.toFixed(2),
      bbLower: +(item.price * 0.95).toFixed(2),
      bbPband: +(Math.random()).toFixed(4),
      smaShort: +(item.price * (0.98 + Math.random() * 0.04)).toFixed(2),
      smaLong: +(item.price * (0.95 + Math.random() * 0.06)).toFixed(2),
    },
  };
}

export const signalFeed: SignalFeedItem[] = [
  {
    id: "1",
    message: "Volatility spike detected — 2.4σ above 30-day average",
    severity: "HIGH",
    symbol: "AAPL",
    timeframe: "1H",
    timestamp: "2m ago",
  },
  {
    id: "2",
    message:
      "Realized vol crossed 2.4σ. Elevated mean-reversion probability within 4-6 bars.",
    severity: "MEDIUM",
    symbol: "AAPL",
    timeframe: "1H",
    timestamp: "5m ago",
  },
  {
    id: "3",
    message: "Trend reversal probability increased to 61% — watch key level",
    severity: "HIGH",
    symbol: "TSLA",
    timeframe: "4H",
    timestamp: "7m ago",
  },
  {
    id: "4",
    message: "SPY unusual volume activity — 3.1x session average",
    severity: "MEDIUM",
    symbol: "SPY",
    timeframe: "1H",
    timestamp: "14m ago",
  },
  {
    id: "5",
    message: "MSFT approaching key resistance zone at $417",
    severity: "MEDIUM",
    symbol: "MSFT",
    timeframe: "1D",
    timestamp: "22m ago",
  },
  {
    id: "6",
    message: "Confidence score elevated — accumulation pattern forming",
    severity: "LOW",
    symbol: "AAPL",
    timeframe: "4H",
    timestamp: "31m ago",
  },
  {
    id: "7",
    message: "Cross-asset correlation rising — macro regime shift possible",
    severity: "MEDIUM",
    symbol: "SPY",
    timeframe: "1D",
    timestamp: "45m ago",
  },
  {
    id: "8",
    message: "NVDA volume profile divergence detected on 4H timeframe",
    severity: "LOW",
    symbol: "NVDA",
    timeframe: "4H",
    timestamp: "50m ago",
  },
  {
    id: "9",
    message: "Momentum score: 78 — uptrend structure intact",
    severity: "LOW",
    symbol: "MSFT",
    timeframe: "1D",
    timestamp: "1h ago",
  },
  {
    id: "10",
    message: "Funding rate turning negative — potential squeeze setup",
    severity: "LOW",
    symbol: "TSLA",
    timeframe: "4H",
    timestamp: "1h ago",
  },
];
