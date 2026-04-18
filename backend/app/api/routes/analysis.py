from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import get_analysis_graph, get_signals_graph
from app.api.schemas import AnalysisResponse, AnalyzeRequest
from app.services.scheduler import get_latest_results, subscribe, unsubscribe

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)


def _state_to_response(r: dict) -> AnalysisResponse:
    """Map a raw scheduler state dict to the AnalysisResponse schema."""
    signal_data = None
    if r.get("signal"):
        signal_data = {
            "signal": r["signal"],
            "score": r.get("score", 0),
            "confidence": r.get("confidence", 0),
            "reasons": r.get("reasons", []),
        }
    return AnalysisResponse(
        symbol=r.get("symbol", ""),
        indicators=r.get("indicators"),
        signal=signal_data,
        llm_results=r.get("llm_results"),
        error=r.get("error"),
    )


@router.post("", response_model=AnalysisResponse)
async def analyze_symbol(req: AnalyzeRequest):
    """Run the full analysis pipeline for a symbol."""
    graph = get_analysis_graph() if req.include_llm else get_signals_graph()

    initial_state = {
        "symbol": req.symbol.upper(),
        "prompts": [{"file": p.file, "name": p.name} for p in req.prompts],
    }

    try:
        result = await graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    indicators = result.get("indicators")
    signal_data = None
    if result.get("signal"):
        signal_data = {
            "signal": result["signal"],
            "score": result.get("score", 0),
            "confidence": result.get("confidence", 0),
            "reasons": result.get("reasons", []),
        }

    return AnalysisResponse(
        symbol=req.symbol.upper(),
        indicators=indicators,
        signal=signal_data,
        llm_results=result.get("llm_results"),
        error=result.get("error"),
    )


@router.post("/batch", response_model=list[AnalysisResponse])
async def analyze_batch(symbols: list[str]):
    """Run analysis on multiple symbols."""
    graph = get_signals_graph()
    results = []

    for symbol in symbols:
        symbol = symbol.strip().upper()
        if not symbol:
            continue
        try:
            result = await graph.ainvoke({"symbol": symbol})
        except Exception as e:
            result = {"symbol": symbol, "error": str(e)}

        indicators = result.get("indicators")
        signal_data = None
        if result.get("signal"):
            signal_data = {
                "signal": result["signal"],
                "score": result.get("score", 0),
                "confidence": result.get("confidence", 0),
                "reasons": result.get("reasons", []),
            }

        results.append(AnalysisResponse(
            symbol=symbol,
            indicators=indicators,
            signal=signal_data,
            llm_results=result.get("llm_results"),
            error=result.get("error"),
        ))

    return results


@router.get("/scheduled", response_model=list[AnalysisResponse])
async def get_scheduled_results():
    """Get results from the latest scheduled analysis cycle."""
    raw = await get_latest_results()
    return [_state_to_response(r) for r in raw]


@router.get("/stream")
async def stream_analysis():
    """SSE stream — pushes an AnalysisResponse event for every symbol the scheduler
    completes.  The connection is kept alive with comment pings every 20 s.

    Clients should open this with ``new EventSource('/api/analysis/stream')``
    and handle ``onmessage`` events whose ``data`` field is JSON matching the
    AnalysisResponse schema.
    """
    queue = await subscribe()

    async def generator():
        try:
            while True:
                try:
                    raw = await asyncio.wait_for(queue.get(), timeout=20.0)
                    payload = _state_to_response(raw).model_dump_json()
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    # keepalive ping so proxies don't close idle connections
                    yield ":keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await unsubscribe(queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
            "Connection": "keep-alive",
        },
    )
