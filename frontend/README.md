# QuantDash Frontend

Vue 3 + Vite + TypeScript + Tailwind CSS v3 dashboard for the Quant Backend.

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/dashboard` | Market Dashboard | Benchmark KPIs, top movers, sector performance, market breadth |
| `/ticker/:symbol` | Ticker Deep Dive | Candlestick, indicators, 8 descriptive + 8 risk metrics, heatmap, drawdown, distribution |
| `/compare` | Multi-Asset Compare | Normalized equity curves, correlation matrix, risk-return scatter |
| `/stats-hub` | Statistical Analysis Hub | Regime Detection, Seasonality, Tail Risk, Rolling Stats |
| `/bubble` | Bubble Detection | LPPL, z-score, acceleration, historical crash episodes |
| `/backtest` | Backtest Lab | Run strategy backtests, view equity curve & trade log |
| `/strategy-compare` | Strategy Compare | Side-by-side radar chart + metrics table |
| `/optimizer` | Optimizer | Grid search + walk-forward with surface heatmap |
| `/monte-carlo` | Monte Carlo | Percentile bands + final wealth distribution |

## Quick Start

```powershell
# From project root — installs deps and starts both servers:
.\start-dev.ps1

# Or manually:
cd frontend
npm install
npm run dev        # http://localhost:5173

# In a separate terminal:
cd ..
python main.py     # http://localhost:8000
```

## Build for Production

```powershell
cd frontend
npm run build
# dist/ is created and auto-served by FastAPI at http://localhost:8000/ui
```

## Docker

```powershell
# From docker/ directory:
docker compose up --build
# Frontend → http://localhost:8080
# Backend  → http://localhost:8000
```

## Tech Stack
- **Vue 3** + Composition API + `<script setup>`
- **Vite 5** — HMR dev server, proxy to FastAPI
- **TypeScript** strict mode
- **Tailwind CSS v3** — dark/light theme, custom design tokens
- **ECharts 5** — candlestick, heatmap, gauge, radar, scatter
- **Pinia** — theme, toast, market state
- **Axios** — centralized API client with retry + toast on error
