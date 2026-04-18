"""LLM Interpret Node — sends indicator data + signal to a language model.

Uses the prompt templates defined in ``backend/config/<file>.yaml``.  The node
reads the ``prompts`` list from state and runs *each* prompt against the LLM,
collecting all results.  This lets a single workflow run multiple analysis
perspectives (e.g. ``trading_analysis`` + ``sentiment_analysis``) in one pass.

If the LLM call fails for any prompt, the node records the error but does not
abort — downstream nodes still receive the rule-based signal.

Caching
-------
Before each LLM call the node checks ``llm_analyses`` for a recent result
(within ``LLM_CACHE_MINUTES`` minutes, default 60).  If a fresh row exists it
is returned immediately without calling the LLM.  New results are always
persisted so future runs can benefit from the cache.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta, timezone

from app.graph.state import TradingState, PromptRequest
from app.core.config import settings
from app.llm.factory import create_llm_provider
from app.services.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

# How long an LLM result is considered fresh enough to reuse from the cache.
LLM_CACHE_MINUTES = 60


def _build_indicators_text(ind: dict) -> str:
    """Format the indicator dict into human-readable lines for the prompt."""
    lines = [f"  SMA Short:   {ind['sma_short']}", f"  SMA Long:    {ind['sma_long']}"]
    if ind.get("rsi") is not None:
        lines.append(f"  RSI:         {ind['rsi']}")
    if ind.get("macd") is not None:
        lines.append(f"  MACD:        {ind['macd']}  (signal: {ind['macd_signal']}, hist: {ind['macd_diff']})")
    if ind.get("bb_upper") is not None:
        lines.append(f"  Bollinger:   upper={ind['bb_upper']}  mid={ind['bb_middle']}  lower={ind['bb_lower']}  pband={ind['bb_pband']}")
    return "\n".join(lines)


def _parse_llm_response(content: str, fallback_signal: str) -> tuple[str, str]:
    """Parse the LLM response to extract (summary, recommendation).

    Tries JSON first. If the model returned prose instead of JSON (common with
    smaller/weaker models), extracts a BUY/SELL/HOLD keyword from the text and
    uses the full text as the summary so nothing is lost.
    """
    stripped = content.strip()

    # Strip markdown code fences that some models wrap around JSON
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        stripped = stripped.rsplit("```", 1)[0].strip()

    if not stripped:
        raise ValueError("LLM returned an empty response")

    # --- happy path: valid JSON ---
    # Try the whole stripped string first, then scan for an embedded JSON object
    for candidate in (stripped, None):
        try:
            parsed = json.loads(candidate if candidate is not None else stripped)
            summary = parsed.get("summary") or parsed.get("reasoning") or ""
            recommendation = (
                parsed.get("recommendation") or parsed.get("sentiment") or fallback_signal
            )
            return summary, recommendation
        except (json.JSONDecodeError, TypeError):
            if candidate is not None:
                # Try to find an embedded JSON object in the prose
                m = re.search(r"\{[^{}]+\}", stripped, re.DOTALL)
                if m:
                    try:
                        parsed = json.loads(m.group())
                        summary = parsed.get("summary") or parsed.get("reasoning") or ""
                        recommendation = (
                            parsed.get("recommendation") or parsed.get("sentiment") or fallback_signal
                        )
                        return summary, recommendation
                    except (json.JSONDecodeError, TypeError):
                        pass
            break

    # --- prose fallback: extract BUY/SELL/HOLD keyword ---
    logger.warning(
        "LLM returned prose instead of JSON — extracting signal keyword from text"
    )
    m = re.search(r"\b(BUY|SELL|HOLD)\b", stripped, re.IGNORECASE)
    recommendation = m.group(1).upper() if m else fallback_signal
    return stripped, recommendation


def _check_cache(symbol: str, prompt_name: str) -> dict | None:
    """Return a cached LLM result dict if one exists and is still fresh."""
    try:
        from sqlmodel import select
        from app.db.session import get_session
        from app.db.models import LLMAnalysis

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with get_session() as session:
            stmt = (
                select(LLMAnalysis)
                .where(LLMAnalysis.symbol == symbol)
                .where(LLMAnalysis.prompt_name == prompt_name)
                .where(LLMAnalysis.cached_until >= now)
                .order_by(LLMAnalysis.generated_at.desc())  # type: ignore[attr-defined]
                .limit(1)
            )
            row = session.exec(stmt).first()
            if row:
                return {"prompt_name": row.prompt_name, "summary": row.summary, "recommendation": row.recommendation}
    except Exception:
        logger.debug("LLM cache lookup failed", exc_info=True)
    return None


def _persist_llm_result(
    symbol: str,
    prompt_name: str,
    summary: str,
    recommendation: str,
    signal_result_id: int | None,
) -> None:
    """Persist an LLM result and set its cache expiry."""
    try:
        from app.db.session import get_session
        from app.db.models import LLMAnalysis

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        row = LLMAnalysis(
            symbol=symbol,
            prompt_name=prompt_name,
            signal_result_id=signal_result_id,
            generated_at=now,
            cached_until=now + timedelta(minutes=LLM_CACHE_MINUTES),
            summary=summary,
            recommendation=recommendation,
        )
        with get_session() as session:
            session.add(row)
    except Exception:
        logger.debug("LLM result persistence failed", exc_info=True)


async def llm_interpret(state: TradingState) -> dict:
    """Run every prompt in ``state["prompts"]`` against the LLM.

    Results are cached in ``llm_analyses`` for ``LLM_CACHE_MINUTES`` minutes
    (default 60).  A fresh cached row short-circuits the LLM call entirely.

    Reads
    -----
    indicators, signal, score, confidence, reasons, prompts, signal_result_id

    Writes
    ------
    llm_results : list[dict]  — one entry per prompt with keys
                                ``prompt_name``, ``summary``, ``recommendation``
    """
    if state.get("error") or not state.get("indicators"):
        return {}

    if not settings.llm.model:
        logger.warning("LLM skipped — no model configured. Set 'model' in config or LLM_MODEL env var.")
        return {}

    ind = state["indicators"]
    indicators_text = _build_indicators_text(ind)
    reasons_text = "\n".join(f"  - {r}" for r in (state.get("reasons") or []))
    signal_result_id: int | None = state.get("signal_result_id")  # type: ignore[assignment]

    # Support both the new multi-prompt list and a single prompt fallback
    prompts: list[PromptRequest] = state.get("prompts") or [
        PromptRequest(file="prompts", name="trading_analysis")
    ]

    llm_results: list[dict] = []

    for prompt_req in prompts:
        symbol = state["symbol"]
        prompt_name = prompt_req["name"]

        # --- cache hit? ---
        cached = _check_cache(symbol, prompt_name)
        if cached:
            logger.debug("llm_interpret cache hit: %s / %s", symbol, prompt_name)
            llm_results.append(cached)
            continue

        template = load_prompt(prompt_name, file=prompt_req["file"])

        system_prompt, user_prompt = template.render(
            symbol=symbol,
            close=ind["close"],
            indicators_text=indicators_text,
            signal=state.get("signal", "N/A"),
            score=state.get("score", 0),
            confidence=state.get("confidence", 0),
            reasons=reasons_text,
        )

        try:
            llm = create_llm_provider()
            content = await llm.complete(user_prompt, system=system_prompt)
            logger.debug("LLM raw response [%s/%s]: %r", symbol, prompt_name, content)

            summary, recommendation = _parse_llm_response(
                content, fallback_signal=state.get("signal", "HOLD")
            )
            _persist_llm_result(symbol, prompt_name, summary, recommendation, signal_result_id)
            llm_results.append({"prompt_name": prompt_name, "summary": summary, "recommendation": recommendation})
        except Exception as e:
            logger.error(
                "llm_interpret failed for %s / prompt=%s — raw content: %r",
                symbol, prompt_name, locals().get("content", "<no response>"),
            )
            logger.debug("llm_interpret exception detail", exc_info=True)
            llm_results.append({
                "prompt_name": prompt_name,
                "summary": f"LLM call failed: {e}",
                "recommendation": state.get("signal", "HOLD"),
            })

    return {"llm_results": llm_results}

