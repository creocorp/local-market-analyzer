from __future__ import annotations

from functools import lru_cache

from app.graph.workflow import build_analysis_graph, build_signals_only_graph
from app.llm.factory import create_llm_provider
from app.services.market import YFinanceProvider, TAIndicatorService
from app.services.signals import SignalEngine


@lru_cache
def get_analysis_graph():
    return build_analysis_graph()


@lru_cache
def get_signals_graph():
    return build_signals_only_graph()


@lru_cache
def get_market_provider():
    return YFinanceProvider()


@lru_cache
def get_indicator_service():
    return TAIndicatorService()


@lru_cache
def get_signal_engine():
    return SignalEngine()


def get_llm_provider():
    return create_llm_provider()
