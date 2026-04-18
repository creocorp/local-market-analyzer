from __future__ import annotations

from pydantic import BaseModel, Field


class PromptInput(BaseModel):
    """A single prompt to run against the LLM."""
    file: str = "prompts"
    name: str = "trading_analysis"


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, pattern=r"^[A-Z0-9.]+$")
    prompts: list[PromptInput] = Field(
        default_factory=lambda: [PromptInput()],
        description="Prompt templates to run. Each entry maps to a YAML file + key in backend/config/.",
    )
    include_llm: bool = True


class IndicatorsResponse(BaseModel):
    close: float
    sma_short: float
    sma_long: float
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_diff: float | None = None
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    bb_pband: float | None = None


class SignalResponse(BaseModel):
    signal: str
    score: int
    confidence: float
    reasons: list[str]


class LLMResultItem(BaseModel):
    prompt_name: str
    summary: str
    recommendation: str


class AnalysisResponse(BaseModel):
    symbol: str
    indicators: IndicatorsResponse | None = None
    signal: SignalResponse | None = None
    llm_results: list[LLMResultItem] | None = None
    error: str | None = None


class WatchlistItemResponse(BaseModel):
    symbol: str
    price: float
    change: float
    signal: str | None = None
    score: int | None = None
    confidence: float | None = None


class HealthResponse(BaseModel):
    status: str
    version: str


# ── Config schemas ────────────────────────────────────────────────────────────

class SMAConfig(BaseModel):
    short_period: int = 20
    long_period: int = 50


class RSIConfig(BaseModel):
    enabled: bool = False
    period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0


class MACDConfig(BaseModel):
    enabled: bool = False
    fast: int = 12
    slow: int = 26
    signal: int = 9


class BBConfig(BaseModel):
    enabled: bool = False
    period: int = 20
    std: int = 2


class IndicatorConfigPayload(BaseModel):
    sma: SMAConfig = Field(default_factory=SMAConfig)
    rsi: RSIConfig = Field(default_factory=RSIConfig)
    macd: MACDConfig = Field(default_factory=MACDConfig)
    bb: BBConfig = Field(default_factory=BBConfig)


class PromptRefConfig(BaseModel):
    file: str = "default"
    name: str = "trading_analysis"


class WatchlistEntryConfig(BaseModel):
    """Exactly one interval field should be set; most granular wins: seconds > minutes > hours > days."""
    name: str
    enabled: bool = False
    symbols: list[str] = []
    interval_seconds: int | None = None
    interval_minutes: int | None = None
    interval_hours: int | None = None
    interval_days: int | None = None
    include_llm: bool = True
    prompts: list[PromptRefConfig] = Field(default_factory=lambda: [PromptRefConfig()])
    indicators: IndicatorConfigPayload = Field(default_factory=IndicatorConfigPayload)


class LLMConfig(BaseModel):
    """LLM configuration — api_key is intentionally excluded (env-only)."""
    provider: str = "openai_compat"
    base_url: str = "http://localhost:11434/v1"
    model: str = ""
    temperature: float = 0.2
    max_tokens: int = 2048
    timeout: int = 120


class AppConfigPayload(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    watchlist: list[WatchlistEntryConfig] = []
