"""Compute Features Node — fetches OHLCV data and calculates technical indicators.

This is typically the first node in any trading workflow. It populates the
``indicators`` key in TradingState so downstream nodes can generate signals
or call the LLM.

To customise which indicators are computed, edit the watchlist entry's
``indicators`` block in ``backend/config/config.yaml``.
"""
from __future__ import annotations

import logging
from dataclasses import asdict

from app.graph.state import TradingState
from app.services.market import YFinanceProvider, TAIndicatorService

logger = logging.getLogger(__name__)

# Shared service instances (stateless, safe to reuse)
_market = YFinanceProvider()
_indicators = TAIndicatorService()


def compute_features(state: TradingState) -> dict:
    """Fetch OHLCV data and compute technical indicators for ``state["symbol"]``.

    Writes
    ------
    indicators : dict   — latest indicator snapshot (sma, rsi, macd, bb, …)
    error      : str | None
    """
    try:
        symbol = state["symbol"]
        df = _market.fetch_ohlcv(symbol)
        df = _indicators.compute(df)
        ind = _indicators.latest(df)
        return {"indicators": asdict(ind), "error": None}
    except Exception as e:
        logger.exception("compute_features failed for %s", state.get("symbol"))
        return {"indicators": None, "error": str(e)}
