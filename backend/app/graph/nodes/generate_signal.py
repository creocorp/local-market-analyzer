"""Generate Signal Node — runs the rule-based scoring engine.

Reads the ``indicators`` dict produced by ``compute_features`` and outputs a
BUY / SELL / HOLD signal with a numeric score and confidence.

Scoring weights are defined in ``services/signals.py``.
Each result is persisted to ``signal_results`` (and a linked
``indicator_snapshots`` row) so historical signals can be reviewed later.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.graph.state import TradingState
from app.services.signals import SignalEngine

logger = logging.getLogger(__name__)
_signal_engine = SignalEngine()


def _persist_signal(state: TradingState, result) -> int | None:
    """Write IndicatorSnapshot + SignalResult rows; return the SignalResult id."""
    try:
        from app.db.session import get_session
        from app.db.models import IndicatorSnapshot, SignalResult

        ind = state["indicators"]
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        snapshot = IndicatorSnapshot(
            symbol=state["symbol"],
            interval="1d",
            as_of=now,
            computed_at=now,
            close=ind["close"],
            sma_short=ind.get("sma_short"),
            sma_long=ind.get("sma_long"),
            rsi=ind.get("rsi"),
            macd=ind.get("macd"),
            macd_signal=ind.get("macd_signal"),
            macd_diff=ind.get("macd_diff"),
            bb_upper=ind.get("bb_upper"),
            bb_middle=ind.get("bb_middle"),
            bb_lower=ind.get("bb_lower"),
            bb_pband=ind.get("bb_pband"),
        )

        signal_row = SignalResult(
            symbol=state["symbol"],
            generated_at=now,
            signal=result.signal.value,
            score=result.score,
            confidence=result.confidence,
            reasons_json=json.dumps(result.reasons),
        )

        with get_session() as session:
            session.add(snapshot)
            session.flush()
            signal_row.snapshot_id = snapshot.id
            session.add(signal_row)
            session.flush()
            return signal_row.id
    except Exception:
        logger.debug("Signal persistence failed", exc_info=True)
        return None


def generate_signal(state: TradingState) -> dict:
    """Score the latest indicators and produce a trading signal.

    Reads
    -----
    indicators : dict

    Writes
    ------
    signal           : str   — "BUY", "SELL", or "HOLD"
    score            : int
    confidence       : float
    reasons          : list[str]
    signal_result_id : int | None  — DB row id for downstream LLM caching
    """
    if state.get("error") or not state.get("indicators"):
        return {}

    from app.core.models import Indicators

    ind = Indicators(**state["indicators"])
    result = _signal_engine.generate(ind)
    signal_result_id = _persist_signal(state, result)

    return {
        "signal": result.signal.value,
        "score": result.score,
        "confidence": result.confidence,
        "reasons": result.reasons,
        "signal_result_id": signal_result_id,
    }
