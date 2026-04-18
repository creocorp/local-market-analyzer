# ── Node Registry ─────────────────────────────────────────────────────────────
#
# Each file in this package defines one LangGraph node function.
# The workflow builder (graph/workflow.py) imports nodes from here.
#
# HOW TO ADD A NEW NODE:
#
#   1. Create a new file in this directory, e.g. `my_node.py`.
#
#   2. Define a function with this signature:
#
#        def my_node(state: TradingState) -> dict:
#            # Read what you need from `state`, return a dict of keys to update.
#            return {"my_output_key": value}
#
#      For async nodes (e.g. HTTP calls, LLM):
#
#        async def my_node(state: TradingState) -> dict:
#            ...
#
#   3. Add any new state keys your node reads/writes to `graph/state.py`.
#
#   4. Re-export your node here so the workflow can import it:
#
#        from app.graph.nodes.my_node import my_node
#
#   5. Wire it into a workflow in `graph/workflow.py` (see that file for examples).
#
# ──────────────────────────────────────────────────────────────────────────────

from app.graph.nodes.compute_features import compute_features
from app.graph.nodes.generate_signal import generate_signal
from app.graph.nodes.llm_interpret import llm_interpret

__all__ = ["compute_features", "generate_signal", "llm_interpret"]
