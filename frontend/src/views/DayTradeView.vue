<template>
  <div class="space-y-5 animate-fade-in">
    <!-- ── Header ──────────────────────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <div class="flex-1">
        <h1 class="text-xl font-bold text-surface-100 flex items-center gap-2">
          <span class="text-xs font-mono px-2 py-0.5 rounded bg-primary-600/20 text-primary-400 border border-primary-600/30">OCaml</span>
          Day Trade — Probability &amp; Pricing Engine
        </h1>
        <p class="text-sm text-surface-400 mt-0.5">
          Black-Scholes · Binomial Tree · GBM Cone · Bayesian Regime · VaR/CVaR · Kelly
          <span class="ml-2 text-xs text-surface-600">Engine: {{ engineLabel }}</span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-36">
          <TickerSearch :model-value="[ticker]" @update:model-value="v => { ticker = v[0] ?? 'SPY'; runRealtime() }" :multi="false" />
        </div>
        <select v-model="horizonDays" @change="runRealtime"
          class="bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-2 py-2 outline-none focus:border-primary-500">
          <option :value="1">1 Day</option>
          <option :value="3">3 Days</option>
          <option :value="5">5 Days</option>
          <option :value="10">10 Days</option>
          <option :value="21">1 Month</option>
        </select>
        <button @click="runRealtime" :disabled="loading"
          class="btn-primary flex items-center gap-1.5 px-4">
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/>
          </svg>
          Analyse
        </button>
      </div>
    </div>

    <!-- ── Tabs ─────────────────────────────────────────────────────────────── -->
    <div class="flex border-b border-surface-700/50 gap-1">
      <button v-for="tab in tabs" :key="tab.key"
        @click="activeTab = tab.key"
        class="tab-item" :class="{ active: activeTab === tab.key }">
        {{ tab.label }}
      </button>
    </div>

    <!-- ════════════════ TAB: REALTIME ════════════════ -->
    <div v-if="activeTab === 'realtime'" class="space-y-4">
      <!-- Loading skeleton -->
      <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div v-for="i in 8" :key="i" class="glass p-4 h-20 animate-skeleton rounded-xl" />
      </div>

      <template v-if="rt">
        <!-- ── KPI strip ── -->
        <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          <div class="metric-card col-span-2">
            <span class="text-xs text-surface-400 uppercase tracking-wider">{{ rt.ticker }}</span>
            <div class="text-2xl font-bold tabular-nums text-surface-100 mt-1">${{ rt.spot?.toFixed(2) }}</div>
            <div class="text-xs text-surface-400">Last price</div>
          </div>
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">Ann. Vol</span>
            <div class="text-xl font-bold text-side mt-1">{{ rt.ann_volatility?.toFixed(1) }}%</div>
          </div>
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">Ann. Drift</span>
            <div class="text-xl font-bold mt-1" :class="(rt.ann_drift ?? 0) >= 0 ? 'text-bull' : 'text-bear'">
              {{ rt.ann_drift >= 0 ? '+' : '' }}{{ rt.ann_drift?.toFixed(1) }}%
            </div>
          </div>
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">VaR 1D 95%</span>
            <div class="text-xl font-bold text-bear mt-1">{{ rt.var_1day_pct?.toFixed(2) }}%</div>
          </div>
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">CVaR 1D</span>
            <div class="text-xl font-bold text-bear mt-1">{{ rt.cvar_1day_pct?.toFixed(2) }}%</div>
          </div>
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">Kelly %</span>
            <div class="text-xl font-bold mt-1" :class="(rt.kelly_pct ?? 0) > 0 ? 'text-bull' : 'text-surface-400'">
              {{ rt.kelly_pct?.toFixed(1) }}%
            </div>
          </div>
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">Sharpe</span>
            <div class="text-xl font-bold mt-1" :class="(rt.sharpe ?? 0) >= 1 ? 'text-bull' : (rt.sharpe ?? 0) >= 0 ? 'text-side' : 'text-bear'">
              {{ rt.sharpe?.toFixed(2) }}
            </div>
          </div>
        </div>

        <!-- ── Regime + Break-even strip ── -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <!-- Bayesian regime gauge -->
          <div class="glass p-4 flex flex-col items-center gap-2">
            <span class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Bayesian Market Regime</span>
            <div class="relative w-full h-5 rounded-full bg-surface-700 overflow-hidden">
              <div class="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
                :style="{ width: (rt.bull_probability * 100).toFixed(1) + '%' }"
                :class="rt.regime === 'bull' ? 'bg-bull' : 'bg-bear'" />
            </div>
            <div class="flex justify-between w-full text-xs">
              <span class="text-bull font-semibold">Bull {{ (rt.bull_probability * 100).toFixed(1) }}%</span>
              <span class="px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider"
                :class="rt.regime === 'bull' ? 'bg-bull/15 text-bull' : 'bg-bear/15 text-bear'">
                {{ rt.regime }}
              </span>
              <span class="text-bear font-semibold">Bear {{ (rt.bear_probability * 100).toFixed(1) }}%</span>
            </div>
            <p class="text-xs text-surface-500 text-center">OCaml Bayesian update on last 20 daily returns</p>
          </div>

          <!-- ATM straddle / break-even -->
          <div class="glass p-4 space-y-2">
            <span class="text-xs font-semibold text-surface-400 uppercase tracking-wider">ATM Straddle ({{ horizonDays }}d)</span>
            <div class="text-2xl font-bold text-primary-400">${{ rt.atm_straddle?.toFixed(2) }}
              <span class="text-sm text-surface-400 font-normal">({{ rt.atm_straddle_pct?.toFixed(2) }}%)</span>
            </div>
            <div class="space-y-1 text-sm">
              <div class="flex justify-between">
                <span class="text-surface-400">Break-even ↑</span>
                <span class="text-bull font-mono font-semibold">${{ rt.break_even_upper?.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-surface-400">Break-even ↓</span>
                <span class="text-bear font-mono font-semibold">${{ rt.break_even_lower?.toFixed(2) }}</span>
              </div>
            </div>
            <p class="text-xs text-surface-500">Black-Scholes ATM call + put at {{ horizonDays }}-day expiry</p>
          </div>

          <!-- Win rate + Kelly -->
          <div class="glass p-4 space-y-3">
            <span class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Trade Sizing</span>
            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <span class="text-xs text-surface-400">Historical Win Rate</span>
                <span class="font-semibold" :class="(rt.win_rate ?? 0) > 0.5 ? 'text-bull' : 'text-bear'">
                  {{ ((rt.win_rate ?? 0) * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-xs text-surface-400">Kelly Optimal Size</span>
                <span class="font-bold text-primary-400">{{ rt.kelly_pct?.toFixed(1) }}% of capital</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-xs text-surface-400">Half-Kelly (conservative)</span>
                <span class="font-semibold text-surface-200">{{ ((rt.kelly_pct ?? 0) / 2).toFixed(1) }}% of capital</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Probability Cone Chart ── -->
        <div class="glass p-4">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="text-sm font-semibold text-surface-100">GBM Probability Cone — {{ horizonDays }} Trading Days</h3>
              <p class="text-xs text-surface-400 mt-0.5">95% confidence band · Expected path · OCaml Geometric Brownian Motion</p>
            </div>
          </div>
          <VChart v-if="coneOption" :option="coneOption" autoresize style="height:280px" />
        </div>
      </template>

      <div v-else-if="!loading" class="flex flex-col items-center justify-center h-40 text-surface-500 glass rounded-xl">
        <p class="text-sm">Select a ticker and click Analyse to load real-time probability data</p>
      </div>
    </div>

    <!-- ════════════════ TAB: OPTION PRICER ════════════════ -->
    <div v-if="activeTab === 'option'" class="space-y-4">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Left: inputs -->
        <div class="glass p-4 space-y-4">
          <h3 class="text-sm font-semibold text-surface-200">Black-Scholes / CRR Parameters</h3>
          <div class="grid grid-cols-2 gap-3">
            <div v-for="f in optionFields" :key="f.key" class="space-y-1">
              <label class="text-xs text-surface-400">{{ f.label }}</label>
              <input type="number" v-model.number="optForm[f.key]" :step="f.step" :min="f.min"
                class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-2 py-1.5 outline-none focus:border-primary-500" />
            </div>
            <div class="col-span-2 space-y-1">
              <label class="text-xs text-surface-400">Option Type</label>
              <div class="flex gap-3">
                <label class="flex items-center gap-1.5 cursor-pointer text-sm text-surface-300">
                  <input type="radio" value="call" v-model="optForm.option_type" class="accent-primary-500" /> Call
                </label>
                <label class="flex items-center gap-1.5 cursor-pointer text-sm text-surface-300">
                  <input type="radio" value="put" v-model="optForm.option_type" class="accent-primary-500" /> Put
                </label>
              </div>
            </div>
          </div>
          <button @click="priceOption" :disabled="optLoading" class="btn-primary w-full">
            <svg v-if="optLoading" class="w-4 h-4 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Price Option
          </button>
        </div>

        <!-- Right: results -->
        <div class="lg:col-span-2 space-y-4">
          <template v-if="optResult">
            <!-- Price + Binomial comparison -->
            <div class="grid grid-cols-2 gap-4">
              <div class="glass p-4 text-center">
                <p class="text-xs text-surface-400 uppercase tracking-wider mb-1">Black-Scholes Price</p>
                <p class="text-3xl font-bold text-primary-400">${{ optResult.price?.toFixed(4) }}</p>
                <p class="text-xs text-surface-500 mt-1">Analytical formula</p>
              </div>
              <div class="glass p-4 text-center">
                <p class="text-xs text-surface-400 uppercase tracking-wider mb-1">CRR Binomial (200 steps)</p>
                <p class="text-3xl font-bold text-accent-400">${{ optResult.binomial_price?.toFixed(4) }}</p>
                <p class="text-xs text-surface-500 mt-1">Numerical tree</p>
              </div>
            </div>

            <!-- Greeks -->
            <div class="glass p-4">
              <h4 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Greeks</h4>
              <div class="grid grid-cols-5 gap-3">
                <div v-for="g in greeksList" :key="g.key" class="text-center">
                  <p class="text-xs text-surface-500 mb-1">{{ g.label }}</p>
                  <p class="text-lg font-bold tabular-nums" :class="greekColor(g.key, optResult.greeks[g.key])">
                    {{ optResult.greeks[g.key]?.toFixed(4) }}
                  </p>
                  <p class="text-xs text-surface-600">{{ g.desc }}</p>
                </div>
              </div>
            </div>

            <!-- Greeks visual bars -->
            <div class="glass p-4 space-y-2">
              <h4 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Greeks Visualisation</h4>
              <div v-for="g in greeksList" :key="g.key + '_bar'" class="flex items-center gap-3">
                <span class="text-xs text-surface-400 w-12">{{ g.label }}</span>
                <div class="flex-1 h-3 bg-surface-700 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500"
                    :class="greekBarColor(g.key, optResult.greeks[g.key])"
                    :style="{ width: greekBarWidth(g.key, optResult.greeks[g.key]) + '%' }" />
                </div>
                <span class="text-xs font-mono text-surface-300 w-20 text-right">{{ optResult.greeks[g.key]?.toFixed(4) }}</span>
              </div>
            </div>
          </template>
          <div v-else-if="!optLoading" class="flex items-center justify-center h-48 text-surface-500 glass rounded-xl">
            <p class="text-sm">Set parameters and click Price Option</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ════════════════ TAB: OPTION CHAIN ════════════════ -->
    <div v-if="activeTab === 'chain'" class="space-y-4">
      <div class="flex items-center gap-4 flex-wrap">
        <div class="flex items-center gap-2">
          <label class="text-xs text-surface-400">Spot</label>
          <input type="number" v-model.number="chainForm.spot" class="w-24 bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-2 py-1.5 outline-none focus:border-primary-500" />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs text-surface-400">Vol</label>
          <input type="number" v-model.number="chainForm.volatility" step="0.01" class="w-20 bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-2 py-1.5 outline-none focus:border-primary-500" />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs text-surface-400">Expiry (years)</label>
          <input type="number" v-model.number="chainForm.time_to_expiry" step="0.01" class="w-24 bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-2 py-1.5 outline-none focus:border-primary-500" />
        </div>
        <button @click="buildChain" :disabled="chainLoading" class="btn-primary">
          Build Chain
        </button>
      </div>

      <div v-if="chainData.length" class="overflow-x-auto rounded-lg border border-surface-700/50">
        <table class="w-full text-xs">
          <thead>
            <tr class="bg-surface-800/50">
              <th class="px-3 py-2 text-left text-surface-400">Strike</th>
              <th class="px-3 py-2 text-right text-bull">Call Price</th>
              <th class="px-3 py-2 text-right text-bull">Call Δ</th>
              <th class="px-3 py-2 text-right text-surface-400">Gamma</th>
              <th class="px-3 py-2 text-right text-surface-400">Theta</th>
              <th class="px-3 py-2 text-right text-surface-400">Vega</th>
              <th class="px-3 py-2 text-right text-bear">Put Price</th>
              <th class="px-3 py-2 text-right text-bear">Put Δ</th>
              <th class="px-3 py-2 text-right text-surface-400">Moneyness</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in chainData" :key="row.strike"
              class="border-t border-surface-700/30 transition-colors"
              :class="Math.abs(row.moneyness - 1) < 0.005
                ? 'bg-primary-600/10 font-semibold'
                : 'hover:bg-surface-700/20'">
              <td class="px-3 py-2 font-mono font-bold"
                :class="Math.abs(row.moneyness - 1) < 0.005 ? 'text-primary-300' : 'text-surface-200'">
                ${{ row.strike }}
              </td>
              <td class="px-3 py-2 text-right tabular-nums text-bull">${{ row.call_price }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-bull">{{ row.call_delta }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-surface-300">{{ row.gamma }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-surface-300">{{ row.call_theta }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-surface-300">{{ row.vega }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-bear">${{ row.put_price }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-bear">{{ row.put_delta }}</td>
              <td class="px-3 py-2 text-right tabular-nums text-surface-400">{{ row.moneyness }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="!chainLoading" class="flex items-center justify-center h-32 text-surface-500 glass rounded-xl">
        <p class="text-sm">Set parameters and click Build Chain</p>
      </div>
    </div>

    <!-- ════════════════ TAB: BOND ════════════════ -->
    <div v-if="activeTab === 'bond'" class="space-y-4">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div class="glass p-4 space-y-4">
          <h3 class="text-sm font-semibold text-surface-200">Bond Parameters</h3>
          <div class="grid grid-cols-2 gap-3">
            <div v-for="f in bondFields" :key="f.key" class="space-y-1">
              <label class="text-xs text-surface-400">{{ f.label }}</label>
              <input type="number" v-model.number="bondForm[f.key]" :step="f.step"
                class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-2 py-1.5 outline-none focus:border-primary-500" />
            </div>
          </div>
          <button @click="priceBond" :disabled="bondLoading" class="btn-primary w-full">Price Bond</button>
        </div>

        <div v-if="bondResult" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="glass p-4 text-center">
              <p class="text-xs text-surface-400 uppercase tracking-wider mb-1">Bond Price</p>
              <p class="text-3xl font-bold" :class="bondResult.price > bondForm.face_value ? 'text-bull' : 'text-bear'">
                ${{ bondResult.price?.toFixed(2) }}
              </p>
              <p class="text-xs text-surface-500 mt-1">vs Face ${{ bondForm.face_value }}</p>
            </div>
            <div class="glass p-4 text-center">
              <p class="text-xs text-surface-400 uppercase tracking-wider mb-1">YTM</p>
              <p class="text-3xl font-bold text-primary-400">{{ bondResult.ytm_pct?.toFixed(2) }}%</p>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-3">
            <div class="glass p-3 text-center">
              <p class="text-xs text-surface-400 mb-1">Mod. Duration</p>
              <p class="text-xl font-bold text-surface-200">{{ bondResult.duration?.toFixed(4) }}</p>
              <p class="text-xs text-surface-500">years</p>
            </div>
            <div class="glass p-3 text-center">
              <p class="text-xs text-surface-400 mb-1">Convexity</p>
              <p class="text-xl font-bold text-surface-200">{{ bondResult.convexity?.toFixed(4) }}</p>
            </div>
            <div class="glass p-3 text-center">
              <p class="text-xs text-surface-400 mb-1">DV01</p>
              <p class="text-xl font-bold text-bear">{{ bondResult.dv01?.toFixed(4) }}</p>
              <p class="text-xs text-surface-500">per bp</p>
            </div>
          </div>
          <!-- Price sensitivity chart -->
          <div class="glass p-4">
            <h4 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Price Sensitivity to Yield</h4>
            <VChart v-if="bondSensOption" :option="bondSensOption" autoresize style="height:220px" />
          </div>
        </div>
        <div v-else-if="!bondLoading" class="flex items-center justify-center h-48 text-surface-500 glass rounded-xl">
          <p class="text-sm">Set parameters and click Price Bond</p>
        </div>
      </div>
    </div>

    <!-- ════════════════ TAB: RISK ════════════════ -->
    <div v-if="activeTab === 'risk'" class="space-y-4">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div class="glass p-4 space-y-4">
          <h3 class="text-sm font-semibold text-surface-200">Risk Parameters</h3>
          <div class="space-y-3">
            <div v-for="f in riskFields" :key="f.key" class="space-y-1">
              <div class="flex justify-between text-xs">
                <span class="text-surface-400">{{ f.label }}</span>
                <span class="text-surface-200 font-medium">{{ riskForm[f.key] }}</span>
              </div>
              <input type="range" v-model.number="riskForm[f.key]" :min="f.min" :max="f.max" :step="f.step" class="w-full accent-primary-500" />
            </div>
          </div>
          <button @click="computeRisk" :disabled="riskLoading" class="btn-primary w-full">Compute Risk</button>
        </div>

        <div v-if="riskResult" class="lg:col-span-2 grid grid-cols-2 gap-4">
          <div class="glass p-4 text-center border-l-4 border-bear">
            <p class="text-xs text-surface-400 uppercase tracking-wider mb-1">VaR 1-Day 95%</p>
            <p class="text-3xl font-bold text-bear">{{ (riskResult.var_1day * 100).toFixed(3) }}%</p>
            <p class="text-xs text-surface-500 mt-1">Maximum expected loss (95% confidence)</p>
          </div>
          <div class="glass p-4 text-center border-l-4 border-red-800">
            <p class="text-xs text-surface-400 uppercase tracking-wider mb-1">CVaR / ES 1-Day</p>
            <p class="text-3xl font-bold text-red-400">{{ (riskResult.cvar_1day * 100).toFixed(3) }}%</p>
            <p class="text-xs text-surface-500 mt-1">Expected loss beyond VaR</p>
          </div>
          <div class="glass p-4 text-center border-l-4 border-primary-500">
            <p class="text-xs text-surface-400 uppercase tracking-wider mb-1">Kelly Criterion</p>
            <p class="text-3xl font-bold text-primary-400">{{ riskResult.kelly_pct?.toFixed(2) }}%</p>
            <p class="text-xs text-surface-500 mt-1">Optimal position size</p>
          </div>
          <div class="glass p-4 text-center border-l-4 border-bull">
            <p class="text-xs text-surface-400 uppercase tracking-wider mb-1">Sharpe Ratio</p>
            <p class="text-3xl font-bold" :class="riskResult.sharpe >= 1 ? 'text-bull' : riskResult.sharpe >= 0 ? 'text-side' : 'text-bear'">
              {{ riskResult.sharpe?.toFixed(4) }}
            </p>
            <p class="text-xs text-surface-500 mt-1">Annualised (OCaml formula)</p>
          </div>
        </div>
        <div v-else-if="!riskLoading" class="lg:col-span-2 flex items-center justify-center h-48 text-surface-500 glass rounded-xl">
          <p class="text-sm">Set parameters and click Compute Risk</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import dayjs from 'dayjs'
import TickerSearch from '@/components/shared/TickerSearch.vue'
import { daytradeApi } from '@/api/daytradeApi'
import { useMarketStore } from '@/stores/marketStore'
import {
  BASE_TOOLTIP, BASE_GRID, BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE, CHART_COLORS,
} from '@/components/charts/chartTheme'

const marketStore = useMarketStore()

// ── Global state ──────────────────────────────────────────────────────────────
const ticker      = ref('SPY')
const horizonDays = ref(5)
const loading     = ref(false)
const rt          = ref<Record<string, any> | null>(null)
const engineLabel = ref('Python/OCaml port')

const activeTab = ref<'realtime' | 'option' | 'chain' | 'bond' | 'risk'>('realtime')
const tabs = [
  { key: 'realtime' as const, label: '⚡ Realtime Analysis' },
  { key: 'option'   as const, label: '📈 Option Pricer' },
  { key: 'chain'    as const, label: '🔗 Option Chain' },
  { key: 'bond'     as const, label: '🏦 Bond Pricer' },
  { key: 'risk'     as const, label: '⚠️ Risk Metrics' },
]

// ── Probability Cone chart ─────────────────────────────────────────────────────
const coneOption = ref<Record<string, unknown> | null>(null)

function buildConeChart(cone: any) {
  if (!cone?.daily?.length) return
  const days   = cone.daily.map((d: any) => `Day ${d.day}`)
  const upper  = cone.daily.map((d: any) => d.upper)
  const lower  = cone.daily.map((d: any) => d.lower)
  const mid    = cone.daily.map((d: any) => d.expected)
  coneOption.value = {
    tooltip:  { ...BASE_TOOLTIP },
    legend:   { data: ['Upper 95%', 'Expected', 'Lower 95%'], bottom: 0, textStyle: { color: '#94a3b8', fontSize: 11 } },
    grid:     { ...BASE_GRID, bottom: '18%' },
    xAxis:    { ...BASE_XAXIS, data: days, axisLabel: { color: '#64748b', fontSize: 10 } },
    yAxis:    { ...BASE_YAXIS, scale: true, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `$${v.toFixed(0)}` } },
    dataZoom: BASE_DATAZONE,
    series: [
      {
        name: 'Upper 95%', type: 'line', data: upper, symbol: 'none',
        lineStyle: { color: '#22c55e', width: 1.5, type: 'dashed' },
        areaStyle: { color: 'rgba(34,197,94,0.08)' },
      },
      {
        name: 'Expected', type: 'line', data: mid, symbol: 'none',
        lineStyle: { color: '#f1f5f9', width: 2.5 },
      },
      {
        name: 'Lower 95%', type: 'line', data: lower, symbol: 'none',
        lineStyle: { color: '#ef4444', width: 1.5, type: 'dashed' },
        areaStyle: { color: 'rgba(239,68,68,0.08)' },
      },
    ],
  }
}

// ── Realtime tab ──────────────────────────────────────────────────────────────
async function runRealtime() {
  loading.value = true
  rt.value = null
  try {
    const res = await daytradeApi.realtime(ticker.value, horizonDays.value)
    rt.value = res.data
    engineLabel.value = res.data.engine ?? 'python_ocaml_port'
    buildConeChart(res.data.cone)
  } finally {
    loading.value = false
  }
}

// ── Option Pricer tab ─────────────────────────────────────────────────────────
const optLoading = ref(false)
const optResult  = ref<Record<string, any> | null>(null)
const optForm    = ref({
  spot: 100, strike: 100, volatility: 0.25,
  time_to_expiry: 0.0833, risk_free: 0.05, option_type: 'call' as 'call' | 'put',
})
const optionFields = [
  { key: 'spot',           label: 'Spot Price',     step: 0.5,   min: 0.01 },
  { key: 'strike',         label: 'Strike',         step: 0.5,   min: 0.01 },
  { key: 'volatility',     label: 'Volatility (σ)', step: 0.01,  min: 0.01 },
  { key: 'time_to_expiry', label: 'Time (years)',   step: 0.001, min: 0.001 },
  { key: 'risk_free',      label: 'Risk-Free Rate', step: 0.001, min: 0 },
]
const greeksList = [
  { key: 'delta', label: 'Δ Delta',  desc: 'price sensitivity' },
  { key: 'gamma', label: 'Γ Gamma',  desc: 'delta change rate' },
  { key: 'theta', label: 'Θ Theta',  desc: 'time decay/day' },
  { key: 'vega',  label: 'ν Vega',   desc: 'per 1% vol change' },
  { key: 'rho',   label: 'ρ Rho',    desc: 'per 1% rate change' },
]

function greekColor(key: string, val: number | undefined) {
  if (val === undefined || val === null) return 'text-surface-400'
  if (key === 'theta') return val < 0 ? 'text-bear' : 'text-bull'
  if (key === 'delta') return val > 0 ? 'text-bull' : 'text-bear'
  return 'text-primary-300'
}
function greekBarWidth(key: string, val: number | undefined) {
  if (val === undefined || val === null) return 0
  const ranges: Record<string, number> = { delta: 1, gamma: 0.05, theta: 0.1, vega: 0.5, rho: 0.5 }
  return Math.min(100, Math.abs(val) / (ranges[key] ?? 1) * 100)
}
function greekBarColor(key: string, val: number | undefined) {
  if (val === undefined || val === null) return 'bg-surface-600'
  if (key === 'theta') return 'bg-bear'
  if (key === 'gamma') return 'bg-side'
  if (val >= 0) return 'bg-primary-500'
  return 'bg-bear'
}

async function priceOption() {
  optLoading.value = true
  try {
    const res = await daytradeApi.option(optForm.value)
    optResult.value = res.data
  } finally {
    optLoading.value = false
  }
}

// ── Option Chain tab ──────────────────────────────────────────────────────────
const chainLoading = ref(false)
const chainData    = ref<Record<string, any>[]>([])
const chainForm    = ref({ spot: 100, volatility: 0.25, time_to_expiry: 0.0833 })

async function buildChain() {
  chainLoading.value = true
  try {
    const res = await daytradeApi.chain(chainForm.value)
    chainData.value = (res.data.chain ?? []) as Record<string, any>[]
  } finally {
    chainLoading.value = false
  }
}

// ── Bond tab ──────────────────────────────────────────────────────────────────
const bondLoading    = ref(false)
const bondResult     = ref<Record<string, any> | null>(null)
const bondSensOption = ref<Record<string, unknown> | null>(null)
const bondForm       = ref({ face_value: 1000, coupon_rate: 0.05, ytm: 0.04, frequency: 2, periods: 20 })
const bondFields = [
  { key: 'face_value',  label: 'Face Value',    step: 100 },
  { key: 'coupon_rate', label: 'Coupon Rate',   step: 0.005 },
  { key: 'ytm',         label: 'YTM',           step: 0.005 },
  { key: 'frequency',   label: 'Freq/Year',     step: 1 },
  { key: 'periods',     label: 'Total Periods', step: 1 },
]

async function priceBond() {
  bondLoading.value = true
  try {
    const res = await daytradeApi.bond(bondForm.value)
    bondResult.value = res.data
    // Build yield sensitivity curve: price vs YTM ±300bp
    const ytmBase = bondForm.value.ytm
    const sensData: [number, number][] = []
    for (let bps = -300; bps <= 300; bps += 25) {
      const y = ytmBase + bps / 10000
      if (y <= 0) continue
      // Re-price client-side using simplified formula
      const f = bondForm.value.face_value
      const c = f * bondForm.value.coupon_rate / bondForm.value.frequency
      const r = y / bondForm.value.frequency
      const n = bondForm.value.periods
      let p = 0
      for (let t = 1; t <= n; t++) p += c / (1 + r) ** t
      p += f / (1 + r) ** n
      sensData.push([+(ytmBase * 100 + bps / 100).toFixed(2), +p.toFixed(2)])
    }
    bondSensOption.value = {
      tooltip: { ...BASE_TOOLTIP, formatter: (p: any) => `YTM ${p.data[0]}%: $${p.data[1].toFixed(2)}` },
      grid:    { ...BASE_GRID },
      xAxis:   { ...BASE_XAXIS, type: 'value', name: 'YTM (%)', axisLabel: { color: '#64748b', formatter: '{value}%' } },
      yAxis:   { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `$${v.toFixed(0)}` } },
      series: [{
        type: 'line', data: sensData, symbol: 'none', smooth: true,
        lineStyle: { color: '#3b82f6', width: 2 },
        areaStyle: { color: 'rgba(59,130,246,0.1)' },
        markLine: {
          silent: true,
          lineStyle: { color: '#f59e0b', type: 'dashed' },
          data: [{ xAxis: +(ytmBase * 100).toFixed(2), label: { formatter: 'Current YTM', color: '#f59e0b' } }],
        },
      }],
    }
  } finally {
    bondLoading.value = false
  }
}

// ── Risk tab ──────────────────────────────────────────────────────────────────
const riskLoading = ref(false)
const riskResult  = ref<Record<string, any> | null>(null)
const riskForm    = ref({ daily_sigma: 0.015, daily_mu: 0.0003, confidence: 0.95, win_probability: 0.55, win_loss_ratio: 1.5 })
const riskFields = [
  { key: 'daily_sigma',      label: 'Daily Std Dev (σ)',  min: 0.001, max: 0.1,   step: 0.001 },
  { key: 'daily_mu',         label: 'Daily Expected Ret', min: -0.01, max: 0.01,  step: 0.0001 },
  { key: 'confidence',       label: 'VaR Confidence',     min: 0.80,  max: 0.999, step: 0.005 },
  { key: 'win_probability',  label: 'Win Rate',           min: 0.1,   max: 0.9,   step: 0.01 },
  { key: 'win_loss_ratio',   label: 'Win/Loss Ratio',     min: 0.1,   max: 5.0,   step: 0.1 },
]

async function computeRisk() {
  riskLoading.value = true
  try {
    const res = await daytradeApi.risk(riskForm.value)
    riskResult.value = res.data
  } finally {
    riskLoading.value = false
  }
}

onMounted(() => {
  if (!marketStore.availableTickers.length) marketStore.loadAvailable()
  runRealtime()
})
</script>
