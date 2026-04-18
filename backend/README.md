# Local Market Analyzer — Backend

Local-first AI market analysis terminal with configurable LLM integration and technical indicators.

## Architecture

```
backend/
├── app/
│   ├── core/           # Domain models, interfaces (ports), config
│   ├── services/       # Business logic (market data, signal engine)
│   ├── llm/            # Pluggable LLM adapters (OpenAI-compat, llama.cpp)
│   ├── prompts/        # Configurable YAML prompt templates
│   ├── graph/          # LangGraph workflows (orchestration)
│   └── api/            # FastAPI HTTP layer
```

## Quick Start

```bash
cd backend

# Create virtualenv & install
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your LLM settings

# Run
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/market/price/{symbol}` | Latest price |
| `GET` | `/api/market/watchlist` | Watchlist with signals |
| `POST` | `/api/analysis` | Full analysis pipeline |
| `POST` | `/api/analysis/batch` | Batch analysis |

## LLM Providers

### OpenAI-Compatible (Ollama, vLLM, LiteLLM, OpenAI)

```env
LLM_PROVIDER=openai_compat
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:14b
LLM_API_KEY=no-key
```

### llama.cpp Server

```env
LLM_PROVIDER=llamacpp
LLM_BASE_URL=http://localhost:8080
```

## Custom Prompts

Add YAML files to `app/prompts/`:

```yaml
prompts:
  my_custom_analysis:
    system: |
      You are a ...
    user: |
      Symbol: {symbol}
      Price: ${close}
      ...
```

Then reference in API calls:
```json
{
  "symbol": "AAPL",
  "prompt_file": "my_custom",
  "prompt_name": "my_custom_analysis"
}
```
