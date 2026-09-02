#!/usr/bin/env python
"""scripts/run_optimization.py – CLI for strategy parameter optimization."""
import sys, json, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from rich.console import Console
from rich.table import Table

console = Console()
app     = typer.Typer(help="Optimise strategy parameters via grid search.")


@app.command()
def optimise(
    strategy:    str = typer.Option("sma_crossover"),
    tickers:     str = typer.Option("AAPL,MSFT"),
    start:       str = typer.Option("2010-01-01"),
    end:         str = typer.Option("2024-12-31"),
    param_grid:  str = typer.Option('{"fast":[10,20,50],"slow":[100,150,200]}'),
    metric:      str = typer.Option("sharpe"),
    n_jobs:      int = typer.Option(-1),
    walk_forward:bool= typer.Option(False, help="Use walk-forward analysis"),
):
    """Grid search or walk-forward optimisation of a strategy."""
    logging.basicConfig(level="WARNING")

    from data.loader import DataLoader
    from backtester.engine import BacktestConfig
    from backtester.optimizer import StrategyOptimizer
    from strategies import STRATEGY_REGISTRY

    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    grid        = json.loads(param_grid)
    loader      = DataLoader()
    data        = {t: loader.load(t, start=start, end=end)
                   for t in ticker_list if not loader.load(t).empty}

    if not data:
        console.print("[red]No data. Run download_data.py first.[/red]")
        raise typer.Exit(1)

    config    = BacktestConfig(start_date=start, end_date=end)
    optimizer = StrategyOptimizer(STRATEGY_REGISTRY[strategy], data, config, n_jobs)

    if walk_forward:
        console.print("[cyan]Running walk-forward optimisation...[/cyan]")
        df = optimizer.walk_forward(grid, metric=metric)
        console.print(df.to_string())
    else:
        console.print("[cyan]Running grid search...[/cyan]")
        result = optimizer.grid_search(grid, metric=metric)
        console.print(f"\n[green]Best params:[/green] {result.best_params}")
        console.print(f"[green]Best {metric}:[/green] {result.best_metric:.4f}")
        console.print("\nTop 10 results:")
        console.print(result.all_results.head(10).to_string())


if __name__ == "__main__":
    app()
