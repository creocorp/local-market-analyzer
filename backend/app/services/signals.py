from __future__ import annotations

from app.core.config import IndicatorSettings
from app.core.models import Indicators, Signal, SignalResult


class SignalEngine:
    """Rule-based signal generator."""

    def __init__(self, ind_settings: IndicatorSettings | None = None) -> None:
        cfg = ind_settings or IndicatorSettings()
        self._oversold = cfg.rsi_oversold
        self._overbought = cfg.rsi_overbought

    def generate(self, indicators: Indicators) -> SignalResult:
        reasons: list[str] = []
        score = 0
        max_score = 1  # SMA always contributes 1

        # RSI (opt-in)
        if indicators.rsi is not None:
            max_score += 2
            if indicators.rsi < self._oversold:
                score += 2
                reasons.append(f"RSI oversold ({indicators.rsi:.1f} < {self._oversold})")
            elif indicators.rsi > self._overbought:
                score -= 2
                reasons.append(f"RSI overbought ({indicators.rsi:.1f} > {self._overbought})")
            else:
                reasons.append(f"RSI neutral ({indicators.rsi:.1f})")

        # MACD histogram (opt-in)
        if indicators.macd_diff is not None:
            max_score += 1
            if indicators.macd_diff > 0:
                score += 1
                reasons.append(f"MACD histogram positive ({indicators.macd_diff:.4f})")
            else:
                score -= 1
                reasons.append(f"MACD histogram negative ({indicators.macd_diff:.4f})")

        # Bollinger Band position (opt-in)
        if indicators.bb_pband is not None:
            max_score += 1
            if indicators.bb_pband < 0.2:
                score += 1
                reasons.append(f"Price near lower Bollinger Band (pband={indicators.bb_pband:.2f})")
            elif indicators.bb_pband > 0.8:
                score -= 1
                reasons.append(f"Price near upper Bollinger Band (pband={indicators.bb_pband:.2f})")

        # SMA crossover (always)
        if indicators.sma_short > indicators.sma_long:
            score += 1
            reasons.append("SMA short > SMA long (bullish crossover)")
        else:
            score -= 1
            reasons.append("SMA short < SMA long (bearish crossover)")

        # Determine signal – scale thresholds relative to max_score
        threshold = max(2, max_score * 0.6)
        if score >= threshold:
            signal = Signal.BUY
        elif score <= -threshold:
            signal = Signal.SELL
        else:
            signal = Signal.HOLD

        confidence = round(min(abs(score) / max_score, 1.0), 2)

        return SignalResult(
            signal=signal,
            score=score,
            confidence=confidence,
            reasons=reasons,
        )
