import { useState, useEffect, useRef } from "react";
import { Search, Zap, RefreshCw, Settings } from "lucide-react";
import { searchTickers } from "../api";
import type { TickerSearchResult } from "../api";

interface HeaderProps {
  onRefresh: () => void;
  onSearch: (symbol: string) => void;
  backendOnline: boolean;
  onConfigToggle: () => void;
  configActive: boolean;
}

export function Header({ onRefresh, onSearch, backendOnline, onConfigToggle, configActive }: HeaderProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<TickerSearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounced search against yfinance
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length < 1) {
      setResults([]);
      setOpen(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const hits = await searchTickers(query);
        setResults(hits);
        setOpen(hits.length > 0);
        setActiveIdx(-1);
      } catch {
        setResults([]);
        setOpen(false);
      }
    }, 250);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const commit = (symbol: string) => {
    onSearch(symbol.toUpperCase());
    setQuery("");
    setResults([]);
    setOpen(false);
    setActiveIdx(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open) {
      if (e.key === "Enter") {
        const sym = query.trim().toUpperCase();
        if (sym) commit(sym);
      }
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, -1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (activeIdx >= 0 && results[activeIdx]) {
        commit(results[activeIdx].symbol);
      } else {
        const sym = query.trim().toUpperCase();
        if (sym) commit(sym);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <header className="flex items-center justify-between border-b border-terminal-border bg-terminal-surface px-4 py-2">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-cyan-400" />
          <span className="text-lg font-bold tracking-wider text-cyan-400">LOCAL MARKET ANALYZER</span>
        </div>

        <div className="flex items-center gap-2 ml-4">
          {backendOnline ? (
            <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Connected
            </span>
          ) : (
            <span className="flex items-center gap-1.5 rounded-full bg-red-500/20 px-2.5 py-0.5 text-xs text-red-400">
              <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
              Offline
            </span>
          )}
          <span className="rounded-full bg-terminal-border px-2.5 py-0.5 text-xs text-terminal-muted">
            v0.1.0
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Search with autocomplete */}
        <div ref={containerRef} className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-terminal-muted pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => results.length > 0 && setOpen(true)}
            placeholder="Search ticker..."
            autoComplete="off"
            className="w-52 rounded-md border border-terminal-border bg-terminal-bg py-1.5 pl-8 pr-3 text-xs text-slate-300 placeholder-terminal-muted outline-none focus:border-cyan-400/50"
          />

          {open && results.length > 0 && (
            <ul className="absolute left-0 top-full z-50 mt-1 w-72 overflow-hidden rounded-md border border-terminal-border bg-terminal-surface shadow-lg">
              {results.map((r, i) => (
                <li key={r.symbol}>
                  <button
                    type="button"
                    onMouseDown={(e) => { e.preventDefault(); commit(r.symbol); }}
                    className={`flex w-full items-center justify-between px-3 py-2 text-left text-xs transition-colors ${i === activeIdx ? "bg-cyan-400/10 text-cyan-400" : "text-slate-300 hover:bg-terminal-border/50"}`}
                  >
                    <span className="font-mono font-semibold">{r.symbol}</span>
                    <span className="ml-3 truncate text-right text-terminal-muted">{r.name}</span>
                    <span className="ml-2 flex-shrink-0 rounded bg-terminal-border px-1 py-0.5 text-[9px] uppercase text-terminal-muted">{r.exchange}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <button
          onClick={onRefresh}
          className="rounded-md border border-terminal-border p-1.5 text-terminal-muted hover:border-cyan-400/50 hover:text-cyan-400 transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={onConfigToggle}
          className={`rounded-md border p-1.5 transition-colors ${configActive
            ? "border-cyan-400/50 text-cyan-400 bg-cyan-400/10"
            : "border-terminal-border text-terminal-muted hover:border-cyan-400/50 hover:text-cyan-400"
            }`}
          title="Configure"
        >
          <Settings className="h-3.5 w-3.5" />
        </button>
      </div>
    </header>
  );
}

