from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import APIRouter

from app.api.schemas import (
    AppConfigPayload,
    LLMConfig,
    WatchlistEntryConfig,
    IndicatorConfigPayload,
    SMAConfig,
    RSIConfig,
    MACDConfig,
    BBConfig,
    PromptRefConfig,
)

router = APIRouter(prefix="/config", tags=["config"])

# All YAML configuration lives in backend/config/
_CONFIG_YAML = Path(__file__).resolve().parent.parent.parent.parent / "config" / "settings.yaml"


def _read_yaml() -> dict:
    if _CONFIG_YAML.exists():
        with open(_CONFIG_YAML) as f:
            return yaml.safe_load(f) or {}
    return {}


def _write_yaml(data: dict) -> None:
    with open(_CONFIG_YAML, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _parse_indicators(raw: dict) -> IndicatorConfigPayload:
    sma = raw.get("sma", {})
    rsi = raw.get("rsi", {})
    macd = raw.get("macd", {})
    bb = raw.get("bb", {})
    return IndicatorConfigPayload(
        sma=SMAConfig(
            short_period=sma.get("short_period", 20),
            long_period=sma.get("long_period", 50),
        ),
        rsi=RSIConfig(
            enabled=rsi.get("enabled", False),
            period=rsi.get("period", 14),
            oversold=rsi.get("oversold", 30.0),
            overbought=rsi.get("overbought", 70.0),
        ),
        macd=MACDConfig(
            enabled=macd.get("enabled", False),
            fast=macd.get("fast", 12),
            slow=macd.get("slow", 26),
            signal=macd.get("signal", 9),
        ),
        bb=BBConfig(
            enabled=bb.get("enabled", False),
            period=bb.get("period", 20),
            std=bb.get("std", 2),
        ),
    )


def _serialize_indicators(ind: IndicatorConfigPayload) -> dict:
    return {
        "sma": {"short_period": ind.sma.short_period, "long_period": ind.sma.long_period},
        "rsi": {"enabled": ind.rsi.enabled, "period": ind.rsi.period,
                "oversold": ind.rsi.oversold, "overbought": ind.rsi.overbought},
        "macd": {"enabled": ind.macd.enabled, "fast": ind.macd.fast,
                 "slow": ind.macd.slow, "signal": ind.macd.signal},
        "bb": {"enabled": ind.bb.enabled, "period": ind.bb.period, "std": ind.bb.std},
    }


_PROMPTS_YAML = Path(__file__).resolve().parent.parent.parent.parent / "config" / "prompts.yaml"


@router.get("/prompts")
def list_prompts():
    """Return all prompt names available in prompts.yaml as [{file, name}] list."""
    if not _PROMPTS_YAML.exists():
        return []
    with open(_PROMPTS_YAML) as f:
        data = yaml.safe_load(f) or {}
    prompts = data.get("prompts", {})
    return [{"file": "prompts", "name": name} for name in prompts]


@router.get("", response_model=AppConfigPayload)
def get_config():
    """Return the full app configuration (llm + watchlist)."""
    raw = _read_yaml()

    llm_raw = raw.get("llm", {})
    llm = LLMConfig(
        provider=llm_raw.get("provider", "openai_compat"),
        base_url=llm_raw.get("base_url", "http://localhost:11434/v1"),
        model=llm_raw.get("model", ""),
        temperature=llm_raw.get("temperature", 0.2),
        max_tokens=llm_raw.get("max_tokens", 2048),
        timeout=llm_raw.get("timeout", 120),
    )

    watchlist = [
        WatchlistEntryConfig(
            name=w.get("name", ""),
            enabled=w.get("enabled", False),
            symbols=w.get("symbols") or [],
            interval_seconds=w.get("interval_seconds"),
            interval_minutes=w.get("interval_minutes"),
            interval_hours=w.get("interval_hours"),
            interval_days=w.get("interval_days"),
            include_llm=w.get("include_llm", True),
            prompts=[
                PromptRefConfig(file=p.get("file", "prompts"), name=p.get("name", "trading_analysis"))
                for p in (w.get("prompts") or [{"file": "prompts", "name": "trading_analysis"}])
            ],
            indicators=_parse_indicators(w.get("indicators") or {}),
        )
        for w in raw.get("watchlist", [])
    ]

    return AppConfigPayload(llm=llm, watchlist=watchlist)


@router.put("", response_model=AppConfigPayload)
def save_config(config: AppConfigPayload):
    """Write the full config to config.yaml. Watchlist changes apply within 1 min."""
    data = {
        "llm": {
            "provider": config.llm.provider,
            "base_url": config.llm.base_url,
            "model": config.llm.model,
            "temperature": config.llm.temperature,
            "max_tokens": config.llm.max_tokens,
            "timeout": config.llm.timeout,
        },
        "watchlist": [
            {
                "name": e.name,
                "enabled": e.enabled,
                "symbols": e.symbols,
                "interval_seconds": e.interval_seconds,
                "interval_minutes": e.interval_minutes,
                "interval_hours": e.interval_hours,
                "interval_days": e.interval_days,
                "include_llm": e.include_llm,
                "prompts": [{"file": p.file, "name": p.name} for p in e.prompts],
                "indicators": _serialize_indicators(e.indicators),
            }
            for e in config.watchlist
        ],
    }
    _write_yaml(data)
    return config
