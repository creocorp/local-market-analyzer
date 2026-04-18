"""SQLModel table definitions.

Four tables mirror the four stages of the analysis pipeline:

    ohlcv_bars           — raw price cache (write-through from YFinanceProvider)
    indicator_snapshots  — computed indicator values for a symbol at a point-in-time
    signal_results       — rule-based BUY/SELL/HOLD output + JSON reason list
    llm_analyses         — LLM summary/recommendation per prompt, keyed to a signal

Adding a new table
------------------
1. Define a class that inherits ``SQLModel, table=True``.
2. Import it in ``session.py`` so ``SQLModel.metadata.create_all()`` picks it up.
3. Add FK relationships as needed using ``Optional[int] = Field(foreign_key=...)``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class OHLCVBar(SQLModel, table=True):
    """One OHLCV candle for a symbol/interval pair.

    The UNIQUE constraint on (symbol, interval, timestamp) means upserts
    can be done safely by catching ``IntegrityError`` and skipping duplicates.
    """

    __tablename__ = "ohlcv_bars"
    __table_args__ = (
        UniqueConstraint("symbol", "interval", "timestamp", name="uq_ohlcv_symbol_interval_ts"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    interval: str = Field(default="1d")
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class IndicatorSnapshot(SQLModel, table=True):
    """Latest indicator values computed from an OHLCV dataset.

    Stored once per (symbol, interval, as_of) combination so historical
    snapshots are preserved for back-testing or audit purposes.
    """

    __tablename__ = "indicator_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    interval: str = Field(default="1d")
    as_of: datetime = Field(description="Timestamp of the most recent OHLCV bar used")
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    close: float
    sma_short: Optional[float] = None
    sma_long: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_diff: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_pband: Optional[float] = None


class SignalResult(SQLModel, table=True):
    """Rule-based signal output for a given indicator snapshot.

    ``reasons`` is stored as a JSON-encoded list of strings.
    """

    __tablename__ = "signal_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_id: Optional[int] = Field(default=None, foreign_key="indicator_snapshots.id")
    symbol: str = Field(index=True)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    signal: str  # "BUY" | "SELL" | "HOLD"
    score: int
    confidence: float
    reasons_json: str = Field(default="[]", description="JSON-encoded list[str]")


class LLMAnalysis(SQLModel, table=True):
    """LLM-generated summary and recommendation for a signal result.

    One row per (signal_result, prompt_name) pair so multiple prompts
    from the same analysis run are each stored independently.

    ``cached_until`` lets callers skip LLM calls for very recent results.
    """

    __tablename__ = "llm_analyses"

    id: Optional[int] = Field(default=None, primary_key=True)
    signal_result_id: Optional[int] = Field(default=None, foreign_key="signal_results.id")
    symbol: str = Field(index=True)
    prompt_name: str = Field(index=True)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    cached_until: Optional[datetime] = None

    summary: str
    recommendation: str
