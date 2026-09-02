#!/usr/bin/env python
"""scripts/run_backtest.py – CLI to run a backtest."""
import sys, json, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from rich.console import Console
from rich.table import Table

console = Console()
app     = typer.Typer(help="Run a strategy backtest from the command line.")


@app.command()
def run(
    strategy:   str   = typer.Option("sma_crossover"),
    tickers:    str   = typer.Option("AAPL,MSFT,GOOGL,AMZN,NVDA"),
    start:      str   = typer.Option("2010-01-01"),
    end:        str   = typer.Option("2024-12-31"),
    capital:    float = typer.Option(1_000_000),
    commission: float = typer.Option(0.0015),
    slippage:   float = typer.Option(0.0005),
    sizing:     str   = typer.Option("equal"),
    params:     str   = typer.Option("{}", help="JSON strategy params"),
    save:       bool  = typer.Option(True, help="Save HTML + JSON report"),
):
    """Run a backtest and print the performance table."""
    logging.basicConfig(level="WARNING")

    from data.loader import DataLoader
    from backtester.engine import BacktestEngine, BacktestConfig
    from backtester.report import BacktestReport
    from strategies import STRATEGY_REGISTRY

    if strategy not in STRATEGY_REGISTRY:
        console.print(f"[red]Unknown strategy '{strategy}'. Available: {list(STRATEGY_REGISTRY.keys())}[/red]")
        raise typer.Exit(1)

    ticker_list  = [t.strip().upper() for t in tickers.split(",")]
    strategy_params = json.loads(params)
    strategy_params["tickers"] = ticker_list

    loader = DataLoader()
    data   = {}
    console.print(f"[cyan]Loading data for {len(ticker_list)} tickers...[/cyan]")
    for t in ticker_list:
        df = loader.load(t, start=start, end=end)
        if not df.empty:
            data[t] = df
    if not data:
        console.print("[red]No data found. Run download_data.py first.[/red]")
        raise typer.Exit(1)

    config  = BacktestConfig(
        start_date=start, end_date=end,
        initial_capital=capital,
        commission_pct=commission,
        slippage_pct=slippage,
        position_sizing=sizing,
    )
    strat  = STRATEGY_REGISTRY[strategy](params=strategy_params)
    engine = BacktestEngine(strat, data, config)

    console.print(f"[green]Running backtest: {strategy} | {start} → {end}[/green]")
    result = engine.run()
    perf   = result.performance

    # ── Print table ─────────────────────────────────────────────
    table = Table(title=f"Backtest Results: {strategy}", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value",  style="green")

    highlights = [
        "cagr", "sharpe", "sortino", "calmar", "max_drawdown",
        "ann_volatility", "total_return", "win_rate", "var_95", "n_days",
    ]
    for key in highlights:
        val = perf.get(key)
        if val is not None:
            if "return" in key or "drawdown" in key or "vol" in key or key == "cagr":
                fmt_val = f"{val*100:.2f}%"
            else:
                fmt_val = f"{val:.4f}"
            table.add_row(key, fmt_val)

    console.print(table)
    console.print(f"\nRun time: {result.run_time_s:.2f}s | Trades: {len(result.trade_log)}")

    if save:
        paths = BacktestReport(result).save()
        console.print(f"\n[blue]Reports saved:[/blue]")
        for k, v in paths.items():
            console.print(f"  {k}: {v}")


if __name__ == "__main__":
    app()
