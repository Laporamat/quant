"""
utils/plotting.py
Plotly chart generators for equity curves, drawdowns, heatmaps, returns.
Returns plotly Figure objects (can be saved or converted to JSON).
"""
from __future__ import annotations
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def equity_curve(
    equity: pd.Series,
    benchmark: Optional[pd.Series] = None,
    title: str = "Equity Curve",
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity.index, y=equity.values,
        name="Strategy", line=dict(color="#2980b9", width=2),
    ))
    if benchmark is not None:
        rebased = benchmark / benchmark.iloc[0] * equity.iloc[0]
        fig.add_trace(go.Scatter(
            x=rebased.index, y=rebased.values,
            name="Benchmark", line=dict(color="#e74c3c", width=1.5, dash="dash"),
        ))
    fig.update_layout(
        title=title, xaxis_title="Date", yaxis_title="Portfolio Value ($)",
        hovermode="x unified", template="plotly_white",
    )
    return fig


def drawdown_chart(equity: pd.Series, title: str = "Drawdown") -> go.Figure:
    from stats.drawdown import DrawdownAnalysis
    uw = DrawdownAnalysis.underwater(equity) * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=uw.index, y=uw.values,
        fill="tozeroy", name="Drawdown %",
        line=dict(color="#e74c3c", width=1),
        fillcolor="rgba(231,76,60,0.3)",
    ))
    fig.update_layout(
        title=title, xaxis_title="Date", yaxis_title="Drawdown (%)",
        template="plotly_white",
    )
    return fig


def returns_heatmap(prices: pd.Series, title: str = "Monthly Returns (%)") -> go.Figure:
    from stats.returns import ReturnStats
    tbl = ReturnStats.monthly_return_table(prices)
    cols = [c for c in tbl.columns if c != "Annual"]
    data = tbl[cols].values

    fig = go.Figure(go.Heatmap(
        z=data,
        x=cols,
        y=tbl.index.tolist(),
        colorscale="RdYlGn",
        zmid=0,
        text=[[f"{v:.1f}%" if not pd.isna(v) else "" for v in row] for row in data],
        texttemplate="%{text}",
        showscale=True,
    ))
    fig.update_layout(
        title=title, xaxis_title="Month", yaxis_title="Year",
        template="plotly_white",
    )
    return fig


def indicator_chart(
    ohlcv:   pd.DataFrame,
    ticker:  str = "",
    indicators: Optional[Dict[str, pd.Series]] = None,
) -> go.Figure:
    """Candlestick + volume + optional indicator overlays."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.7, 0.3],
        subplot_titles=[ticker, "Volume"],
    )
    fig.add_trace(go.Candlestick(
        x=ohlcv.index,
        open=ohlcv["open"], high=ohlcv["high"],
        low=ohlcv["low"],   close=ohlcv["close"],
        name=ticker,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=ohlcv.index, y=ohlcv["volume"],
        name="Volume", marker_color="rgba(100,100,200,0.5)",
    ), row=2, col=1)
    if indicators:
        for name, series in indicators.items():
            fig.add_trace(go.Scatter(
                x=series.index, y=series.values,
                name=name, line=dict(width=1.5),
            ), row=1, col=1)
    fig.update_layout(
        xaxis_rangeslider_visible=False, template="plotly_white",
        height=600,
    )
    return fig


def correlation_heatmap(corr: pd.DataFrame, title: str = "Correlation Matrix") -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu",
        zmid=0, zmin=-1, zmax=1,
        text=corr.round(2).values.tolist(),
        texttemplate="%{text}",
    ))
    fig.update_layout(title=title, template="plotly_white")
    return fig


def return_distribution(returns: pd.Series, ticker: str = "") -> go.Figure:
    from scipy.stats import norm
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=returns.dropna() * 100,
        nbinsx=100, name="Returns",
        histnorm="probability density",
        marker_color="rgba(41,128,185,0.6)",
    ))
    mu, sig = float(returns.mean() * 100), float(returns.std() * 100)
    x_range = np.linspace(mu - 4*sig, mu + 4*sig, 200)
    fig.add_trace(go.Scatter(
        x=x_range, y=norm.pdf(x_range, mu, sig),
        name="Normal", line=dict(color="red", width=2),
    ))
    fig.update_layout(
        title=f"Return Distribution – {ticker}",
        xaxis_title="Daily Return (%)", yaxis_title="Density",
        template="plotly_white",
    )
    return fig


def performance_comparison(results: Dict[str, pd.Series], title: str = "Strategy Comparison") -> go.Figure:
    """Overlay multiple normalised equity curves."""
    fig = go.Figure()
    for name, equity in results.items():
        rebased = equity / equity.iloc[0]
        fig.add_trace(go.Scatter(
            x=rebased.index, y=rebased.values, name=name, line=dict(width=2),
        ))
    fig.update_layout(
        title=title, xaxis_title="Date", yaxis_title="Growth of $1",
        hovermode="x unified", template="plotly_white",
    )
    return fig
