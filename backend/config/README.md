# Configuration Directory

All YAML configuration for Local Market Analyzer lives here.

> **Disclaimer:** This software is for educational and research purposes only. The outputs it produces are not financial advice. See the root `README.md` for the full disclaimer.

| File | Purpose | Committed? |
|------|---------|------------|
| `settings.yaml` | App settings — LLM connection, watchlist entries, indicator tuning | No (gitignored) |
| `settings.example.yaml` | Starter template — copy to `settings.yaml` | Yes |
| `prompts.yaml` | Prompt templates — system/user pairs used by LLM nodes | No (gitignored) |
| `prompts.example.yaml` | Starter template — copy to `prompts.yaml` | Yes |

## Adding Custom Prompts

1. Create a new YAML file in this directory (e.g. `crypto.yaml`).
2. Follow the same structure as `prompts.example.yaml`:

```yaml
prompts:
  my_prompt:
    system: |
      You are a ...
    user: |
      Symbol: {symbol}
      Current Price: ${close}
      {indicators_text}
      ...
```

3. Available template variables (passed automatically by the LLM node):
   - `{symbol}` — ticker symbol
   - `{close}` — latest closing price
   - `{indicators_text}` — formatted indicator values
   - `{signal}` — rule-based signal (BUY/SELL/HOLD)
   - `{score}` — numeric score
   - `{confidence}` — confidence 0–1
   - `{reasons}` — bullet list of signal reasons

4. Reference your prompt in `settings.yaml` watchlist entries:

```yaml
prompts:
  - file: crypto        # your new YAML filename (without .yaml)
    name: my_prompt     # the key inside the YAML
```

5. Or pass it via the API:

```json
{
  "symbol": "BTC-USD",
  "prompts": [{"file": "crypto", "name": "my_prompt"}],
  "include_llm": true
}
```
