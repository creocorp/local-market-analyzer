from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from app.core.models import Indicators


class MarketDataProvider(ABC):
    """Port for fetching market OHLCV data."""

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_latest_price(self, symbol: str) -> float:
        ...


class IndicatorService(ABC):
    """Port for computing technical indicators."""

    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        ...

    @abstractmethod
    def latest(self, df: pd.DataFrame) -> Indicators:
        ...


class LLMProvider(ABC):
    """Port for calling an LLM."""

    @abstractmethod
    async def complete(self, prompt: str, system: str | None = None) -> str:
        ...
