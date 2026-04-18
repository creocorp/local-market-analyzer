from __future__ import annotations

import logging
from datetime import datetime, timezone

import pandas as pd
import ta
import yfinance as yf
from sqlalchemy.exc import IntegrityError

from app.core.config import IndicatorSettings
from app.core.interfaces import MarketDataProvider, IndicatorService
from app.core.models import Indicators

logger = logging.getLogger(__name__)


def _persist_ohlcv(df: pd.DataFrame, symbol: str, interval: str) -> None:
    """Write new OHLCV rows to the database, skipping duplicates.

    Called after every successful yfinance fetch so the local cache stays
    up-to-date without blocking the caller on failures.
    """
    try:
        from app.db.session import get_session
        from app.db.models import OHLCVBar

        fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
        rows = []
        for ts, row in df.iterrows():
            ts_naive = ts.to_pydatetime().replace(tzinfo=None)
            rows.append(
                OHLCVBar(
                    symbol=symbol,
                    interval=interval,
                    timestamp=ts_naive,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                    fetched_at=fetched_at,
                )
            )

        with get_session() as session:
            for bar in rows:
                try:
                    session.add(bar)
                    session.flush()  # flush individually to isolate constraint errors
                except IntegrityError:
                    session.rollback()  # skip duplicate bar, keep going
    except Exception:
        logger.debug("OHLCV persistence skipped (DB not ready yet)", exc_info=True)


class YFinanceProvider(MarketDataProvider):
    """Fetch OHLCV data from Yahoo Finance with a local SQLite write-through cache."""

    def fetch_ohlcv(
        self,
        symbol: str,
        period: str | None = None,
        interval: str | None = None,
    ) -> pd.DataFrame:
        period = period or "6mo"
        interval = interval or "1d"

        logger.info("yfinance  GET  history  symbol=%s  period=%s  interval=%s", symbol, period, interval)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            logger.warning("yfinance  EMPTY  symbol=%s  period=%s  interval=%s", symbol, period, interval)
            raise ValueError(f"No data returned for symbol '{symbol}'")

        df.index = pd.to_datetime(df.index)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.dropna(inplace=True)

        logger.info("yfinance  OK    symbol=%s  rows=%d  latest_close=%.4f", symbol, len(df), float(df["Close"].iloc[-1]))
        _persist_ohlcv(df, symbol, interval)
        return df

    def get_latest_price(self, symbol: str) -> float:
        logger.info("yfinance  GET  latest_price  symbol=%s", symbol)
        df = self.fetch_ohlcv(symbol, period="5d", interval="1d")
        price = float(df["Close"].iloc[-1])
        logger.info("yfinance  OK   latest_price  symbol=%s  price=%.4f", symbol, price)
        return price


class TAIndicatorService(IndicatorService):
    """Compute technical indicators using the `ta` library."""

    def __init__(self, ind_settings: IndicatorSettings | None = None) -> None:
        self._cfg = ind_settings or IndicatorSettings()

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # SMA – always computed
        df["sma_short"] = ta.trend.SMAIndicator(
            close=df["Close"], window=self._cfg.sma_short
        ).sma_indicator()
        df["sma_long"] = ta.trend.SMAIndicator(
            close=df["Close"], window=self._cfg.sma_long
        ).sma_indicator()

        # RSI – opt-in
        if self._cfg.is_enabled("rsi"):
            df["rsi"] = ta.momentum.RSIIndicator(
                close=df["Close"], window=self._cfg.rsi_period
            ).rsi()

        # MACD – opt-in
        if self._cfg.is_enabled("macd"):
            macd = ta.trend.MACD(
                close=df["Close"],
                window_fast=self._cfg.macd_fast,
                window_slow=self._cfg.macd_slow,
                window_sign=self._cfg.macd_signal,
            )
            df["macd"] = macd.macd()
            df["macd_signal"] = macd.macd_signal()
            df["macd_diff"] = macd.macd_diff()

        # Bollinger Bands – opt-in
        if self._cfg.is_enabled("bb"):
            bb = ta.volatility.BollingerBands(
                close=df["Close"],
                window=self._cfg.bb_period,
                window_dev=self._cfg.bb_std,
            )
            df["bb_upper"] = bb.bollinger_hband()
            df["bb_middle"] = bb.bollinger_mavg()
            df["bb_lower"] = bb.bollinger_lband()
            df["bb_pband"] = bb.bollinger_pband()

        df.dropna(inplace=True)
        return df

    def latest(self, df: pd.DataFrame) -> Indicators:
        if df.empty:
            raise ValueError("Indicator DataFrame is empty — not enough historical data to compute indicators")
        row = df.iloc[-1]

        kwargs: dict = {
            "close": round(float(row["Close"]), 4),
            "sma_short": round(float(row["sma_short"]), 4),
            "sma_long": round(float(row["sma_long"]), 4),
        }

        if self._cfg.is_enabled("rsi"):
            kwargs["rsi"] = round(float(row["rsi"]), 2)

        if self._cfg.is_enabled("macd"):
            kwargs["macd"] = round(float(row["macd"]), 4)
            kwargs["macd_signal"] = round(float(row["macd_signal"]), 4)
            kwargs["macd_diff"] = round(float(row["macd_diff"]), 4)

        if self._cfg.is_enabled("bb"):
            kwargs["bb_upper"] = round(float(row["bb_upper"]), 4)
            kwargs["bb_middle"] = round(float(row["bb_middle"]), 4)
            kwargs["bb_lower"] = round(float(row["bb_lower"]), 4)
            kwargs["bb_pband"] = round(float(row["bb_pband"]), 4)

        return Indicators(**kwargs)
