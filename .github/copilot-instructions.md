# Copilot Instructions — Local Market Analyzer

## Project Overview

**Local Market Analyzer** is a local-first AI-powered market analysis terminal. It combines real-time market data (Yahoo Finance), configurable technical indicators, and LLM-powered interpretation to generate trading signals. The system runs entirely on-machine (except for market data fetches and optional remote LLM endpoints).

## Architecture

```
Frontend (React + TypeScript + Vite + Tailwind)
   │  REST/JSON over HTTP
Backend (FastAPI + LangGraph)
   ├── API Layer        → routes for health, market, analysis, config
   ├── LangGraph Workflow → compute_features → generate_signal → llm_interpret
   ├── Services         → market data (yfinance), indicators (ta), signal engine, scheduler
   ├── LLM Adapters     → openai_compat (Ollama/vLLM/etc.), llamacpp (native)
   ├── Prompts          → YAML templates with variable substitution
   └── Core             → Pydantic models, settings, abstract interfaces
```

## Directory Layout

```
/
├── backend/                  # FastAPI application (Python ≥3.11)
│   ├── app/
│   │   ├── main.py           # App startup, lifespan, CORS
│   │   ├── config.yaml       # Watchlist + LLM defaults (hot-reloaded)
│   │   ├── api/
│   │   │   ├── app.py        # FastAPI app factory
│   │   │   ├── deps.py       # Dependency injection (providers, workflow)
│   │   │   ├── schemas.py    # Pydantic request/response models
│   │   │   └── routes/       # health, market, analysis, config endpoints
│   │   ├── core/
│   │   │   ├── config.py     # Pydantic settings (env + YAML hybrid)
│   │   │   ├── models.py     # Domain objects (Indicators, Signal, etc.)
│   │   │   └── interfaces.py # Abstract base classes (clean architecture ports)
│   │   ├── graph/
│   │   │   ├── workflow.py   # LangGraph graph builders (full + signals-only)
│   │   │   ├── nodes.py      # Graph node functions (compute, signal, LLM)
│   │   │   └── state.py      # TradingState TypedDict
│   │   ├── llm/
│   │   │   ├── factory.py    # create_llm_provider() factory
│   │   │   ├── openai_compat.py  # OpenAI-compatible provider (Ollama, vLLM, etc.)
│   │   │   └── llamacpp.py       # Native llama.cpp HTTP provider
│   │   ├── prompts/
│   │   │   ├── default.yaml  # Prompt templates (trading_analysis, sentiment)
│   │   │   └── loader.py     # Template rendering with variable substitution
│   │   └── services/
│   │       ├── market.py     # YFinanceProvider (OHLCV data)
│   │       ├── signals.py    # SignalEngine (rule-based scoring)
│   │       └── scheduler.py  # Background watchlist analysis loop
│   └── pyproject.toml        # Python dependencies and project metadata
│
├── frontend/                 # React SPA (Node ≥18)
│   ├── src/
│   │   ├── App.tsx           # Root component, view switching, global state
│   │   ├── api.ts            # Backend HTTP client functions
│   │   ├── types.ts          # TypeScript interfaces mirroring backend schemas
│   │   ├── hooks.ts          # useMarketData() custom hook
│   │   ├── data.ts           # Static/mock data
│   │   └── components/
│   │       ├── Header.tsx       # Logo, search, health indicator, nav
│   │       ├── Watchlist.tsx    # Symbol list with signal badges
│   │       ├── StockPanel.tsx   # Detail view: price, indicators, signal
│   │       ├── SignalFeed.tsx   # Real-time signal notifications
│   │       └── ConfigPanel.tsx  # LLM settings + watchlist editor
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── Makefile                  # Dev commands (see below)
└── .env                      # Root-level env (may exist)
```

### Legacy Top-Level Modules

`graph/`, `market/`, `strategy/` at the repo root are older standalone modules. The active code lives in `backend/app/`. Do not add new code to the top-level modules.

## Key Conventions

- **Backend**: Python 3.11+, FastAPI, async/await, Pydantic v2 for validation and settings.
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS. Terminal/hacker UI aesthetic (dark theme, cyan/green accents, monospace).
- **Config priority**: Environment variables > `config.yaml` > hardcoded defaults. API keys are env-only (never in YAML).
- **Clean architecture**: Core defines abstract interfaces (`interfaces.py`); services implement them. Dependency injection via FastAPI `Depends()` in `deps.py`.
- **LangGraph workflows**: Two pipelines — full (with LLM) and signals-only (lightweight). Conditional routing skips downstream nodes on errors.
- **Indicators are opt-in**: SMA is always computed. RSI, MACD, and Bollinger Bands must be enabled per watchlist entry in `config.yaml`.

## Signal Generation

The rule-based signal engine scores each symbol:

| Indicator | Weight | Bullish | Bearish |
|-----------|--------|---------|---------|
| SMA crossover | ±1 | short > long | short < long |
| RSI | ±2 | < oversold (30) | > overbought (70) |
| MACD histogram | ±1 | positive | negative |
| Bollinger %B | ±1 | < 0.2 | > 0.8 |

Signal = BUY if score ≥ 60% of max, SELL if ≤ −60%, else HOLD. Confidence = abs(score) / max_score.

## LLM Integration

- **Factory pattern**: `LLM_PROVIDER` env var selects `openai_compat` or `llamacpp`.
- The LLM receives indicator data + rule-based signal and returns a JSON object with `summary` and `recommendation`.
- If the LLM fails, the system falls back to the rule-based signal.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/market/price/{symbol}` | Latest price |
| GET | `/api/market/watchlist` | Watchlist with signals |
| POST | `/api/analysis` | Full analysis pipeline |
| POST | `/api/analysis/batch` | Batch analysis |
| GET | `/api/analysis/scheduled` | Latest scheduled results (snapshot) |
| GET | `/api/analysis/stream` | SSE stream — pushes `AnalysisResponse` JSON on each scheduler cycle |
| GET | `/api/config` | Read config |
| PUT | `/api/config` | Update config |
| GET | `/api/config/prompts` | List available prompt names |

## Real-time Updates (SSE)

The frontend receives analysis results without polling via Server-Sent Events:

- **Backend**: `scheduler.py` maintains a set of `asyncio.Queue` objects (`_subscribers`), one per connected client. After each `_run_cycle`, results are broadcast by calling `q.put_nowait(result)` on every queue.
- **Endpoint**: `GET /api/analysis/stream` opens a long-lived `StreamingResponse` with `Content-Type: text/event-stream`. Each event is `data: <AnalysisResponse JSON>\n\n`. A `:keepalive` ping is sent every 20 s to prevent proxy timeouts.
- **Frontend**: `subscribeAnalysisStream(onResult)` in `api.ts` wraps `EventSource`. The `useMarketData` hook opens this connection when the backend is online and closes it on cleanup. Every event updates the watchlist badge (price, signal, confidence) and refreshes the stock detail panel if the symbol is currently selected.
- **Latency**: updates arrive within milliseconds of the scheduler completing a cycle, regardless of the configured `interval_seconds`.


## Common Commands

```bash
make install          # Install all dependencies (backend venv + frontend npm)
make dev              # Run backend (:8000) + frontend (:5173) concurrently
make backend          # Start FastAPI only
make frontend         # Start Vite only
make lint             # Lint backend (ruff) + frontend (eslint)
make typecheck        # TypeScript type checking
make build            # Production build (frontend)
make clean            # Remove build artifacts
make setup            # Full setup (install + create .env)
```

## Tech Stack Reference

**Backend**: FastAPI, uvicorn, Pydantic v2, pydantic-settings, httpx, pandas, numpy, yfinance, ta (technical analysis), langgraph, PyYAML, python-dotenv.

**Frontend**: React 18, TypeScript 5.6, Vite, Tailwind CSS 3.4, lucide-react, ESLint.

## When Making Changes

- Backend route handlers live in `backend/app/api/routes/`. Register new routes in the respective `__init__.py`.
- Add new indicators in `backend/app/services/market.py` (computation) and `backend/app/services/signals.py` (scoring rules).
- Frontend API calls go in `frontend/src/api.ts`; types in `frontend/src/types.ts`.
- New prompts go in `backend/app/prompts/` as YAML files following the `default.yaml` structure.
- Keep frontend and backend schemas in sync — `schemas.py` ↔ `types.ts`.
