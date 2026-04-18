from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Indicators:
    close: float
    sma_short: float
    sma_long: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_diff: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_pband: Optional[float] = None


@dataclass(frozen=True)
class SignalResult:
    signal: Signal
    score: int
    confidence: float
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LLMAnalysis:
    summary: str
    recommendation: Signal


@dataclass
class AnalysisResult:
    symbol: str
    indicators: Indicators | None = None
    signal_result: SignalResult | None = None
    llm_analysis: LLMAnalysis | None = None
    error: str | None = None
