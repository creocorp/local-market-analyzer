"""LangGraph workflow definitions — the directed graphs that orchestrate nodes.

Each function builds and compiles a LangGraph StateGraph.  The graph defines
which nodes run, in what order, and under what conditions.

BUILT-IN WORKFLOWS
──────────────────
- ``build_analysis_graph``   — full pipeline: features → signal → LLM
- ``build_signals_only_graph`` — lightweight: features → signal (no LLM)

CREATING A CUSTOM WORKFLOW
──────────────────────────
1. Define your node(s) in ``graph/nodes/`` (see that package's __init__.py).
2. Add any new state keys to ``graph/state.py``.
3. Write a new ``build_*_graph()`` function here:

       from app.graph.nodes import compute_features, my_node

       def build_my_graph():
           builder = StateGraph(TradingState)
           builder.add_node("compute_features", compute_features)
           builder.add_node("my_node", my_node)
           builder.set_entry_point("compute_features")
           builder.add_edge("compute_features", "my_node")
           builder.add_edge("my_node", END)
           return builder.compile()

4. Expose it via ``api/deps.py`` so routes can call it.

CONDITIONAL ROUTING
───────────────────
Use ``add_conditional_edges`` to skip nodes on error or to branch based on
state values.  See ``build_analysis_graph`` for an example.
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.graph.state import TradingState
from app.graph.nodes import compute_features, generate_signal, llm_interpret


def build_analysis_graph():
    """Full trading analysis workflow: features → signal → LLM interpret."""
    builder = StateGraph(TradingState)

    builder.add_node("compute_features", compute_features)
    builder.add_node("generate_signal", generate_signal)
    builder.add_node("llm_interpret", llm_interpret)

    builder.set_entry_point("compute_features")

    # Skip downstream nodes if feature computation fails
    builder.add_conditional_edges(
        "compute_features",
        lambda s: "end" if s.get("error") else "continue",
        {"end": END, "continue": "generate_signal"},
    )
    builder.add_edge("generate_signal", "llm_interpret")
    builder.add_edge("llm_interpret", END)

    return builder.compile()


def build_signals_only_graph():
    """Lightweight graph: features → signal (no LLM call)."""
    builder = StateGraph(TradingState)

    builder.add_node("compute_features", compute_features)
    builder.add_node("generate_signal", generate_signal)

    builder.set_entry_point("compute_features")
    builder.add_conditional_edges(
        "compute_features",
        lambda s: "end" if s.get("error") else "continue",
        {"end": END, "continue": "generate_signal"},
    )
    builder.add_edge("generate_signal", END)

    return builder.compile()
