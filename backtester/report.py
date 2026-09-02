"""
backtester/report.py
Generate HTML and JSON backtest reports.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from config import REPORTS_DIR

logger = logging.getLogger(__name__)


class BacktestReport:
    """Generate readable HTML and JSON reports from BacktestResult."""

    def __init__(self, result) -> None:
        self.result = result

    def to_json(self, path: Optional[Path] = None) -> str:
        """Serialise result to JSON string and optionally save to disk."""
        data = {
            "strategy":    self.result.strategy_name,
            "config":      {
                "start_date":      self.result.config.start_date,
                "end_date":        self.result.config.end_date,
                "initial_capital": self.result.config.initial_capital,
                "commission_pct":  self.result.config.commission_pct,
                "slippage_pct":    self.result.config.slippage_pct,
            },
            "performance": self._serialise_performance(),
            "equity_curve": {
                str(k.date()): round(v, 2)
                for k, v in self.result.equity_curve.items()
                if not pd.isna(v)
            },
            "trade_summary": self._trade_summary(),
            "generated_at":  datetime.utcnow().isoformat() + "Z",
            "run_time_s":    round(self.result.run_time_s, 3),
        }
        js = json.dumps(data, default=str, indent=2)
        if path:
            Path(path).write_text(js, encoding="utf-8")
            logger.info("Report saved to %s", path)
        return js

    def to_html(self, path: Optional[Path] = None) -> str:
        """Generate a self-contained HTML report with charts."""
        perf   = self.result.performance
        trades = self.result.trade_log
        equity = self.result.equity_curve

        # ── Equity chart data ─────────────────
        eq_dates = [str(d.date()) for d in equity.index]
        eq_vals  = [round(v, 2) for v in equity.values]

        # ── Performance table rows ─────────────
        def _fmt(k: str, v) -> str:
            if isinstance(v, float):
                if "return" in k or "drawdown" in k or "cagr" in k or "vol" in k:
                    return f"{v*100:.2f}%"
                return f"{v:.4f}"
            return str(v)

        table_rows = "".join(
            f"<tr><td>{k}</td><td>{_fmt(k, v)}</td></tr>"
            for k, v in perf.items()
            if not isinstance(v, dict) and k not in ("monthly_returns",)
        )

        # ── Trade stats ───────────────────────
        n_trades = len(trades) if not trades.empty else 0
        realised = float(trades["realised_pnl"].sum()) if (not trades.empty and "realised_pnl" in trades.columns) else 0.0

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Backtest Report – {self.result.strategy_name}</title>
<script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: auto; padding: 20px; }}
  h1 {{ color: #2c3e50; }} h2 {{ color: #34495e; border-bottom: 2px solid #eee; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
  tr:hover {{ background-color: #f5f5f5; }}
  .metric-card {{ display: inline-block; background: #f8f9fa; border-radius: 8px;
                  padding: 15px 25px; margin: 8px; text-align: center; }}
  .metric-val {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
  .metric-lbl {{ font-size: 12px; color: #7f8c8d; }}
</style>
</head>
<body>
<h1>📊 Backtest Report: {self.result.strategy_name}</h1>
<p>Period: {self.result.config.start_date} → {self.result.config.end_date} |
   Capital: ${self.result.config.initial_capital:,.0f} |
   Commission: {self.result.config.commission_pct*100:.2f}% |
   Run time: {self.result.run_time_s:.2f}s</p>

<div>
  <div class="metric-card">
    <div class="metric-val">{perf.get('cagr', 0)*100:.1f}%</div>
    <div class="metric-lbl">CAGR</div>
  </div>
  <div class="metric-card">
    <div class="metric-val">{perf.get('sharpe', 0):.2f}</div>
    <div class="metric-lbl">Sharpe</div>
  </div>
  <div class="metric-card">
    <div class="metric-val">{perf.get('max_drawdown', 0)*100:.1f}%</div>
    <div class="metric-lbl">Max Drawdown</div>
  </div>
  <div class="metric-card">
    <div class="metric-val">{perf.get('calmar', 0):.2f}</div>
    <div class="metric-lbl">Calmar</div>
  </div>
  <div class="metric-card">
    <div class="metric-val">{perf.get('win_rate', 0)*100:.1f}%</div>
    <div class="metric-lbl">Win Rate</div>
  </div>
  <div class="metric-card">
    <div class="metric-val">{n_trades}</div>
    <div class="metric-lbl">Trades</div>
  </div>
</div>

<h2>Equity Curve</h2>
<div id="equity-chart"></div>
<script>
Plotly.newPlot('equity-chart', [{{
  x: {json.dumps(eq_dates)},
  y: {json.dumps(eq_vals)},
  type: 'scatter', mode: 'lines',
  line: {{color: '#2980b9', width: 2}},
  name: 'Equity'
}}], {{
  title: '', xaxis: {{title: 'Date'}}, yaxis: {{title: 'Portfolio Value ($)'}},
  height: 400, margin: {{l:60, r:20, t:20, b:60}}
}});
</script>

<h2>Performance Metrics</h2>
<table><tr><th>Metric</th><th>Value</th></tr>
{table_rows}
</table>

<h2>Trade Summary</h2>
<p>Total trades: {n_trades} | Realised PnL: ${realised:,.2f}</p>

<p style="color:#999; font-size:11px;">Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
</body></html>"""

        if path:
            Path(path).write_text(html, encoding="utf-8")
            logger.info("HTML report saved to %s", path)
        return html

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _serialise_performance(self) -> dict:
        """Convert performance dict to JSON-safe format."""
        result = {}
        for k, v in self.result.performance.items():
            if isinstance(v, (int, float, str, bool)) or v is None:
                result[k] = v
            elif isinstance(v, dict):
                result[k] = str(v)[:500]  # truncate large nested dicts
            else:
                result[k] = str(v)
        return result

    def _trade_summary(self) -> dict:
        tl = self.result.trade_log
        if tl.empty:
            return {"n_trades": 0}
        return {
            "n_trades":         len(tl),
            "realised_pnl":     float(tl.get("realised_pnl", pd.Series(0)).sum()),
            "commission_total": float(tl.get("commission", pd.Series(0)).sum()),
            "avg_trade_pnl":    float(tl.get("realised_pnl", pd.Series(0)).mean()),
        }

    def save(self, directory: Optional[Path] = None) -> Dict[str, Path]:
        """Save both JSON and HTML reports. Returns paths."""
        directory = Path(directory or REPORTS_DIR)
        directory.mkdir(parents=True, exist_ok=True)
        ts    = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name  = f"{self.result.strategy_name}_{ts}"
        j_path = directory / f"{name}.json"
        h_path = directory / f"{name}.html"
        self.to_json(j_path)
        self.to_html(h_path)
        return {"json": j_path, "html": h_path}
