import { useState } from "react";
import { Header } from "./components/Header";
import { Watchlist } from "./components/Watchlist";
import { StockPanel } from "./components/StockPanel";
import { SignalFeed } from "./components/SignalFeed";
import { ConfigPanel } from "./components/ConfigPanel";
import { useMarketData } from "./hooks";
import { Loader2 } from "lucide-react";

function App() {
  const [activeView, setActiveView] = useState<"market" | "config">("market");
  const {
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
  } = useMarketData();

  const handleSearch = (symbol: string) => {
    searchSymbol(symbol);
    setActiveView("market");
  };

  return (
    <div className="flex h-screen flex-col bg-terminal-bg text-slate-300">
      <Header
        onRefresh={refresh}
        onSearch={handleSearch}
        backendOnline={backendOnline}
        onConfigToggle={() =>
          setActiveView((v) => (v === "config" ? "market" : "config"))
        }
        configActive={activeView === "config"}
      />
      <div className="flex flex-1 overflow-hidden">
        <Watchlist
          items={watchlist}
          selectedSymbol={selectedSymbol}
          onSelect={setSelectedSymbol}
        />

        {activeView === "config" ? (
          <ConfigPanel />
        ) : loading && !stockDetail ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="mx-auto h-8 w-8 text-cyan-400 animate-spin" />
              <p className="mt-3 text-sm text-terminal-muted">
                Loading market data...
              </p>
            </div>
          </div>
        ) : error && !stockDetail ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center max-w-md">
              <p className="text-red-400 text-sm">{error}</p>
              <p className="mt-2 text-xs text-terminal-muted">
                Make sure the backend is running on port 8000
              </p>
            </div>
          </div>
        ) : stockDetail ? (
          <StockPanel stock={stockDetail} loading={loading} />
        ) : null}

        <SignalFeed signals={signals} />
      </div>
    </div>
  );
}

export default App;
