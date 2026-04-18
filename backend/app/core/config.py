from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

# All YAML configuration lives in backend/config/
_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
_CONFIG_YAML = _CONFIG_DIR / "settings.yaml"


def _load_config_yaml() -> dict:
    if _CONFIG_YAML.exists():
        with open(_CONFIG_YAML) as f:
            return yaml.safe_load(f) or {}
    return {}


# ── Per-entry indicator settings ──────────────────────────────────────────────

class IndicatorSettings:
    """Constructed from a watchlist entry's 'indicators' block (or SMA-only defaults)."""

    def __init__(self, raw: dict | None = None) -> None:
        raw = raw or {}
        sma = raw.get("sma", {})
        rsi = raw.get("rsi", {})
        macd = raw.get("macd", {})
        bb = raw.get("bb", {})

        self.sma_short: int = int(sma.get("short_period", 20))
        self.sma_long: int = int(sma.get("long_period", 50))

        self._rsi_enabled: bool = bool(rsi.get("enabled", False))
        self.rsi_period: int = int(rsi.get("period", 14))
        self.rsi_oversold: float = float(rsi.get("oversold", 30))
        self.rsi_overbought: float = float(rsi.get("overbought", 70))

        self._macd_enabled: bool = bool(macd.get("enabled", False))
        self.macd_fast: int = int(macd.get("fast", 12))
        self.macd_slow: int = int(macd.get("slow", 26))
        self.macd_signal: int = int(macd.get("signal", 9))

        self._bb_enabled: bool = bool(bb.get("enabled", False))
        self.bb_period: int = int(bb.get("period", 20))
        self.bb_std: int = int(bb.get("std", 2))

    def is_enabled(self, name: str) -> bool:
        if name == "sma":
            return True
        return getattr(self, f"_{name}_enabled", False)


# ── Watchlist entry ────────────────────────────────────────────────────────────

@dataclass
class PromptRef:
    file: str = "default"
    name: str = "trading_analysis"


@dataclass
class WatchlistEntry:
    name: str
    enabled: bool
    symbols: list[str]
    interval_seconds: int   # total interval in seconds (computed from config)
    include_llm: bool
    prompts: list[PromptRef]
    indicators: IndicatorSettings


# ── Config loaders ─────────────────────────────────────────────────────────────

def load_watchlist() -> list[WatchlistEntry]:
    """Read watchlist entries fresh from config.yaml."""
    raw = _load_config_yaml()
    entries: list[WatchlistEntry] = []
    for w in raw.get("watchlist", []):
        prompt_list = w.get("prompts") or [{"file": "prompts", "name": "trading_analysis"}]
        prompts = [
            PromptRef(file=p.get("file", "prompts"), name=p.get("name", "trading_analysis"))
            for p in prompt_list
        ]
        # Most-granular field wins: seconds > minutes > hours > days
        if w.get("interval_seconds"):
            interval_sec = int(w["interval_seconds"])
        elif w.get("interval_minutes"):
            interval_sec = int(w["interval_minutes"]) * 60
        elif w.get("interval_hours"):
            interval_sec = int(w["interval_hours"]) * 3600
        elif w.get("interval_days"):
            interval_sec = int(w["interval_days"]) * 86400
        else:
            interval_sec = 3600  # default: 1 hour
        entries.append(WatchlistEntry(
            name=w.get("name", ""),
            enabled=w.get("enabled", False),
            symbols=w.get("symbols") or [],
            interval_seconds=int(interval_sec),
            include_llm=w.get("include_llm", True),
            prompts=prompts,
            indicators=IndicatorSettings(w.get("indicators")),
        ))
    return entries


def all_watchlist_symbols() -> list[str]:
    """Deduplicated symbols across all watchlist entries, preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for entry in load_watchlist():
        for sym in entry.symbols:
            if sym not in seen:
                seen.add(sym)
                result.append(sym)
    return result


# ── LLM settings ──────────────────────────────────────────────────────────────

class LLMSettings(BaseSettings):
    """
    Reads from env vars (LLM_*) first; config.yaml llm section fills
    in anything not set via env — so env vars always override config.yaml.
    LLM_API_KEY is env-only (never stored in config.yaml).
    """

    provider: str = "openai_compat"
    base_url: str = "http://localhost:11434/v1"
    api_key: str = "no-key"
    model: str = ""
    temperature: float = 0.2
    max_tokens: int = 2048
    timeout: int = 120

    model_config = {
        "env_prefix": "LLM_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def _apply_yaml_defaults(self) -> "LLMSettings":
        """config.yaml values apply when not overridden by env vars."""
        yaml_llm = _load_config_yaml().get("llm", {})
        _types: dict[str, type] = {
            "provider": str,
            "base_url": str,
            "model": str,
            "temperature": float,
            "max_tokens": int,
            "timeout": int,
        }
        for key, cast in _types.items():
            if key in yaml_llm and key not in self.model_fields_set:
                object.__setattr__(self, key, cast(yaml_llm[key]))
        return self


# ── App-level settings (non-secret env config) ────────────────────────────────

class Settings(BaseSettings):
    app_name: str = "Local Market Analyzer"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def llm(self) -> LLMSettings:
        """Always returns a fresh LLMSettings — enables hot-reload after config.yaml edits."""
        return LLMSettings()


settings = Settings()

