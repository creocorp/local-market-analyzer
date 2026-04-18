"""Trading workflow state — the shared data that flows between LangGraph nodes.

Every node in a workflow reads from and writes to this TypedDict.  LangGraph
merges the dict returned by each node back into the state automatically.

EXTENDING THE STATE
───────────────────
When you add a new node that needs extra data, add your keys here:

    class TradingState(TypedDict, total=False):
        ...
        # My new node output
        my_custom_score: Optional[float]

Then read/write that key in your node function:

    def my_node(state: TradingState) -> dict:
        return {"my_custom_score": 42.0}

Because ``total=False``, every key is optional — existing nodes are unaffected
when you add new fields.
"""
from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict


class PromptRequest(TypedDict):
    """A single prompt to run against the LLM.

    Corresponds to a ``{file, name}`` pair that references a YAML template
    inside ``backend/config/``.  For example::

        {"file": "default", "name": "trading_analysis"}
    """
    file: str
    name: str


class TradingState(TypedDict, total=False):
    # ── Inputs (set when invoking the graph) ──────────────────────────────
    symbol: str

    # List of prompt templates to run.  Each entry is a PromptRequest dict
    # pointing to a YAML file + key in backend/config/.  The LLM interpret
    # node iterates over all of them, so a single workflow run can produce
    # multiple analyses (e.g. trading_analysis + sentiment_analysis).
    prompts: list[PromptRequest]

    # ── Computed by compute_features ──────────────────────────────────────
    indicators: Optional[dict]

    # ── Computed by generate_signal ───────────────────────────────────────
    signal: Optional[str]
    score: Optional[int]
    confidence: Optional[float]
    reasons: Optional[list[str]]
    # DB row id written by generate_signal; read by llm_interpret for FK linkage
    signal_result_id: Optional[int]

    # ── Computed by llm_interpret ─────────────────────────────────────────
    # One result dict per prompt in ``prompts``, each containing:
    #   prompt_name, summary, recommendation
    llm_results: Optional[list[dict]]

    # ── Error (set by any node on failure) ────────────────────────────────
    error: Optional[str]
