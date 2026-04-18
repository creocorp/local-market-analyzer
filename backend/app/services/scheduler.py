from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from datetime import datetime, timezone

from app.core.config import WatchlistEntry, load_watchlist

logger = logging.getLogger(__name__)

# In-memory store — keyed by symbol so we always have the latest result per symbol
_latest_results: dict[str, dict] = {}
_last_run: dict[str, datetime] = {}
_lock = asyncio.Lock()

# SSE subscriber queues — one per connected client
_subscribers: set[asyncio.Queue] = set()


async def get_latest_results() -> list[dict]:
    async with _lock:
        return list(_latest_results.values())


async def subscribe() -> "asyncio.Queue[dict]":
    """Register a new SSE client and return its dedicated queue."""
    q: asyncio.Queue[dict] = asyncio.Queue(maxsize=50)
    async with _lock:
        _subscribers.add(q)
    return q


async def unsubscribe(q: "asyncio.Queue[dict]") -> None:
    """Deregister an SSE client queue when the connection closes."""
    async with _lock:
        _subscribers.discard(q)


async def _run_cycle(entry: WatchlistEntry) -> None:
    """Run one analysis cycle for a watchlist entry using its own indicator config."""
    from app.services.market import YFinanceProvider, TAIndicatorService
    from app.services.signals import SignalEngine
    from app.graph.nodes import llm_interpret

    provider = YFinanceProvider()
    ind_svc = TAIndicatorService(entry.indicators)
    sig_engine = SignalEngine(entry.indicators)

    cycle_results: list[dict] = []
    for symbol in entry.symbols:
        try:
            df = provider.fetch_ohlcv(symbol)
            df = ind_svc.compute(df)
            ind_obj = ind_svc.latest(df)
            sig = sig_engine.generate(ind_obj)

            state: dict = {
                "symbol": symbol,
                "indicators": asdict(ind_obj),
                "signal": sig.signal.value,
                "score": sig.score,
                "confidence": sig.confidence,
                "reasons": sig.reasons,
            }

            if entry.include_llm and entry.prompts:
                state["prompts"] = [
                    {"file": p.file, "name": p.name} for p in entry.prompts
                ]
                state.update(await llm_interpret(state))

            state["_timestamp"] = datetime.now(timezone.utc).isoformat()
            state["_schedule"] = entry.name
            cycle_results.append(state)
            logger.info(
                "Scheduled [%s] %s → %s (score=%s)",
                entry.name, symbol, sig.signal.value, sig.score,
            )
        except ValueError as e:
            logger.warning("Scheduled analysis skipped: %s / %s — %s", entry.name, symbol, e)
            cycle_results.append({
                "symbol": symbol,
                "_schedule": entry.name,
                "error": str(e),
            })
        except Exception:
            logger.exception("Scheduled analysis failed: %s / %s", entry.name, symbol)
            cycle_results.append({
                "symbol": symbol,
                "_schedule": entry.name,
                "error": "analysis failed",
            })

    async with _lock:
        for result in cycle_results:
            _latest_results[result["symbol"]] = result
        # Broadcast to all connected SSE clients
        for q in _subscribers:
            for result in cycle_results:
                try:
                    q.put_nowait(result)
                except asyncio.QueueFull:
                    pass  # slow consumer; drop rather than block


async def scheduler_loop() -> None:
    """Background loop — re-reads settings.yaml every tick and runs due entries.

    The tick interval adapts: if any enabled entry uses a sub-60-second
    interval the loop ticks every 5 s; otherwise it ticks every 60 s.
    """
    logger.info("Scheduler started")
    while True:
        try:
            entries = load_watchlist()
            now = datetime.now(timezone.utc)
            min_interval = 60
            for entry in entries:
                if not entry.enabled or not entry.symbols:
                    continue
                if entry.interval_seconds < min_interval:
                    min_interval = entry.interval_seconds
                last = _last_run.get(entry.name)
                if last is None or (now - last).total_seconds() >= entry.interval_seconds:
                    logger.info(
                        "Running scheduled entry: %s (interval=%ss)",
                        entry.name, entry.interval_seconds,
                    )
                    await _run_cycle(entry)
                    _last_run[entry.name] = now
        except Exception:
            logger.exception("Scheduler loop error")
        tick = 5 if min_interval < 60 else 60
        await asyncio.sleep(tick)

