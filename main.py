import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from config import SYMBOLS
from graph.workflow import build_graph

console = Console()


SIGNAL_COLOR = {
    "BUY": "bold green",
    "SELL": "bold red",
    "HOLD": "bold yellow",
}


def print_result(state: dict) -> None:
    symbol = state["symbol"]

    if state.get("error"):
        console.print(Panel(f"[red]Error for {symbol}:[/red] {state['error']}", border_style="red"))
        return

    ind = state["indicators"]
    signal = state.get("signal", "N/A")
    color = SIGNAL_COLOR.get(signal, "white")

    # --- Indicators table ---
    table = Table(title=f"[bold]{symbol}[/bold] — Indicators", box=box.SIMPLE_HEAVY, show_header=True)
    table.add_column("Indicator", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right")

    table.add_row("Close Price",  f"${ind['close']}")
    table.add_row("RSI",          str(ind["rsi"]))
    table.add_row("MACD",         str(ind["macd"]))
    table.add_row("MACD Signal",  str(ind["macd_signal"]))
    table.add_row("MACD Hist",    str(ind["macd_diff"]))
    table.add_row("BB Upper",     str(ind["bb_upper"]))
    table.add_row("BB Middle",    str(ind["bb_middle"]))
    table.add_row("BB Lower",     str(ind["bb_lower"]))
    table.add_row("BB %B",        str(ind["bb_pband"]))
    table.add_row("SMA Short",    str(ind["sma_short"]))
    table.add_row("SMA Long",     str(ind["sma_long"]))
    console.print(table)

    # --- Signal summary ---
    console.print(
        f"  Rule Signal : [{color}]{signal}[/{color}]  "
        f"score={state.get('score')}  confidence={state.get('confidence')}"
    )
    for r in state.get("reasons", []):
        console.print(f"    [dim]• {r}[/dim]")

    # --- LLM output ---
    llm_rec = state.get("llm_recommendation", "N/A")
    llm_color = SIGNAL_COLOR.get(llm_rec, "white")
    console.print(Panel(
        f"[bold]LLM Summary:[/bold]\n{state.get('llm_summary', '')}\n\n"
        f"[bold]LLM Recommendation:[/bold] [{llm_color}]{llm_rec}[/{llm_color}]",
        title=f"[bold]{symbol}[/bold] — AI Analysis",
        border_style="blue",
    ))


def main() -> None:
    # Allow overriding symbols via CLI args: python main.py AAPL MSFT
    symbols = sys.argv[1:] if len(sys.argv) > 1 else SYMBOLS

    graph = build_graph()

    console.rule("[bold blue]AI Trading Assistant[/bold blue]")

    for symbol in symbols:
        symbol = symbol.strip().upper()
        console.print(f"\n[bold]Analysing [cyan]{symbol}[/cyan]...[/bold]")
        initial_state: dict = {
            "symbol": symbol,
            "indicators": None,
            "signal": None,
            "score": None,
            "confidence": None,
            "reasons": None,
            "llm_summary": None,
            "llm_recommendation": None,
            "error": None,
        }
        result = graph.invoke(initial_state)
        print_result(result)

    console.rule()


if __name__ == "__main__":
    main()
