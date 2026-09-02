# Quant Trading System — Frontend + Historical Data Analysis

## 1. ปัญหา / เป้าหมาย

### ปัญหา (Problem)
ระบบ Quant Backend ปัจจุบันมี API ครบถ้วน (Data / Stats / Indicators / Strategy / Backtest / Optimize) และ CLI Scripts แต่ **ไม่มีหน้า UI Web จริงๆ** ที่ทำให้ผู้ใช้สามารถ:
- ดูภาพรวมการวิเคราะห์ข้อมูล Historical Data ได้แบบ Interactive
- เปรียบเทียบหุ้น หลายตัวพร้อมกัน
- Run Backtest ผ่านหน้าเว็บโดยไม่ต้องรัน CLI
- ดูผลการวิเคราะห์ (Stats, Risk, Drawdown, Correlation, Regime, Seasonality) แบบ Dashboard

### เป้าหมาย (Goals)
1. **สร้าง Frontend Dashboard (SPA)** ที่สวยงาม ทันสมัย มี Animation + Smooth UX เหมือนเว็บไซต์บริษัทขนาดใหญ่ (ระดับ Entrepreneur/Enterprise)
2. **สร้าง Task การวิเคราะห์ Historical Data ที่ชัดเจน 8 Tasks** โดยใช้ข้อมูลย้อนหลัง 20 ปี (SP100 / SET50 / Benchmark ETFs)
3. **เชื่อมต่อ Frontend กับ Backend API** ที่มีอยู่แล้ว — ไม่ต้องแก้ API เดิม (แต่ถ้าจำเป็นอาจเพิ่ม Endpoint เสริมเล็กน้อย)
4. **Deploy ในรูปแบบเดียวกับระบบเดิม** — Frontend Static Files ถูก Serve จาก FastAPI โดยตรง (หรือรันแยก Vite Dev Server สำหรับพัฒนา)

### ไม่ทำ (Non-Goals)
- ไม่สร้างระบบ Authentication / User Management (รอบนี้)
- ไม่สร้าง Real-time Live Trading (รอบนี้เป็น Historical Analysis + Backtest เท่านั้น)
- ไม่เปลี่ยน Strategy / Backtester Logic เดิม — ใช้ของเดิม
- ไม่ทำ Mobile App (รองรับ Responsive Web เท่านั้น)

---

## 2. ผู้ใช้และ Use Cases

### ผู้ใช้หลัก (Primary User)
- Quant Researcher / Trader ที่ต้องการสำรวจข้อมูลหุ้นย้อนหลัง + ทดสอบกลยุทธ์
- ต้องการ UI ที่รวดเร็ว สวยงาม มี Interactive Charts

### Use Cases หลัก
| ID | Use Case | คำอธิบาย |
|----|----------|----------|
| UC-01 | ดูภาพรวม Market Dashboard | SP100/SET50 Performance, Top Gainers/Losers, Sector Breakdown |
| UC-02 | วิเคราะห์หุ้นรายตัว Deep Dive | Candlestick + Indicators + Descriptive Stats + Risk + Drawdown |
| UC-03 | เปรียบเทียบหลายหุ้น | Normalized Equity, Correlation Heatmap, Return Distribution |
| UC-04 | Statistical Analysis Dashboard | Regime Detection, Seasonality, Factor Analysis, Tail Risk |
| UC-05 | Run Backtest ผ่าน UI | เลือก Strategy + Tickers + Date Range + Parameters → ดูผล Real-time |
| UC-06 | Compare Strategies | เปรียบเทียบผล Backtest หลายๆ กลยุทธ์พร้อมกัน (Equity + Metrics Table) |
| UC-07 | Strategy Optimizer | Grid Search / Walk-Forward Optimization ผ่าน UI |
| UC-08 | Monte Carlo Simulator | สร้าง Forecast Paths + Percentile Bands สำหรับหุ้น/พอร์ต |

---

## 3. Functional Requirements (FR)

### FR-01: Frontend Architecture
- **FR-1.1**: ใช้ **Vue 3 + Vite + TypeScript + Tailwind CSS v3** เป็น Frontend Stack
- **FR-1.2**: ใช้ **ECharts 5** สำหรับ Charts หลัก (Candlestick, Heatmap, Correlation) + **Plotly.js** สำหรับ Charts พิเศษ (ถ้าจำเป็น)
- **FR-1.3**: ใช้ **Pinia** สำหรับ State Management
- **FR-1.4**: ใช้ **Vue Router** สำหรับ Navigation 8 Pages
- **FR-1.5**: Frontend Directory อยู่ที่ `frontend/` (แยกจาก Backend)
- **FR-1.6**: มี Light/Dark Theme Toggle (Animations)
- **FR-1.7**: Responsive Design — รองรับ Desktop 1920px → Tablet 768px
- **FR-1.8**: Loading Skeleton + Skeleton Screens สำหรับทุกหน้าที่มีการเรียก API

### FR-02: Market Dashboard (Page 1)
- **FR-2.1**: แสดง Overview Metrics: SPY / QQQ / SET Total Return (YTD, 1Y, 3Y, 5Y, 10Y, ALL)
- **FR-2.2**: Top 10 Gainers / Losers จาก SP100 (วันล่าสุด, เดือนล่าสุด)
- **FR-2.3**: Sector Performance Bar Chart (11 Sectors ของ SP100)
- **FR-2.4**: Market Breadth Indicator (จำนวนหุ้น SP100 ที่อยู่เหนือ SMA50 / SMA200)
- **FR-2.5**: Universe Selector (SP100 / SET50 / Benchmark)

### FR-03: Ticker Deep Dive (Page 2) — Historical Analysis Task 1
- **FR-3.1**: Candlestick Chart พร้อม Volume + SMA/EMA/Bollinger Bands (Toggle ได้)
- **FR-3.2**: RSI + MACD Subplots (ด้านล่าง Candlestick)
- **FR-3.3**: Descriptive Stats Cards (Mean, Std, Skew, Kurtosis, Hurst Exponent, Autocorr1)
- **FR-3.4**: Risk Metrics Cards (Sharpe, Sortino, Calmar, Omega, MaxDD, VaR95, CVaR95, Ulcer Index)
- **FR-3.5**: Monthly Returns Heatmap (ปี × เดือน)
- **FR-3.6**: Underwater / Drawdown Curve
- **FR-3.7**: Return Distribution Histogram + Normal Overlay
- **FR-3.8**: Date Range Picker (Custom / 1M / 3M / 6M / 1Y / 3Y / 5Y / MAX)
- **FR-3.9**: Ticker Search Box + Autocomplete จาก Universe

### FR-04: Multi-Asset Comparison (Page 3) — Historical Analysis Task 2
- **FR-4.1**: เลือก 2–10 Tickers สำหรับเปรียบเทียบ
- **FR-4.2**: Normalized Equity Curve (Growth of $1) ทุกรายการบนกราฟเดียว
- **FR-4.3**: Rolling 1Y Return Area Chart (หลายหุ้น)
- **FR-4.4**: Correlation Matrix Heatmap (N×N) พร้อม Cluster
- **FR-4.5**: Comparison Metrics Table (CAGR, Sharpe, MaxDD, Volatility, Win Rate, Sortino)
- **FR-4.6**: Scatter Plot: Risk (X) vs Return (Y) แบบ Bubble

### FR-05: Statistical Analysis Hub (Page 4) — Historical Analysis Tasks 3-6
**5 Tasks ย่อย ที่ชัดเจน:**
- **Task 3 — Regime Detection**: HMM 3-State (Bull/Bear/Sideways) Regime Chart + Regime Statistics Table (Avg Return per Regime, % Time in Regime, Volatility per Regime)
- **Task 4 — Seasonality Analysis**: Day-of-Week Effect Bar Chart, Month-of-Year Effect Bar Chart, January Effect Test, Monday Effect Test (Stat Significance)
- **Task 5 — Tail Risk & Distribution Analysis**: VaR (Hist/Param/CF) Comparison Table, CVaR, Expected Shortfall, Best-Fit Distribution (with parameters), t-Distribution fit
- **Task 6 — Rolling Statistics**: Rolling 1Y Sharpe, Rolling 1Y Volatility, Rolling 1Y Beta vs SPY (Overlay)

### FR-06: Backtest Lab (Page 5) — Historical Analysis Task 7
- **FR-6.1**: Strategy Selector (10 Strategies — พร้อม Description + Default Parameters)
- **FR-6.2**: Ticker Multi-Select + Benchmark Ticker Select
- **FR-6.3**: Date Range Picker + Initial Capital / Commission / Slippage Sliders
- **FR-6.4**: Position Sizing Method Select (Equal / Vol-Target / Kelly)
- **FR-6.5**: Strategy Parameters Form (Dynamic — ขึ้นอยู่กับ Strategy)
- **FR-6.6**: Run Button + Progress Indicator (Animation)
- **FR-6.7**: ผลลัพธ์: Equity Curve (Strategy vs Benchmark), Drawdown Curve, Performance Cards, Trade Log Table, Monthly Returns Heatmap
- **FR-6.8**: Save Report Button → Download HTML / JSON

### FR-07: Strategy Comparison (Page 6)
- **FR-7.1**: Select 2-5 Past Backtest Runs เพื่อเปรียบเทียบ
- **FR-7.2**: Normalized Equity Curves บนกราฟเดียว
- **FR-7.3**: Comparison Table (CAGR, Sharpe, Sortino, Calmar, MaxDD, Volatility, WinRate, Total Trades, Profit Factor)
- **FR-7.4**: Radar Chart ของ Key Metrics (Normalized 0-100)

### FR-08: Strategy Optimizer (Page 7) — Historical Analysis Task 8
- **FR-8.1**: Strategy Select + Tickers + Date Range
- **FR-8.2**: Parameter Grid Builder (Define Min / Max / Step / Values for each param)
- **FR-8.3**: Grid Search Results Table (Sortable + Filterable)
- **FR-8.4**: Optimization Surface Plot (2 Params Heatmap)
- **FR-8.5**: Top-5 Best Parameter Cards พร้อม Action: "Apply to Backtest"
- **FR-8.6**: Walk-Forward Analysis Setup (Window / Step / Metric)

### FR-09: Monte Carlo Simulator (Page 8)
- **FR-9.1**: Ticker / Portfolio Select
- **FR-9.2**: Method: Bootstrap / Parametric
- **FR-9.3**: Horizon (Days) + Number of Simulations Sliders
- **FR-9.4**: Percentile Bands Chart (P5 / P25 / P50 / P75 / P95)
- **FR-9.5**: Probability of Gain / Loss at Horizon
- **FR-9.6**: Final Wealth Distribution Histogram

### FR-10: Data Management (Sidebar Utility)
- **FR-10.1**: Download Data Dialog (Universe Select + Force Refresh)
- **FR-10.2**: Available Tickers List + Status (Row Count / Date Range)

---

## 4. Non-Functional Requirements (NFR)

| ID | Requirement | Acceptance |
|----|-------------|------------|
| NFR-01 | Performance | First Contentful Paint < 2s; Page transition < 200ms; API Call Skeleton แสดง < 100ms |
| NFR-02 | Bundle Size | Frontend Production Gzip < 500KB (ECharts ใช้ Tree Shaking) |
| NFR-03 | Visual Quality | ทุก Chart มี Legend, Tooltip, Zoom, Download PNG Button; Colors Consistent Theme |
| NFR-04 | Animations | Router Transition (Fade + Slide), Chart Load Animation, Number Counter Tween, Hover Micro-interactions |
| NFR-05 | API Integration | ทุก API Request ผ่าน Axios Instance Centralized; Error Handling ด้วย Toast; Retry 1 ครั้งสำหรับ Network Error |
| NFR-06 | Error Handling | API Error → Toast + Fallback UI; Network Offline → Offline Indicator; 404 NotFound Page |
| NFR-07 | Browser Support | Chrome, Edge, Firefox ล่าสุด 2 Version |
| NFR-08 | Code Quality | ESLint + Prettier; TypeScript Strict Mode; Component < 300 lines |

---

## 5. Constraints / Dependencies / Assumptions

### Constraints
- ใช้ **Vue 3 + Vite** เท่านั้น — ห้ามเปลี่ยนเป็น React / Next.js
- ใช้ **ECharts** เป็น Chart Library หลัก (เพราะมี Candlestick + Heatmap + Animation ที่ดีกว่า Plotly สำหรับ UI)
- Backend API ใช้ของเดิม (FastAPI ที่ port 8000) — ห้ามแก้ Backtest / Strategy Core Logic
- Frontend Dev Server รันที่ port 5173 (Vite default) พร้อม Proxy ไป /api → http://localhost:8000

### Dependencies
- Node.js ≥ 18 + npm/yarn/pnpm
- Backend ต้องรันก่อน (python main.py) เพื่อให้ Frontend เรียก API ได้
- ถ้ายังไม่มีข้อมูล Historical Data — ต้อง Run `python scripts/download_data.py` ก่อน

### Assumptions
- ผู้ใช้ติดตั้ง Node.js และ Python 3.11+ แล้ว
- ต้องการ Professional UI ด้วย Tailwind CSS + Custom Animations (ตรงกับ User Profile)
- Historical Data สำหรับ SP100 (20 ปี) สามารถโหลดจาก yFinance ได้ภายในเวลาที่เหมาะสม

### Open Questions
- ❓ จะสร้าง **Docker Compose Service สำหรับ Frontend (Vite Dev + Nginx Production)** ไว้พร้อมกับของเดิมหรือไม่? (Default: YES)
- ❓ Ticker Deep Dive จะรองรับ **Compare 2 Tickers บน Chart เดียว** (Dual Axis) หรือไม่? (Default: YES)
- ❓ Backtest Result จะให้ **Export PDF** เพิ่มเติมจาก HTML/JSON หรือไม่? (Default: NO รอบแรก)

---

## 6. Acceptance Criteria

### AC (rule) — Binary / Verifiable
- **AC-R1**: Frontend สามารถ `npm run build` ได้สำเร็จ โดยไม่มี Error (TypeScript + Build)
- **AC-R2**: 8 Pages ทั้งหมดสามารถเปิดผ่าน Router ได้ โดยไม่มี Console Error
- **AC-R3**: Market Dashboard แสดง Sector Performance Chart ได้จริงจาก API `/data/universe/{name}/sectors`
- **AC-R4**: Ticker Deep Dive Page แสดง Candlestick + RSI + MACD + 8 Metrics Cards ได้จริงสำหรับ AAPL
- **AC-R5**: Multi-Asset Comparison สามารถเลือก AAPL,MSFT,GOOGL แล้วแสดง Correlation Heatmap 3×3 ได้
- **AC-R6**: Statistical Hub — Regime Detection แสดง 3-State HMM Chart + Stats Table สำหรับ SPY (2010-2024)
- **AC-R7**: Statistical Hub — Seasonality แสดง Day-of-Week + Month Effects สำหรับหุ้นใดหุ้นหนึ่ง
- **AC-R8**: Statistical Hub — Tail Risk แสดง VaR95 Hist / Param / CF + Best Fit Distribution
- **AC-R9**: Statistical Hub — Rolling Stats แสดง Rolling 1Y Sharpe + Volatility
- **AC-R10**: Backtest Lab สามารถ Run `sma_crossover` สำหรับ AAPL,MSFT ระหว่าง 2018-2024 และแสดง Equity Curve + Performance Cards
- **AC-R11**: Strategy Optimizer สามารถ Define Grid สำหรับ `sma_crossover` (sma_fast: [10,20,30], sma_slow: [50,100,200]) แล้วแสดง Results Table ได้
- **AC-R12**: Monte Carlo สำหรับ SPY Bootstrap 1000 sims / 252 วัน แสดง Percentile Bands Chart ได้
- **AC-R13**: Frontend `npm run dev` สามารถเชื่อมต่อกับ FastAPI (dev proxy) ได้สำเร็จ
- **AC-R14**: มี Light/Dark Toggle พร้อม Transition Animation ทุกหน้า
- **AC-R15**: All Chart มี Tooltip, Zoomable, และ Download PNG Option

### AC (rubric) — Evaluative
- **AC-Q1 (Visual Quality — 0-5)**:
  - 0: UI ขาดสเกล ไม่มี Theme
  - 1: ใช้ Tailwind แต่ไม่มี Animation ไม่มี Layout System
  - 2: มี Layout + Colors แต่ Animation หายาก
  - 3: มี Router Transition, Hover Effects, Skeleton — ความสวยระดับ Mid-tier SaaS
  - 4: Professional UI, Animations รัดกุม (Number Counter, Chart Entrance, Page Fade), Consistent Color Palette
  - 5: ระดับบริษัทขนาดใหญ่ — Micro-interactions ทุกจุด, Deep Layered Shadows, Motion Curves สวย
  - **Pass Threshold: ≥ 3**

- **AC-Q2 (Information Density — 0-5)**:
  - 0: Dashboard มีแค่ 1-2 Card เท่านั้น
  - 1: มีข้อมูลแต่กระจัดกระจาย ไม่มี Hierarchy
  - 2: แต่ละ Page มี 3-4 Components แต่ไม่สอดคล้องกัน
  - 3: แต่ละ Page มี Structure ชัดเจน (Header → KPIs → Charts → Details)
  - 4: Data Hierarchy เหมาะสม สามารถ Drill Down ได้จากภาพรวม → ละเอียด
  - 5: Dashboard Design มี Causal Link ระหว่าง Metrics — ผู้ใช้เข้าใจนิยามทันที
  - **Pass Threshold: ≥ 3**

- **AC-Q3 (Historical Analysis Depth — 0-5)**:
  - 0: แค่แสดง Prices เท่านั้น ไม่มี Stats
  - 1: มี Descriptive Stats พื้นฐาน (Mean/Std)
  - 2: มี Risk Metrics + Drawdown
  - 3: 8 Analysis Tasks ครบ: Regime, Seasonality, TailRisk, Rolling, 5 เพิ่มเติม
  - 4: แต่ละ Task มี Statistical Significance (p-value) และ Interpretation Text
  - 5: มี Insight Auto-generation (เช่น "SPY อยู่ใน Bear Regime 12% ของเวลา 20 ปีล่าสุด")
  - **Pass Threshold: ≥ 3**
