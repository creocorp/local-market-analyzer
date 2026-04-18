import {
  AlertTriangle,
  Info,
  AlertCircle,
  Radio,
} from "lucide-react";
import { SignalFeedItem } from "../types";

interface SignalFeedProps {
  signals: SignalFeedItem[];
}

const severityConfig = {
  HIGH: {
    icon: AlertTriangle,
    badge: "bg-red-500/20 text-red-400 border-red-500/30",
    dot: "bg-red-400",
  },
  MEDIUM: {
    icon: AlertCircle,
    badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    dot: "bg-yellow-400",
  },
  LOW: {
    icon: Info,
    badge: "bg-slate-500/20 text-slate-400 border-slate-500/30",
    dot: "bg-slate-400",
  },
};

export function SignalFeed({ signals }: SignalFeedProps) {
  return (
    <aside className="flex w-80 flex-col border-l border-terminal-border bg-terminal-surface">
      <div className="border-b border-terminal-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-cyan-400" />
          <h2 className="text-xs font-semibold tracking-widest text-terminal-muted uppercase">
            Signal Feed
          </h2>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {signals.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-4 text-center">
            <Radio className="h-8 w-8 text-terminal-muted/30 mb-3" />
            <p className="text-xs text-terminal-muted">
              Signal feed will populate with AI analysis
            </p>
            <p className="text-[10px] text-terminal-muted/60 mt-1">
              Connect an LLM to enable real-time signals
            </p>
          </div>
        ) : (
          signals.map((signal) => {
            const config = severityConfig[signal.severity];
            const Icon = config.icon;

            return (
              <div
                key={signal.id}
                className="border-b border-terminal-border px-4 py-3 hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex items-start gap-2.5">
                  <div
                    className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${config.dot}`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {signal.message}
                    </p>
                    <div className="mt-2 flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] text-terminal-muted">
                        {signal.timestamp}
                      </span>
                      <span className="rounded bg-cyan-400/10 px-1.5 py-0.5 text-[10px] font-medium text-cyan-400">
                        {signal.symbol}
                      </span>
                      <span className="rounded bg-terminal-border px-1.5 py-0.5 text-[10px] text-terminal-muted">
                        {signal.timeframe}
                      </span>
                      <span
                        className={`flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium ${config.badge}`}
                      >
                        <Icon className="h-2.5 w-2.5" />
                        {signal.severity}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
