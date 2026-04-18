import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { WatchlistItem } from "../types";

interface WatchlistProps {
  items: WatchlistItem[];
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}

const signalConfig = {
  UP: { icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-400/20" },
  DOWN: { icon: TrendingDown, color: "text-red-400", bg: "bg-red-400/20" },
  NEUTRAL: { icon: Minus, color: "text-yellow-400", bg: "bg-yellow-400/20" },
};

export function Watchlist({ items, selectedSymbol, onSelect }: WatchlistProps) {
  return (
    <aside className="flex w-64 flex-col border-r border-terminal-border bg-terminal-surface">
      <div className="border-b border-terminal-border px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold tracking-widest text-terminal-muted uppercase">
            Watchlist
          </h2>
          <span className="text-xs text-terminal-muted">
            {items.length} assets
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {items.map((item) => {
          const config = signalConfig[item.signal];
          const Icon = config.icon;
          const isSelected = item.symbol === selectedSymbol;

          return (
            <button
              key={item.symbol}
              onClick={() => onSelect(item.symbol)}
              className={`w-full border-b border-terminal-border px-4 py-3 text-left transition-colors hover:bg-white/5 ${isSelected ? "bg-cyan-400/5 border-l-2 border-l-cyan-400" : ""
                }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-slate-200">
                      {item.symbol}
                    </span>
                    <span
                      className={`flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium ${config.bg} ${config.color}`}
                    >
                      <Icon className="h-3 w-3" />
                      {item.signal}
                    </span>
                  </div>
                  <p className="text-[11px] text-terminal-muted truncate mt-0.5">
                    {item.name}
                  </p>
                </div>
                <div className="text-right ml-2">
                  <div className="text-sm font-medium text-slate-200">
                    ${item.price.toFixed(2)}
                  </div>
                  <div
                    className={`text-xs ${item.change >= 0 ? "text-emerald-400" : "text-red-400"}`}
                  >
                    {item.change >= 0 ? "+" : ""}
                    {item.change.toFixed(2)}%
                  </div>
                </div>
              </div>

              <div className="mt-2 flex items-center gap-2">
                <span className="text-[10px] text-terminal-muted">
                  AI {item.aiScore}
                </span>
                <div className="flex-1 h-1 bg-terminal-border rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${item.aiScore >= 70
                        ? "bg-emerald-400"
                        : item.aiScore >= 50
                          ? "bg-yellow-400"
                          : "bg-red-400"
                      }`}
                    style={{ width: `${item.aiScore}%` }}
                  />
                </div>
              </div>

              {item.tag && (
                <p className="mt-1.5 text-[10px] text-terminal-muted/70 italic truncate">
                  {item.tag}
                </p>
              )}
            </button>
          );
        })}
      </div>
    </aside>
  );
}
