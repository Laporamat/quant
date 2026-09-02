#!/usr/bin/env python
"""scripts/generate_report.py – Generate HTML report from a backtest result."""
import sys, json, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from rich.console import Console

console = Console()
app     = typer.Typer(help="Generate HTML/JSON reports for a saved backtest.")


@app.command()
def report(
    strategy:  str   = typer.Option("sma_crossover"),
    tickers:   str   = typer.Option("AAPL,MSFT,GOOGL"),
    start:     str   = typer.Option("2010-01-01"),
    end:       str   = typer.Option("2024-12-31"),
    capital:   float = typer.Option(1_000_000),
    out_dir:   str   = typer.Option("reports"),
    open_html: bool  = typer.Option(False),
):
    """Run a backtest, then generate and save an HTML + JSON report."""
    logging.basicConfig(level="WARNING")

    from data.loader import DataLoader
    from backtester.engine import BacktestEngine, BacktestConfig
    from backtester.report import BacktestReport
    from strategies import STRATEGY_REGISTRY

    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    loader      = DataLoader()
    data        = {t: loader.load(t, start=start, end=end)
                   for t in ticker_list}
    data        = {t: df for t, df in data.items() if not df.empty}

    config = BacktestConfig(start_date=start, end_date=end, initial_capital=capital)
    strat  = STRATEGY_REGISTRY[strategy](params={"tickers": ticker_list})
    engine = BacktestEngine(strat, data, config)
    result = engine.run()

    out_path = Path(out_dir)
    paths    = BacktestReport(result).save(out_path)

    console.print(f"[green]Report saved:[/green]")
    for k, v in paths.items():
        console.print(f"  {k}: {v}")

    if open_html:
        import webbrowser
        webbrowser.open(str(paths["html"]))


if __name__ == "__main__":
    app()
