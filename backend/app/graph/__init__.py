"""LangGraph trading workflows.

This package contains:

- ``state.py``     — TradingState TypedDict shared by all nodes
- ``nodes/``       — one file per node function (compute_features, generate_signal, …)
- ``workflow.py``  — graph builders that wire nodes into executable pipelines

See each module's docstring for instructions on extending the system.
"""
