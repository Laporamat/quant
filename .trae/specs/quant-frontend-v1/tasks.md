# Quant Frontend v1 — Implementation Tasks

## Task Map to Spec ACs

| Task | Covers AC(s) | Priority |
|------|-------------|----------|
| 1 | AC-R1, AC-R13, NFR-08 | High |
| 2 | AC-R14, NFR-03, NFR-04, AC-Q1 | High |
| 3 | AC-R3, AC-Q2 | High |
| 4 | AC-R4, AC-Q2, AC-Q3 | High |
| 5 | AC-R5, AC-Q2 | High |
| 6 | AC-R6, AC-R7, AC-R8, AC-R9, AC-Q3 | High |
| 7 | AC-R10, AC-Q2 | High |
| 8 | AC-Q2 | Medium |
| 9 | AC-R11, AC-Q2 | Medium |
| 10 | AC-R12, AC-Q2 | Medium |
| 11 | AC-R1, AC-R13, NFR-01 | High |

---

## Task 1: Scaffold Vue 3 + Vite + TypeScript + Tailwind Project

**Status: pending**
**Priority: high**

### Objective
สร้างโปรเจค Vue 3 + Vite + TypeScript + Tailwind CSS v3 + Pinia + Vue Router พร้อม Config Dev Proxy ไปยัง FastAPI (localhost:8000)

### Sub-steps
1.1 Initialize `frontend/` ด้วย `npm create vite@latest frontend -- --template vue-ts`
1.2 ติดตั้ง Dependencies: `pinia`, `vue-router@4`, `axios`, `echarts`, `vue-echarts`, `dayjs`, `@vueuse/core`
1.3 ติดตั้ง Dev Dependencies: `tailwindcss@3`, `postcss`, `autoprefixer`, `@types/node`, `typescript`, `eslint`, `prettier`
1.4 Setup `tailwind.config.js` — define custom theme (Primary/Secondary/Accent/Semantic Colors, Font Family, Box Shadows, Animation Keyframes)
1.5 Setup `src/styles/main.css` — Tailwind directives + base utility classes (scrollbar, glass, card)
1.6 Setup `src/api/client.ts` — Axios instance with baseURL `/api`, timeout, retry, interceptors (attach token, handle error with toast)
1.7 Setup `src/api/` modules: `dataApi.ts`, `statsApi.ts`, `indicatorsApi.ts`, `strategyApi.ts`, `backtestApi.ts`, `optimizeApi.ts` (map ทุก endpoint จาก README.md)
1.8 Setup `src/stores/` modules: `marketStore.ts`, `appStore.ts` (theme, sidebarOpen, global loading)
1.9 Setup `src/router/index.ts` — 8 Routes (Dashboard, Ticker, Compare, Stats, Backtest, CompareStrat, Optimizer, MonteCarlo) + 404
1.10 Update `vite.config.ts` — Server proxy: `/api` → `http://localhost:8000`, port 5173, alias `@/`
1.11 Setup Types: `src/types/index.ts` (TickerInfo, PriceBar, Stats, BacktestResult, etc.)

### Test Requirements
- **TR-1.1 (rule)**: `cd frontend && npm run build` ไม่มี Error
- **TR-1.2 (rule)**: `npm run dev` เปิด `http://localhost:5173` เห็น Welcome Screen พร้อม 8 Nav Links
- **TR-1.3 (rule)**: ไปที่ `/dashboard` และ Console Network tab เห็น Request ไป `http://localhost:8000/api/health` (ผ่าน proxy) ถ้าจะเรียก

### Read-first Paths
- [config.py](file:///c:/appAI/quant/config.py) — Universe / Ticker list
- [api/main.py](file:///c:/appAI/quant/api/main.py) — Route prefixes
- [README.md](file:///c:/appAI/quant/README.md) — API endpoints table

---

## Task 2: Global Layout, Theme System, Animations, and Shared Components

**Status: pending**
**Priority: high**

### Objective
สร้าง Global Layout: Sidebar Navigation + Topbar + Theme Toggle + Shared Components (Metric Card, KPI Row, Chart Card, DataTable, SectionHeader, LoadingSkeleton, EmptyState, Toast)

### Sub-steps
2.1 `src/layouts/AppLayout.vue` — Sidebar (Collapsible, icons), Topbar (Breadcrumb, Theme Toggle, API Status), Main Content Area
2.2 `src/components/shared/AppSidebar.vue` — 8 Nav Items with icons, active highlight, collapse animation
2.3 `src/components/shared/ThemeToggle.vue` — Light/Dark with spring animation + CSS variables (persist to localStorage)
2.4 `src/components/shared/MetricCard.vue` — Title, Value, Delta (↑↓), Icon, Sparkline (optional), Hover lift animation
2.5 `src/components/shared/ChartCard.vue` — Title, toolbar (download, refresh, expand), slot content, header subtitle
2.6 `src/components/shared/DataTable.vue` — Sortable Columns, Search, Pagination, Loading Skeleton, EmptyState
2.7 `src/components/shared/SectionHeader.vue` — Title + Description + Action Button slot
2.8 `src/components/shared/LoadingSkeleton.vue` — Line skeletons, MetricCard skeletons, Chart area skeleton
2.9 `src/components/shared/ToastSystem.vue` — Pinia toasts (success/warning/error/info) with auto-dismiss + slide animation
2.10 `src/components/shared/TickerSearch.vue` — Autocomplete Search input (debounce, multi-select mode optional)
2.11 `src/components/shared/DateRangePicker.vue` — Presets (1M/3M/6M/1Y/3Y/5Y/MAX) + Custom Range
2.12 Animations: Router transition (`page-fade-slide`), Metric number count-up Tween, Chart entrance animation (ECharts animationDurationUpdate=600 easing=quinticOut)

### Test Requirements
- **TR-2.1 (rule)**: กด Theme Toggle เปลี่ยนระหว่าง Light/Dark ได้ แล้ว Refresh Page คงค่าเดิม
- **TR-2.2 (rule)**: Sidebar บีบ/ขยายได้ด้วย animation ไม่กระตุก
- **TR-2.3 (rule)**: 8 Menu Items สามารถคลิกแล้วเปลี่ยน Route ได้ครบถ้วน
- **TR-2.4 (rubric — AC-Q1 Visual Quality)**: 0-5 scale, threshold ≥ 3

### Read-first Paths
- N/A — greenfield build

---

## Task 3: Market Dashboard Page

**Status: pending**
**Priority: high**

### Objective
สร้างหน้า `/dashboard` — Market Overview สำหรับ SP100/SET50: Benchmark Performance (YTD-10Y), Top Gainers/Losers, Sector Bar Chart, Market Breadth (SMA50/SMA200)

### Sub-steps
3.1 `src/views/DashboardView.vue` — 4 Sections: Benchmark KPIs, Top Movers, Sector Performance, Market Breadth
3.2 Benchmark Row: 6 MetricCard (SPY/QQQ/IWM/GLD/TLT/VTI) — แสดง Return สำหรับ YTD, 1Y, 3Y, 5Y, 10Y, ALL (เรียก `/stats/returns/{ticker}` จากหลาย ticker พร้อมกันด้วย Promise.all)
3.3 Top Gainers / Losers Section: DataTable 2 คอลัมน์ side-by-side — Columns: Ticker, Last Price, Daily %, Monthly %, 1Y %
3.4 Sector Performance — Vertical Bar Chart (11 Sectors) โดยเรียก `/data/universe/{name}/sectors` + compute return จาก tickers ในแต่ละ sector (นำหนักโดยเท่าๆ กัน)
3.5 Market Breadth Gauge — 2 Gauge Charts (ECharts Gauge): % SP100 อยู่เหนือ SMA50, % อยู่เหนือ SMA200
3.6 Universe Switcher (Topbar ของหน้า): SP100 / SET50 / Benchmark — Switch แล้ว Data ทั้งหน้า Refresh
3.7 Responsive: Mobile → Stack Gainers/Losers เป็นแนวตั้ง

### Test Requirements
- **TR-3.1 (rule)**: Universe = SP100 → Sector Chart แสดง 11 Sectors พร้อม Value
- **TR-3.2 (rule)**: Top Gainers Table มี Data (ไม่ Empty State) เมื่อมี Data ใน Backend
- **TR-3.3 (rule)**: Click Universe Switcher เปลี่ยน Label ได้ และ State ถูกเก็บใน Pinia
- **TR-3.4 (rubric — AC-Q2 Information Density)**: 0-5, threshold ≥ 3

### Read-first Paths
- [api/routers/data_router.py](file:///c:/appAI/quant/api/routers/data_router.py#L89-L115) — /data/universe, /data/sectors
- [config.py](file:///c:/appAI/quant/config.py#L148-L161) — SECTOR_ETFS mapping, UNIVERSE_MAP

---

## Task 4: Ticker Deep Dive Page (Historical Analysis Task 1)

**Status: pending**
**Priority: high**

### Objective
สร้างหน้า `/ticker/:symbol` — Deep Dive หุ้นรายตัว: Candlestick + Indicators + 8 Descriptive Stats + 8 Risk Metrics + Monthly Heatmap + Underwater Curve + Return Distribution

### Sub-steps
4.1 `src/views/TickerDeepDive.vue` — Header (Ticker, Last Price, Change, Sector), TickerSearch, DateRangePicker
4.2 Price Panel: 2-row Chart (Candlestick + Volume) ด้วย ECharts Candlestick series + Volume Bar — Toggle Overlay: SMA(20,50,200), BB(20,2) (Checkbox)
4.3 Indicator Subplots: RSI(14) Panel + MACD(12,26,9) Panel (Histogram + Signal)
4.4 Descriptive Stats Grid — 8 MetricCard: Count, Mean, Median, Std, Skew, Kurt, Hurst, Autocorr1 (API: `/stats/descriptive/{ticker}`)
4.5 Risk Metrics Grid — 8 MetricCard: Sharpe, Sortino, Calmar, Omega, MaxDD, VaR95, CVaR95, Ulcer (API: `/stats/risk/{ticker}`)
4.6 Monthly Returns Heatmap: ECharts Heatmap, Year × Month, Colorscale RdYlGn, values เป็น % (API: `/stats/returns/{ticker}` → จากนั้น Client compute monthly table หรือเรียก `/stats/returns` แล้วแปลง)
4.7 Drawdown / Underwater Curve: Area Chart (fill to zero, red gradient) — API `/stats/drawdown/{ticker}`
4.8 Return Distribution: Histogram + Normal Overlay Line — API `/stats/distribution/{ticker}`
4.9 Sidebar: Quick Stats (Start Date, End Date, Rows, CAGR, Ann Volatility)
4.10 URL Sync: ถ้าเปลี่ยน Date Range → Update query params (`?start=...&end=...`) ทำให้ Copy Paste Share ได้

### Test Requirements
- **TR-4.1 (rule)**: ไปที่ `/ticker/AAPL` → Candlestick แสดงข้อมูลจริง ไม่มี Error (ถ้ามี data)
- **TR-4.2 (rule)**: 8 Descriptive + 8 Risk Cards แสดง Value (ไม่ NaN / Error)
- **TR-4.3 (rule)**: Monthly Heatmap มีอย่างน้อย 10 Rows (Years) ถ้าข้อมูล 20 ปี
- **TR-4.4 (rubric — AC-Q3 Historical Depth)**: 0-5, threshold ≥ 3 (สำหรับหน้านี้)

### Read-first Paths
- [api/routers/stats_router.py](file:///c:/appAI/quant/api/routers/stats_router.py#L33-L179) — descriptive, returns, risk, drawdown, distribution
- [utils/plotting.py](file:///c:/appAI/quant/utils/plotting.py) — chart types reference
- [api/routers/indicators_router.py](file:///c:/appAI/quant/api/routers/indicators_router.py) — RSI/MACD/Bollinger endpoints

---

## Task 5: Multi-Asset Comparison Page (Historical Analysis Task 2)

**Status: pending**
**Priority: high**

### Objective
สร้างหน้า `/compare` — เลือก 2-10 Tickers เปรียบเทียบ: Normalized Equity, Rolling 1Y Returns, Correlation Heatmap, Comparison Table, Risk-Return Scatter

### Sub-steps
5.1 `src/views/CompareAssets.vue` — Multi TickerSearch (Chips แสดงรายการที่เลือก), DateRangePicker, Benchmark Ticker Select
5.2 Normalized Equity Curve: Multi-line Chart (Rebase ทุก ticker = 1.0 ที่วันแรก) พร้อม Benchmark (เส้นประ)
5.3 Rolling 1Y Return Chart: Stacked Area Chart (หรือ Multi-line) สำหรับ rolling_beta / rolling_sharpe
5.4 Correlation Matrix Heatmap: N×N ECharts Heatmap, zmin=-1 zmax=1, zmid=0, Colorscale RdBu, แสดงค่าบนเซลล์
5.5 Risk-Return Scatter Plot: X=Ann Volatility, Y=CAGR, Bubble Size=Max Drawdown magnitude, Color=Ticker
5.6 Comparison Metrics Table: DataTable sortable (Columns: Ticker, CAGR, Sharpe, Sortino, MaxDD, Vol, WinRate, VaR95)
5.7 Add "Quick Sets": แบตช์ล่วงหน้า — "FAANG" (AAPL,MSFT,GOOGL,AMZN,META), "AI Leaders" (NVDA,MSFT,GOOGL,META,AMD), "SET50 Top 10"

### Test Requirements
- **TR-5.1 (rule)**: เลือก AAPL,MSFT,GOOGL → Correlation Heatmap 3×3 มีค่าทุกเซลล์
- **TR-5.2 (rule)**: Normalized Equity Line เริ่มที่ 1.0 ทุกเส้น
- **TR-5.3 (rule)**: Quick Set "FAANG" เมื่อกด → Ticker Chips เปลี่ยนทันทีและ Charts Refresh

### Read-first Paths
- [api/routers/stats_router.py](file:///c:/appAI/quant/api/routers/stats_router.py#L111-L124) — /stats/correlation endpoint (POST body)

---

## Task 6: Statistical Analysis Hub (Historical Tasks 3-6 — 4 Tasks)

**Status: pending**
**Priority: high**

### Objective
สร้างหน้า `/stats-hub` — 4 Tabs ย่อย:
**Regime Detection** (Task 3), **Seasonality** (Task 4), **Tail Risk** (Task 5), **Rolling Stats** (Task 6)

### Sub-steps
6.1 `src/views/StatsHub.vue` — 4 Tabs (Header Tab Bar with Underline Animation) + Ticker Search + DateRangePicker (global สำหรับทุก Tab)
6.2 **Tab 1 — Regime (Task 3)**: HMM Regime Stacked Area Chart (State 0/1/2 → Bull/Bear/Sideways), Regime Stats Table (Regime, % Time, Avg Return, Volatility, Count), Interpretation Summary ("20 ปีล่าสุด อยู่ใน Bull 62% Bear 14% Sideways 24%")
6.3 **Tab 2 — Seasonality (Task 4)**: Day-of-Week Effect Bar Chart (Mon-Fri, error bar std), Month-of-Year Effect Bar Chart (Jan-Dec), January Effect Result Card (Boolean + p-value), Monday Effect Result Card (Boolean + p-value)
6.4 **Tab 3 — Tail Risk (Task 5)**: VaR Comparison Table (Method, 95%, 99%), Distribution Fit Result Card (Best Name, Params, KS p-value), Tail Risk Curve (Log-scale Extreme Quantile Chart)
6.5 **Tab 4 — Rolling Stats (Task 6)**: Rolling 1Y Sharpe Line Chart, Rolling 1Y Volatility Area Chart, Rolling 1Y Beta vs SPY Line Chart (3 Charts Stacked Vertical)

### Test Requirements
- **TR-6.1 (rule)**: Regime Tab → API `/stats/regime/{ticker}` → ส่ง Regime Chart 252 วันล่าสุด
- **TR-6.2 (rule)**: Seasonality Tab → Day-of-Week มี 5 Bars, Month มี 12 Bars
- **TR-6.3 (rule)**: Tail Risk Tab → VaR Table มี 3 Rows (Hist, Param, CF) หรือมากกว่า
- **TR-6.4 (rule)**: Rolling Tab → 3 Stacked Charts แสดง Line อย่างน้อย 200 จุด
- **TR-6.5 (rubric — AC-Q3)**: 0-5, threshold ≥ 3

### Read-first Paths
- [api/routers/stats_router.py](file:///c:/appAI/quant/api/routers/stats_router.py#L126-L179) — /stats/regime, /stats/seasonality, /stats/distribution
- [stats/regime_detection.py](file:///c:/appAI/quant/stats/regime_detection.py) — HMM / MA regimes
- [stats/seasonality.py](file:///c:/appAI/quant/stats/seasonality.py) — effects
- [stats/distribution.py](file:///c:/appAI/quant/stats/distribution.py) — VaR/CVaR/Dist fits

---

## Task 7: Backtest Lab Page (Historical Analysis Task 7)

**Status: pending**
**Priority: high**

### Objective
สร้างหน้า `/backtest` — Run Backtest ผ่าน Form UI: Strategy, Tickers, Params → Run → ดูผล: Equity, Drawdown, Metrics, Trade Log, Heatmap

### Sub-steps
7.1 `src/views/BacktestLab.vue` — 2 Column Layout: Left (Config Form) | Right (Result Area, hidden ก่อนรัน)
7.2 Config Form (Left):
  - Strategy Select Dropdown (10 items + Description tooltip)
  - Multi-Select Tickers + Benchmark
  - Initial Capital Input (number, thousand separator), Commission Slider (0-1%), Slippage Slider (0-0.5%)
  - Position Sizing Radio (Equal / Vol-Target / Kelly)
  - Strategy Dynamic Params (JSON Schema Form — ตัวอย่าง sma_crossover: sma_fast=20, sma_slow=50 sliders)
  - "Run Backtest" Button (primary, large, loading spinner + progress percent)
7.3 Result Area (Right, แสดงเมื่อสำเร็จ):
  - Top KPI Row: CAGR, Sharpe, MaxDD, Calmar, WinRate, Trades
  - Equity Chart: Strategy + Benchmark (2 lines, benchmark dashed)
  - Drawdown Curve (red fill)
  - Monthly Returns Heatmap
  - Trade Log DataTable: Date, Ticker, Side, Entry, Exit, PnL, Return%, Duration
7.4 "Save Report" Actions: Download JSON / Open HTML Report (new tab ไป `/backtest/{id}/report`)
7.5 Backtest History Side Panel: List Recent Runs (strategy, date, sharpe) — click เพื่อโหลดผลเก่า (API `/backtest/list`)

### Test Requirements
- **TR-7.1 (rule)**: Run `sma_crossover` → AAPL,MSFT → 2018-01-01 ถึง 2024-12-31 → ได้ผลลัพธ์ (equity_curve มีอย่างน้อย 1000 points)
- **TR-7.2 (rule)**: Trade Log Table มีข้อมูล (≥ 1 row)
- **TR-7.3 (rule)**: Metrics Cards แสดงค่าถูกต้องตาม API Response
- **TR-7.4 (rubric — AC-Q2 Info Density)**: 0-5, threshold ≥ 3

### Read-first Paths
- [api/routers/backtest_router.py](file:///c:/appAI/quant/api/routers/backtest_router.py#L26-L134) — /backtest/run, /list, /{id}, /report
- [api/schemas/backtest_schema.py](file:///c:/appAI/quant/api/schemas/backtest_schema.py) — Request/Response shapes
- [strategies/__init__.py](file:///c:/appAI/quant/strategies/__init__.py) — STRATEGY_REGISTRY list

---

## Task 8: Strategy Comparison Page

**Status: pending**
**Priority: medium**

### Objective
สร้างหน้า `/strategy-compare` — Select 2-5 Backtest Runs แล้วเปรียบเทียบ

### Sub-steps
8.1 `src/views/StrategyCompare.vue` — Select Multiple Backtest Runs (Checkbox List จาก `/backtest/list`), Benchmark Select
8.2 Normalized Equity Chart: Multi-line สำหรับทุก Strategy
8.3 Comparison Table: ทุก Strategy เป็น Row, Columns = CAGR, Sharpe, Sortino, Calmar, MaxDD, Vol, WinRate, Trades, ProfitFactor
8.4 Radar Chart: 6 Axes (Sharpe, Sortino, Calmar, Omega, WinRate, ProfitFactor) — Normalized 0-100 (เทียบสูงสุดในกลุ่ม)
8.5 "Best Overall" Badge — Auto select strategy ที่มี Sharpe สูงสุด

### Test Requirements
- **TR-8.1 (rule)**: Select ≥ 2 Runs → Radar Chart แสดง Polygon ทุกอัน
- **TR-8.2 (rule)**: Comparison Table Rows = จำนวน Runs ที่เลือก

### Read-first Paths
- [api/routers/backtest_router.py](file:///c:/appAI/quant/api/routers/backtest_router.py#L93-L123) — /backtest/list, /{id}

---

## Task 9: Strategy Optimizer Page (Historical Analysis Task 8)

**Status: pending**
**Priority: medium**

### Objective
สร้างหน้า `/optimizer` — Grid Search / Walk-Forward: Define Parameter Grid → Run → Results Table + Surface Plot

### Sub-steps
9.1 `src/views/StrategyOptimizer.vue` — Strategy + Tickers + Date Range + Metric Dropdown
9.2 Parameter Grid Builder: สำหรับแต่ละ Strategy param ที่ user กด "Add Param" → เลือก Key, ป้อน Values (comma-separated) หรือ Min/Max/Step
9.3 "Run Grid Search" Button — Loading Progress (จำนวน configs รวม, รองเท่าไหน), Result Table Refresh ทุกๆ N config ถ้าเป็นไปได้ (หรือเอาหมดเวลาเลย)
9.4 Results DataTable: Param Cols + Metric Value + Rank (Sort by Metric, default DESC)
9.5 2D Surface Plot: เลือก X=Param A, Y=Param B → Heatmap ของ Metric Value (Z)
9.6 Top 5 Best Params Cards: แต่ละ Card มี "Apply to Backtest Lab" ปุ่ม → Navigate ไป `/backtest` พร้อม pre-fill params
9.7 Walk-Forward Section: Window Size (days/years), Step Size, Metric → Run → Results: Walk-Forward Equity Curve + Rolling Window Performance Bars

### Test Requirements
- **TR-9.1 (rule)**: Grid Search sma_crossover — fast=[10,20,30], slow=[50,100,200] → Result Table มี 9 Rows (3×3)
- **TR-9.2 (rule)**: Surface Plot เมื่อเลือก X=fast, Y=slow → Heatmap 3×3
- **TR-9.3 (rubric — AC-Q2 Info Density)**: 0-5, threshold ≥ 3

### Read-first Paths
- [api/routers/optimize_router.py](file:///c:/appAI/quant/api/routers/optimize_router.py) — Grid + Walk-Forward endpoints
- [backtester/optimizer.py](file:///c:/appAI/quant/backtester/optimizer.py) — return structure

---

## Task 10: Monte Carlo Simulator Page

**Status: pending**
**Priority: medium**

### Objective
สร้างหน้า `/monte-carlo` — Simulate Equity Paths: Percentile Bands + Final Wealth Distribution + Probability Table

### Sub-steps
10.1 `src/views/MonteCarloView.vue` — Ticker Select, Method Toggle (Bootstrap / Parametric), Horizon Slider (63/126/252/504/1260 วัน), Num Sims Slider (100/500/1000/5000/10000)
10.2 Percentile Bands Chart: 5 Line Series (P5 red, P25 orange, P50 black/thick, P75 light green, P95 dark green) — filled bands ระหว่าง P25-P75 (light fill)
10.3 Stats KPI Row: Mean Ending Wealth, Median, P5 (worst 5%), P95 (best 5%), Prob(Loss > 0%), Prob(Gain > 5%), Prob(Gain > 10%)
10.4 Final Wealth Histogram: Vertical Bar, Colorscale (red < 1.0, green > 1.0), KDE Overlay Line
10.5 "Run Again" Button + Seed Input (optional reproducibility)
10.6 Sample Paths Preview: Optional Toggle — แสดง 20 Random Paths (semi-transparent gray lines) บน Percentile Chart

### Test Requirements
- **TR-10.1 (rule)**: SPY, Bootstrap, 1000 sims, 252 days → Stats KPI แสดง Mean, P5, P95 เป็นตัวเลข (ไม่ NaN)
- **TR-10.2 (rule)**: Percentile Chart มี 5 Lines (P5/P25/P50/P75/P95) ทั้งหมด

### Read-first Paths
- [api/routers/backtest_router.py](file:///c:/appAI/quant/api/routers/backtest_router.py#L136-L165) — /backtest/monte-carlo (POST)
- [backtester/monte_carlo.py](file:///c:/appAI/quant/backtester/monte_carlo.py) — path generation

---

## Task 11: Integration, Final Polish, Docker

**Status: pending**
**Priority: high**

### Objective
รวมทุกอย่าง: Error Handling, Polish, Build Success, Docker Integration, Data Download Shortcut Script

### Sub-steps
11.1 Error Boundary: Wrap Router View ด้วย Error Boundary component
11.2 Fallback UI: ทุก API Error → Toast + Retry Button ใน ChartCard
11.3 Empty States: ทุก Page / Section มี Empty State Component (Icon + Text + CTA Button)
11.4 `Dockerfile.frontend` สำหรับ Production — multi-stage (node build → nginx:alpine), expose 80
11.5 Update `docker/docker-compose.yml` — เพิ่ม service `frontend` (Build from Dockerfile.frontend, port 8080, depends on api), Update nginx.conf (if any) to proxy `/api` → api:8000
11.6 404 Page (src/views/NotFoundView.vue)
11.7 Home `/` redirect → `/dashboard`
11.8 Run `npm run build` → เก็บ build artifacts (dist)
11.9 (Optional) FastAPI Static Serve: ถ้า Frontend build แล้ว ให้ FastAPI serve `frontend/dist` ที่ path `/ui` (เพิ่มใน api/main.py ด้วย StaticFiles) — ให้ผู้ใช้เปิด `http://localhost:8000/ui` ได้เลยโดยไม่ต้องรัน Vite
11.10 Script `start-dev.ps1` — รอสักครู่ backend (python main.py) + รอ frontend (cd frontend && npm run dev) ใน 2 Terminal windows ในคราวเดียว

### Test Requirements
- **TR-11.1 (rule)**: `cd frontend && npm run build` exit code 0, no TS errors
- **TR-11.2 (rule)**: ไปที่ `/not-existing-route` เห็น NotFound Page (ไม่ white screen)
- **TR-11.3 (rule)**: Build แล้ว dist/ folder มี index.html + assets
- **TR-11.4 (rubric — AC-Q1 Visual Quality)**: Final 0-5, threshold ≥ 3

### Read-first Paths
- [api/main.py](file:///c:/appAI/quant/api/main.py) — FastAPI app factory (เพิ่ม StaticFiles mount)
- [docker/docker-compose.yml](file:///c:/appAI/quant/docker/docker-compose.yml) — existing services

---

## Dependencies

```
Task 1 → Task 2 → Task 3, Task 4, Task 5, Task 6, Task 7, Task 8, Task 9, Task 10 → Task 11
```

Task 3-10 ไม่มีขึ้นอยู่ซึ่งกันและกันหลังจาก Task 2 เสร็จ → สามารถทำขนานได้ถ้ามี sub-agents
