from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

import yfinance as yf

from app.api.deps import get_market_provider, get_indicator_service
from app.api.schemas import WatchlistItemResponse
from app.core.config import all_watchlist_symbols

router = APIRouter(prefix="/market", tags=["market"])
logger = logging.getLogger(__name__)


@router.get("/search")
async def search_symbols(q: str = Query(..., min_length=1, max_length=50)):
    """Search for ticker symbols via yfinance. Returns up to 8 matches."""
    logger.info("yfinance  GET  search  q=%r", q)
    try:
        results = yf.Search(q, max_results=8)
        hits = [
            {
                "symbol": r["symbol"],
                "name": r.get("longname") or r.get("shortname") or r["symbol"],
                "type": r.get("quoteType", ""),
                "exchange": r.get("exchange", ""),
            }
            for r in results.quotes
            if r.get("symbol")
        ]
        logger.info("yfinance  OK   search  q=%r  hits=%d", q, len(hits))
        return hits
    except Exception:
        logger.exception("yfinance  ERR  search  q=%r", q)
        return []


@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    period: str = Query("3mo", description="yfinance period, e.g. 1d, 5d, 1mo, 3mo, 1y"),
    interval: str = Query("1d", description="yfinance interval, e.g. 1m, 5m, 1h, 1d"),
):
    """Return OHLCV bars for charting.

    Serves from the local SQLite cache when the data is fresh enough;
    otherwise fetches from yfinance (which also writes to the cache).
    """
    sym = symbol.upper()
    try:
        bars = _bars_from_cache(sym, period, interval)
        source = "cache"
        if bars is None:
            logger.info("OHLCV cache miss — fetching from yfinance  symbol=%s period=%s interval=%s", sym, period, interval)
            provider = get_market_provider()
            df = provider.fetch_ohlcv(sym, period=period, interval=interval)
            bars = [
                {
                    "time": int(ts.timestamp()),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                }
                for ts, row in df.iterrows()
            ]
            source = "yfinance"
        logger.info("OHLCV  %s  symbol=%s  bars=%d  interval=%s", source, sym, len(bars), interval)
        return {"symbol": sym, "period": period, "interval": interval, "bars": bars, "source": source}
    except Exception as exc:
        logger.exception("OHLCV fetch failed for %s", sym)
        return {"symbol": sym, "period": period, "interval": interval, "bars": [], "error": str(exc)}


# How old the most-recent cached bar can be before we bypass the cache.
# Keyed by the yfinance interval string.
_INTERVAL_STALENESS: dict[str, timedelta] = {
    "1m":   timedelta(minutes=2),
    "2m":   timedelta(minutes=4),
    "5m":   timedelta(minutes=10),
    "15m":  timedelta(minutes=30),
    "30m":  timedelta(hours=1),
    "60m":  timedelta(hours=2),
    "1h":   timedelta(hours=2),
    "90m":  timedelta(hours=3),
    "1d":   timedelta(hours=20),
    "5d":   timedelta(days=5),
    "1wk":  timedelta(days=7),
    "1mo":  timedelta(days=31),
    "3mo":  timedelta(days=93),
}

# Minimum bar counts to consider the cache useful (rough lower bounds).
_PERIOD_MIN_BARS: dict[str, int] = {
    "1d": 60, "5d": 100, "1mo": 20, "3mo": 60,
    "6mo": 120, "1y": 240, "2y": 480, "5y": 1200, "ytd": 50, "max": 100,
}


def _bars_from_cache(sym: str, period: str, interval: str) -> list[dict] | None:
    """Return bars from DB if fresh enough and plentiful, else None."""
    try:
        from sqlmodel import Session, select
        from app.db.session import engine
        from app.db.models import OHLCVBar

        with Session(engine) as session:
            rows = session.exec(
                select(OHLCVBar)
                .where(OHLCVBar.symbol == sym, OHLCVBar.interval == interval)
                .order_by(OHLCVBar.timestamp)
            ).all()

        if not rows:
            return None

        # Check freshness: most recent bar must be within the staleness window
        staleness = _INTERVAL_STALENESS.get(interval, timedelta(hours=24))
        latest_ts = rows[-1].timestamp.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - latest_ts > staleness:
            logger.info("OHLCV cache stale  symbol=%s  interval=%s  latest=%s", sym, interval, latest_ts.isoformat())
            return None

        # Check count: must have enough bars for the requested period
        min_bars = _PERIOD_MIN_BARS.get(period, 20)
        if len(rows) < min_bars:
            logger.info("OHLCV cache sparse  symbol=%s  bars=%d  min=%d", sym, len(rows), min_bars)
            return None

        return [
            {
                "time": int(row.timestamp.replace(tzinfo=timezone.utc).timestamp()),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }
            for row in rows
        ]
    except Exception:
        logger.debug("OHLCV cache read failed, falling through to yfinance", exc_info=True)
        return None


@router.get("/price/{symbol}")
async def get_price(symbol: str):
    """Get latest price for a symbol."""
    provider = get_market_provider()
    price = provider.get_latest_price(symbol.upper())
    return {"symbol": symbol.upper(), "price": price}


@router.get("/watchlist", response_model=list[WatchlistItemResponse])
async def get_watchlist():
    """Get prices and quick signals for configured watchlist symbols."""
    provider = get_market_provider()
    indicator_svc = get_indicator_service()
    from app.services.signals import SignalEngine

    engine = SignalEngine()
    results = []

    for symbol in all_watchlist_symbols():
        try:
            df = provider.fetch_ohlcv(symbol, period="5d", interval="1d")
            df = indicator_svc.compute(df)
            indicators = indicator_svc.latest(df)
            sig = engine.generate(indicators)

            # Compute % change
            if len(df) >= 2:
                prev_close = float(df["Close"].iloc[-2])
                change = round((indicators.close - prev_close) / prev_close * 100, 2)
            else:
                change = 0.0

            results.append(WatchlistItemResponse(
                symbol=symbol,
                price=indicators.close,
                change=change,
                signal=sig.signal.value,
                score=sig.score,
                confidence=sig.confidence,
            ))
        except Exception:
            results.append(WatchlistItemResponse(
                symbol=symbol,
                price=0.0,
                change=0.0,
            ))

    return results
