# Local Market Analyzer

A local-first AI-powered market analysis terminal. Send your own technical indicator data to any LLM you choose and get back natural language summaries and signal recommendations — all running on your machine. Your data never leaves your machine.

![Stack](https://img.shields.io/badge/Python-FastAPI-009688?style=flat) ![Stack](https://img.shields.io/badge/React-TypeScript-61DAFB?style=flat) ![Stack](https://img.shields.io/badge/LLM-Ollama%20%7C%20llama.cpp-orange?style=flat)

> **Disclaimer:** This project is for educational and research purposes only. It does not constitute financial advice, investment advice, trading advice, or any other type of advice. The signals, scores, and LLM-generated summaries produced by this software are the output of rule-based heuristics and language models — they are not predictions of future price movements. Do not make any financial or investment decisions based on the output of this software. Always do your own research and consult a qualified financial professional before trading.

## Quick Start

```bash
# 1. Clone & install
make setup          # creates .env, installs backend + frontend deps

# 2. Start everything
make dev            # backend on :8000, frontend on :5173
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Architecture

```
frontend/          → React + Vite + Tailwind (terminal-style UI)
backend/
  app/
    api/           → FastAPI routes (REST endpoints)
    core/          → Config, domain models, interfaces
    services/      → Market data (yfinance), signal engine, scheduler
    graph/         → LangGraph workflows (features → signals → LLM)
    llm/           → Pluggable LLM adapters (OpenAI-compat, llama.cpp)
    prompts/       → YAML prompt templates
```

## Configuration

All configuration is done through `backend/.env`. Copy from `.env.example`:

```bash
cp backend/.env.example backend/.env
```

### Watchlist Symbols

```env
MARKET_SYMBOLS=["AAPL","MSFT","TSLA","SPY","NVDA","AMZN"]
```

These symbols appear in the left sidebar and are analyzed on page load. You can also search for any ticker using the search bar in the header.

### Technical Indicators

SMA (Simple Moving Average) is **always computed**. Other indicators are opt-in:

```env
# Only SMA (default)
INDICATOR_ENABLED=["sma"]

# SMA + RSI
INDICATOR_ENABLED=["sma","rsi"]

# All indicators
INDICATOR_ENABLED=["sma","rsi","macd","bb"]
```

Available indicator groups:
| Group | Indicators | Env Params |
|-------|-----------|------------|
| `sma` | SMA Short, SMA Long | `INDICATOR_SMA_SHORT`, `INDICATOR_SMA_LONG` |
| `rsi` | Relative Strength Index | `INDICATOR_RSI_PERIOD`, `INDICATOR_RSI_OVERSOLD`, `INDICATOR_RSI_OVERBOUGHT` |
| `macd` | MACD, Signal, Histogram | `INDICATOR_MACD_FAST`, `INDICATOR_MACD_SLOW`, `INDICATOR_MACD_SIGNAL` |
| `bb` | Bollinger Bands (upper/mid/lower/%B) | `INDICATOR_BB_PERIOD`, `INDICATOR_BB_STD` |

Only enabled indicators appear in the UI, signal scoring, and LLM prompts.

### LLM Provider

The system supports two LLM backends:

**Option A: Ollama (recommended for local)**
```env
LLM_PROVIDER=openai_compat
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:14b
LLM_API_KEY=no-key
```

**Option B: llama.cpp server**
```env
LLM_PROVIDER=llamacpp
LLM_BASE_URL=http://localhost:8080
```

**Option C: Any OpenAI-compatible API** (vLLM, LM Studio, OpenRouter, etc.)
```env
LLM_PROVIDER=openai_compat
LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=your-model-name
LLM_API_KEY=your-api-key
```

To use AI analysis, you need a running LLM. The easiest way:

```bash
# Install Ollama: https://ollama.com
ollama pull qwen2.5:14b
ollama serve                # Starts on :11434
```

### Scheduled Analysis

Run automated analysis at regular intervals:

```env
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_MINUTES=60        # Run every hour
SCHEDULER_SYMBOLS=["AAPL","TSLA"]    # Leave empty to use MARKET_SYMBOLS
SCHEDULER_INCLUDE_LLM=true           # Include AI analysis (requires LLM running)
```

Results are available via `GET /api/analysis/scheduled` and will appear in the signal feed.

## Prompt Templates

Prompts sent to the LLM are defined in YAML files under `backend/config/` (copy from `prompts.example.yaml`).

### `prompts.yaml` (example structure)

```yaml
prompts:
  trading_analysis:
    system: |
      You are a technical analysis assistant for a research tool.
      Summarize indicator data — do not give financial advice.
      Respond in valid JSON with keys: "summary" and "recommendation".
      "recommendation" must be BUY, SELL, or HOLD (indicator-based, not personal advice).
    user: |
      Symbol: {symbol}
      Current Price: ${close}
      Technical Indicators:
      {indicators_text}
      Rule-based signal: {signal}  (score={score}, confidence={confidence})
      Signal reasons:
      {reasons}
      ...
```

**Variables** available in prompts:
- `{symbol}`, `{close}` — always available
- `{indicators_text}` — auto-generated from enabled indicators
- `{signal}`, `{score}`, `{confidence}`, `{reasons}` — from the rule-based engine

**Custom prompts:** Create a new YAML file in `backend/config/` (e.g. `crypto.yaml`) with the same structure, then reference it in `settings.yaml` with `file: crypto`.

## Charts

The chart area is currently a placeholder. To add live charts, you can:

1. **Lightweight Charts** (recommended) — add the [`lightweight-charts`](https://github.com/niclas-nicol/lightweight-charts-react-wrapper) npm package to render candlestick/line charts from the OHLCV data the backend already provides via `GET /api/market/price/{symbol}`
2. **TradingView Widget** — embed the free TradingView widget for real-time charting

The backend already serves historical OHLCV data through yfinance that can feed any charting library.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/market/price/{symbol}` | Latest price for a symbol |
| `GET` | `/api/market/watchlist` | Prices + signals for configured symbols |
| `POST` | `/api/analysis` | Full analysis pipeline (indicators + signal + optional LLM) |
| `POST` | `/api/analysis/batch` | Analyze multiple symbols |
| `GET` | `/api/analysis/scheduled` | Latest results from background scheduler |
| `GET` | `/docs` | Interactive API docs (Swagger) |

### Example: Run analysis with LLM

```bash
curl -X POST http://localhost:8000/api/analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "include_llm": true}'
```

### Example: Signals only (no LLM)

```bash
curl -X POST http://localhost:8000/api/analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "include_llm": false}'
```

## Make Targets

```
make help              Show all targets
make setup             Full project setup (install + .env)
make dev               Run backend + frontend concurrently
make backend           Start FastAPI backend only
make frontend          Start Vite frontend only
make build             Build frontend for production
make lint              Lint all code
make clean             Remove build artifacts
```

## Project Structure

```
backend/
  .env                 ← Your configuration (gitignored)
  .env.example         ← Template with all options documented
  app/
    core/
      config.py        ← Pydantic settings (reads .env)
      models.py        ← Domain models (Indicators, Signal, etc.)
      interfaces.py    ← Abstract base classes (ports)
    services/
      market.py        ← yfinance data provider + indicator computation
      signals.py       ← Rule-based signal engine
      scheduler.py     ← Background scheduled analysis
    graph/
      nodes.py         ← LangGraph node functions
      workflow.py      ← Graph definitions (full + signals-only)
      state.py         ← TypedDict for graph state
    llm/
      factory.py       ← Provider factory + registry
      openai_compat.py ← OpenAI-compatible adapter (Ollama, vLLM, etc.)
      llamacpp.py      ← llama.cpp native adapter
    prompts/
      default.yaml     ← Default prompt templates
      loader.py        ← YAML template loader
    api/
      app.py           ← FastAPI app factory
      schemas.py       ← Request/response models
      deps.py          ← Dependency injection
      routes/          ← Route handlers

frontend/
  src/
    App.tsx            ← Main layout
    hooks.ts           ← Data fetching hook
    api.ts             ← Backend API client
    types.ts           ← TypeScript interfaces
    components/
      Header.tsx       ← Top bar with search + status
      Watchlist.tsx     ← Left sidebar
      StockPanel.tsx   ← Center panel (price, indicators, signals)
      SignalFeed.tsx   ← Right sidebar
```
