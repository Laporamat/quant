<template>
  <div class="space-y-5 animate-fade-in">

    <!-- ── Header ──────────────────────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row sm:items-start gap-3">
      <div class="flex-1">
        <h1 class="text-xl font-bold text-surface-100">
          Statistical Edge Trading
        </h1>
        <p class="text-sm text-surface-400 mt-0.5">
          กำไรน้อยแต่ต่อเนื่อง · ขาดทุนน้อยที่สุด ·
          ใช้ข้อมูลอดีต 20 ปีคำนวณ probability จริง
        </p>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <div class="w-36"><TickerSearch :model-value="[ticker]" @update:model-value="v => { ticker = v[0] ?? 'SPY' }" :multi="false" /></div>
        <select v-model.number="capital" class="bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-2 py-2 outline-none focus:border-primary-500">
          <option :value="10000">$10K</option>
          <option :value="50000">$50K</option>
          <option :value="100000">$100K</option>
          <option :value="500000">$500K</option>
          <option :value="1000000">$1M</option>
        </select>
        <select v-model.number="holdingDays" class="bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-2 py-2 outline-none focus:border-primary-500">
          <option :value="1">Hold 1d</option>
          <option :value="3">Hold 3d</option>
          <option :value="5">Hold 5d</option>
          <option :value="10">Hold 10d</option>
        </select>
        <button @click="loadAll" :disabled="loading" class="btn-primary flex items-center gap-2">
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          Analyse
        </button>
        <button @click="runScan" :disabled="scanLoading" class="btn-ghost border border-surface-700 text-sm px-3 py-2 flex items-center gap-1.5">
          <svg v-if="scanLoading" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          Scan All
        </button>
      </div>
    </div>

    <!-- ── Tabs ─────────────────────────────────────────────────────────────── -->
    <div class="flex border-b border-surface-700/50 gap-1">
      <button v-for="t in tabs" :key="t.key" @click="activeTab = t.key"
        class="tab-item" :class="{ active: activeTab === t.key }">{{ t.label }}</button>
    </div>

    <!-- ══════════════ TAB: SETUP ══════════════ -->
    <div v-if="activeTab === 'setup'" class="space-y-4">

      <!-- Loading -->
      <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div v-for="i in 8" :key="i" class="glass h-20 animate-skeleton rounded-xl" />
      </div>

      <template v-if="setup && !loading">

        <!-- ── Signal strip ─────────────────────────────────────────────── -->
        <div class="glass p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <!-- Signal badge -->
          <div class="flex items-center gap-3">
            <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-black"
              :class="{
                'bg-bull/20 text-bull':   setup.signals.mean_reversion.direction === 'LONG',
                'bg-bear/20 text-bear':   setup.signals.mean_reversion.direction === 'SHORT',
                'bg-surface-700 text-surface-400': setup.signals.mean_reversion.direction === 'NEUTRAL',
              }">
              {{ setup.signals.mean_reversion.direction === 'LONG' ? '↑' : setup.signals.mean_reversion.direction === 'SHORT' ? '↓' : '–' }}
            </div>
            <div>
              <p class="text-xs text-surface-400 uppercase tracking-wider">Signal</p>
              <p class="text-lg font-bold" :class="setup.signals.mean_reversion.direction === 'LONG' ? 'text-bull' : setup.signals.mean_reversion.direction === 'SHORT' ? 'text-bear' : 'text-surface-400'">
                {{ setup.signals.mean_reversion.direction }}
              </p>
            </div>
          </div>
          <!-- Sub-signals -->
          <div class="flex gap-4 flex-wrap text-sm">
            <div>
              <span class="text-xs text-surface-500">Mean Rev</span>
              <span class="ml-1 font-semibold"
                :class="setup.signals.mean_reversion.direction === 'LONG' ? 'text-bull' : setup.signals.mean_reversion.direction === 'SHORT' ? 'text-bear' : 'text-surface-400'">
                {{ setup.signals.mean_reversion.direction }}
              </span>
            </div>
            <div>
              <span class="text-xs text-surface-500">Momentum</span>
              <span class="ml-1 font-semibold"
                :class="setup.signals.momentum.direction === 'LONG' ? 'text-bull' : setup.signals.momentum.direction === 'SHORT' ? 'text-bear' : 'text-surface-400'">
                {{ setup.signals.momentum.direction }}
              </span>
            </div>
            <div>
              <span class="text-xs text-surface-500">RSI</span>
              <span class="ml-1 font-mono font-semibold"
                :class="setup.signals.mean_reversion.rsi < 35 ? 'text-bull' : setup.signals.mean_reversion.rsi > 65 ? 'text-bear' : 'text-surface-200'">
                {{ setup.signals.mean_reversion.rsi?.toFixed(1) }}
              </span>
            </div>
            <div>
              <span class="text-xs text-surface-500">Z-Score</span>
              <span class="ml-1 font-mono font-semibold"
                :class="setup.signals.mean_reversion.z_score < -1.5 ? 'text-bull' : setup.signals.mean_reversion.z_score > 1.5 ? 'text-bear' : 'text-surface-200'">
                {{ setup.signals.mean_reversion.z_score?.toFixed(2) }}
              </span>
            </div>
            <div>
              <span class="text-xs text-surface-500">Regime</span>
              <span class="ml-1 font-semibold" :class="setup.regime === 'bull' ? 'text-bull' : 'text-bear'">
                {{ setup.regime }} ({{ (setup.regime_prob * 100).toFixed(0) }}%)
              </span>
            </div>
          </div>
          <!-- Edge score gauge -->
          <div class="ml-auto flex flex-col items-center gap-1">
            <span class="text-xs text-surface-400 uppercase tracking-wider">Edge Score</span>
            <div class="relative w-16 h-16">
              <svg viewBox="0 0 36 36" class="w-16 h-16 -rotate-90">
                <circle cx="18" cy="18" r="15" fill="none" stroke="#1e293b" stroke-width="3"/>
                <circle cx="18" cy="18" r="15" fill="none"
                  :stroke="edgeScoreColor" stroke-width="3"
                  :stroke-dasharray="`${(signalData?.edge_score ?? 0) * 0.942} 94.2`"
                  stroke-linecap="round" class="transition-all duration-700"/>
              </svg>
              <div class="absolute inset-0 flex items-center justify-center rotate-90">
                <span class="text-sm font-bold" :class="edgeScoreColor.replace('#','text-[#') + ']'">
                  {{ signalData?.edge_score?.toFixed(0) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Trade Setup Card ──────────────────────────────────────────── -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">

          <!-- Entry / SL / TP -->
          <div class="glass p-4 space-y-3">
            <h3 class="text-sm font-semibold text-surface-200">Trade Setup</h3>
            <div class="space-y-2">
              <div class="flex justify-between items-center py-2 border-b border-surface-700/30">
                <span class="text-xs text-surface-400">Entry</span>
                <span class="font-mono font-bold text-surface-100">${{ setup.entry?.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between items-center py-2 border-b border-surface-700/30">
                <span class="text-xs text-surface-400">Stop-Loss (2×VaR)</span>
                <span class="font-mono font-bold text-bear">${{ setup.stop_price?.toFixed(2) }}
                  <span class="text-xs ml-1">({{ setup.stop_pct?.toFixed(2) }}%)</span>
                </span>
              </div>
              <div class="flex justify-between items-center py-2 border-b border-surface-700/30">
                <span class="text-xs text-surface-400">Take-Profit 1 (1.5R)</span>
                <span class="font-mono font-bold text-bull">${{ setup.tp1_price?.toFixed(2) }}
                  <span class="text-xs ml-1">(+{{ setup.tp1_pct?.toFixed(2) }}%)</span>
                </span>
              </div>
              <div class="flex justify-between items-center py-2">
                <span class="text-xs text-surface-400">Take-Profit 2 (2.5R)</span>
                <span class="font-mono font-bold text-bull">${{ setup.tp2_price?.toFixed(2) }}
                  <span class="text-xs ml-1">(+{{ setup.tp2_pct?.toFixed(2) }}%)</span>
                </span>
              </div>
            </div>
          </div>

          <!-- Position Sizing -->
          <div class="glass p-4 space-y-3">
            <h3 class="text-sm font-semibold text-surface-200">Position Sizing</h3>
            <div class="space-y-2">
              <div class="flex justify-between py-1.5 border-b border-surface-700/30">
                <span class="text-xs text-surface-400">Capital</span>
                <span class="font-mono font-semibold text-surface-200">${{ capital.toLocaleString() }}</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-surface-700/30">
                <span class="text-xs text-surface-400">Kelly Criterion</span>
                <span class="font-mono text-primary-400">{{ setup.kelly_pct?.toFixed(1) }}%</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-surface-700/30">
                <span class="text-xs text-surface-400">Half-Kelly (safe)</span>
                <span class="font-mono font-bold text-primary-300">{{ setup.half_kelly_pct?.toFixed(1) }}%</span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-surface-700/30">
                <span class="text-xs text-surface-400">Position Size</span>
                <span class="font-mono font-bold text-surface-100">{{ setup.position_size_pct?.toFixed(1) }}%
                  <span class="text-xs text-surface-400 ml-1">({{ setup.position_value ? '$' + setup.position_value.toFixed(0) : '—' }})</span>
                </span>
              </div>
              <div class="flex justify-between py-1.5 border-b border-surface-700/30">
                <span class="text-xs text-surface-400">Shares</span>
                <span class="font-mono text-surface-200">{{ setup.shares?.toLocaleString() }}</span>
              </div>
              <div class="flex justify-between py-1.5">
                <span class="text-xs text-surface-400">Max Loss</span>
                <span class="font-mono font-bold text-bear">${{ setup.max_loss_dollar?.toFixed(0) }}
                  <span class="text-xs ml-1">({{ setup.max_loss_cap_pct?.toFixed(2) }}% of capital)</span>
                </span>
              </div>
            </div>
          </div>

          <!-- Probability Outcomes -->
          <div class="glass p-4 space-y-3">
            <h3 class="text-sm font-semibold text-surface-200">Outcome Probabilities ({{ holdingDays }}d)</h3>
            <div class="space-y-3">
              <!-- P(TP1) -->
              <div>
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-bull">Hit TP1 (+{{ setup.tp1_pct?.toFixed(2) }}%)</span>
                  <span class="font-semibold text-bull">{{ (setup.p_tp1 * 100).toFixed(1) }}%</span>
                </div>
                <div class="h-2 bg-surface-700 rounded-full overflow-hidden">
                  <div class="h-full bg-bull rounded-full transition-all duration-700"
                    :style="{ width: (setup.p_tp1 * 100).toFixed(1) + '%' }" />
                </div>
              </div>
              <!-- P(TP2) -->
              <div>
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-bull/70">Hit TP2 (+{{ setup.tp2_pct?.toFixed(2) }}%)</span>
                  <span class="font-semibold text-bull/70">{{ (setup.p_tp2 * 100).toFixed(1) }}%</span>
                </div>
                <div class="h-2 bg-surface-700 rounded-full overflow-hidden">
                  <div class="h-full bg-bull/50 rounded-full transition-all duration-700"
                    :style="{ width: (setup.p_tp2 * 100).toFixed(1) + '%' }" />
                </div>
              </div>
              <!-- P(Neutral) -->
              <div>
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-surface-400">No clear move</span>
                  <span class="font-semibold text-surface-400">{{ (setup.p_neutral * 100).toFixed(1) }}%</span>
                </div>
                <div class="h-2 bg-surface-700 rounded-full overflow-hidden">
                  <div class="h-full bg-surface-500 rounded-full transition-all duration-700"
                    :style="{ width: (setup.p_neutral * 100).toFixed(1) + '%' }" />
                </div>
              </div>
              <!-- P(Stop) -->
              <div>
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-bear">Hit Stop ({{ setup.stop_pct?.toFixed(2) }}%)</span>
                  <span class="font-semibold text-bear">{{ (setup.p_stop * 100).toFixed(1) }}%</span>
                </div>
                <div class="h-2 bg-surface-700 rounded-full overflow-hidden">
                  <div class="h-full bg-bear rounded-full transition-all duration-700"
                    :style="{ width: (setup.p_stop * 100).toFixed(1) + '%' }" />
                </div>
              </div>
            </div>
            <!-- Expected Value -->
            <div class="pt-2 border-t border-surface-700/30">
              <div class="flex justify-between">
                <span class="text-xs text-surface-400">Expected Value</span>
                <span class="font-bold tabular-nums"
                  :class="(setup.ev_trade_pct ?? 0) >= 0 ? 'text-bull' : 'text-bear'">
                  {{ setup.ev_trade_pct >= 0 ? '+' : '' }}{{ setup.ev_trade_pct?.toFixed(3) }}%
                  <span class="text-xs text-surface-400 ml-1">(${{ setup.ev_dollar?.toFixed(0) }})</span>
                </span>
              </div>
              <div class="flex justify-between mt-1">
                <span class="text-xs text-surface-400">Historical Win Rate</span>
                <span class="font-semibold" :class="(setup.win_rate ?? 0) > 0.5 ? 'text-bull' : 'text-bear'">
                  {{ ((setup.win_rate ?? 0) * 100).toFixed(1) }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Probability Cone Chart ─────────────────────────────────────── -->
        <div class="glass p-4">
          <h3 class="text-sm font-semibold text-surface-100 mb-1">
            Probability Cone — {{ holdingDays }} Trading Days
            <span class="text-xs text-surface-500 ml-2 font-normal">OCaml GBM engine · 95% confidence</span>
          </h3>
          <VChart v-if="coneOption" :option="coneOption" autoresize style="height:260px" />
        </div>

        <!-- ── Risk metrics ───────────────────────────────────────────────── -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">VaR 1D 95%</span>
            <div class="text-xl font-bold text-bear mt-1">{{ setup.var_1day_pct?.toFixed(3) }}%</div>
          </div>
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">Sharpe</span>
            <div class="text-xl font-bold mt-1" :class="(setup.sharpe ?? 0) >= 1 ? 'text-bull' : (setup.sharpe ?? 0) >= 0 ? 'text-side' : 'text-bear'">
              {{ setup.sharpe?.toFixed(3) }}
            </div>
          </div>
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">W/L Ratio</span>
            <div class="text-xl font-bold mt-1" :class="(setup.wl_ratio ?? 0) >= 1.5 ? 'text-bull' : 'text-side'">{{ setup.wl_ratio?.toFixed(2) }}</div>
          </div>
          <div class="metric-card">
            <span class="text-xs text-surface-400 uppercase tracking-wider">Ann. Vol</span>
            <div class="text-xl font-bold text-side mt-1">{{ setup.ann_volatility ?? signalData?.ann_volatility }}%</div>
          </div>
        </div>

      </template>
      <div v-else-if="!loading" class="flex flex-col items-center justify-center h-52 text-surface-500 glass rounded-xl">
        <p class="text-sm">Select a ticker and click Analyse</p>
      </div>
    </div>

    <!-- ══════════════ TAB: SCAN ══════════════ -->
    <div v-if="activeTab === 'scan'" class="space-y-4">
      <!-- Scan controls -->
      <div class="glass p-4 flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-2">
          <label class="text-xs text-surface-400">Min Edge Score</label>
          <input type="range" v-model.number="scanMinEdge" min="20" max="80" step="5" class="w-28 accent-primary-500" />
          <span class="text-xs text-surface-200 w-8">{{ scanMinEdge }}</span>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs text-surface-400">Max VaR 1D</label>
          <input type="range" v-model.number="scanMaxVar" min="0.5" max="5" step="0.5" class="w-28 accent-primary-500" />
          <span class="text-xs text-surface-200 w-10">{{ scanMaxVar }}%</span>
        </div>
        <span class="text-xs text-surface-500">Scanning {{ scanTickers.length }} tickers…</span>
        <button @click="runScan" :disabled="scanLoading" class="btn-primary ml-auto">
          <svg v-if="scanLoading" class="w-4 h-4 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          Scan
        </button>
      </div>

      <!-- Scan results -->
      <div v-if="scanResults.length" class="overflow-x-auto rounded-xl border border-surface-700/50">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-surface-800/60">
              <th class="px-3 py-2.5 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider">Ticker</th>
              <th class="px-3 py-2.5 text-center text-xs font-semibold text-surface-400">Signal</th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold text-surface-400">Edge Score</th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold text-surface-400">Win Rate</th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold text-surface-400">EV%</th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold text-surface-400">Half-Kelly</th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold text-surface-400">VaR 1D</th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold text-surface-400">Sharpe</th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold text-surface-400">RSI</th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold text-surface-400">Z-Score</th>
              <th class="px-3 py-2.5 text-center text-xs font-semibold text-surface-400">Regime</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in scanResults" :key="row.ticker"
              @click="selectFromScan(row.ticker)"
              class="border-t border-surface-700/30 hover:bg-primary-600/10 cursor-pointer transition-colors">
              <td class="px-3 py-2.5">
                <TickerBadge :ticker="row.ticker" />
              </td>
              <td class="px-3 py-2.5 text-center">
                <span class="px-2 py-0.5 rounded text-xs font-bold uppercase"
                  :class="row.signal === 'LONG' ? 'bg-bull/15 text-bull' : row.signal === 'SHORT' ? 'bg-bear/15 text-bear' : 'bg-surface-700 text-surface-400'">
                  {{ row.signal }}
                </span>
              </td>
              <td class="px-3 py-2.5 text-right">
                <div class="flex items-center justify-end gap-1.5">
                  <div class="w-16 h-1.5 bg-surface-700 rounded-full overflow-hidden">
                    <div class="h-full rounded-full" :class="edgeBarClass(row.edge_score)"
                      :style="{ width: row.edge_score + '%' }" />
                  </div>
                  <span class="font-bold tabular-nums text-xs" :class="edgeTextClass(row.edge_score)">
                    {{ row.edge_score.toFixed(1) }}
                  </span>
                </div>
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="row.win_rate > 0.55 ? 'text-bull' : 'text-surface-300'">
                {{ (row.win_rate * 100).toFixed(1) }}%
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="row.expected_value > 0 ? 'text-bull' : 'text-bear'">
                {{ row.expected_value > 0 ? '+' : '' }}{{ row.expected_value?.toFixed(3) }}%
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums text-primary-400 font-semibold">
                {{ row.half_kelly?.toFixed(1) }}%
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="row.var_1day_pct < 1.5 ? 'text-bull' : 'text-side'">
                {{ row.var_1day_pct?.toFixed(2) }}%
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="row.sharpe >= 1 ? 'text-bull' : row.sharpe >= 0 ? 'text-surface-300' : 'text-bear'">
                {{ row.sharpe?.toFixed(2) }}
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="row.rsi < 35 ? 'text-bull' : row.rsi > 65 ? 'text-bear' : 'text-surface-300'">
                {{ row.rsi }}
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="row.z_score < -1.5 ? 'text-bull' : row.z_score > 1.5 ? 'text-bear' : 'text-surface-300'">
                {{ row.z_score?.toFixed(2) }}
              </td>
              <td class="px-3 py-2.5 text-center">
                <span class="text-xs" :class="row.regime === 'bull' ? 'text-bull' : 'text-bear'">{{ row.regime }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="!scanLoading" class="flex flex-col items-center justify-center h-32 text-surface-500 glass rounded-xl">
        <p class="text-sm">Click Scan to find high-edge opportunities across all downloaded tickers</p>
      </div>
    </div>

    <!-- ══════════════ TAB: EDGE STATS ══════════════ -->
    <div v-if="activeTab === 'edge'" class="space-y-4">
      <button @click="loadEdge" :disabled="edgeLoading" class="btn-primary text-sm flex items-center gap-2">
        <svg v-if="edgeLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
        Load 20yr Statistical Edge
      </button>

      <template v-if="edge">
        <!-- By holding period -->
        <div class="glass p-4">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">Win Rate by Holding Period ({{ ticker }})</h3>
          <VChart v-if="holdingPeriodOption" :option="holdingPeriodOption" autoresize style="height:220px" />
        </div>

        <!-- By regime -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="glass p-4">
            <h3 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">Bull Market Edge (5d)</h3>
            <div class="space-y-1.5 text-sm">
              <div class="flex justify-between"><span class="text-surface-400">Win Rate</span><span :class="edge.by_regime.bull_market.win_rate > 0.5 ? 'text-bull' : 'text-bear'">{{ (edge.by_regime.bull_market.win_rate * 100).toFixed(1) }}%</span></div>
              <div class="flex justify-between"><span class="text-surface-400">Avg Win</span><span class="text-bull">+{{ edge.by_regime.bull_market.avg_win?.toFixed(3) }}%</span></div>
              <div class="flex justify-between"><span class="text-surface-400">Avg Loss</span><span class="text-bear">{{ edge.by_regime.bull_market.avg_loss?.toFixed(3) }}%</span></div>
              <div class="flex justify-between"><span class="text-surface-400">Kelly</span><span class="text-primary-400 font-bold">{{ edge.by_regime.bull_market.kelly_pct?.toFixed(1) }}%</span></div>
            </div>
          </div>
          <div class="glass p-4">
            <h3 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">Bear Market Edge (5d)</h3>
            <div class="space-y-1.5 text-sm">
              <div class="flex justify-between"><span class="text-surface-400">Win Rate</span><span :class="edge.by_regime.bear_market.win_rate > 0.5 ? 'text-bull' : 'text-bear'">{{ (edge.by_regime.bear_market.win_rate * 100).toFixed(1) }}%</span></div>
              <div class="flex justify-between"><span class="text-surface-400">Avg Win</span><span class="text-bull">+{{ edge.by_regime.bear_market.avg_win?.toFixed(3) }}%</span></div>
              <div class="flex justify-between"><span class="text-surface-400">Avg Loss</span><span class="text-bear">{{ edge.by_regime.bear_market.avg_loss?.toFixed(3) }}%</span></div>
              <div class="flex justify-between"><span class="text-surface-400">Kelly</span><span class="text-primary-400 font-bold">{{ edge.by_regime.bear_market.kelly_pct?.toFixed(1) }}%</span></div>
            </div>
          </div>
        </div>

        <!-- Z-score entry conditions -->
        <div class="glass p-4">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">Historical Win Rate by Entry Z-Score</h3>
          <div class="flex flex-wrap gap-3">
            <div v-for="(v, k) in edge.entry_by_zscore" :key="k"
              class="glass p-3 text-center min-w-[100px] border"
              :class="(v.win_rate_5d ?? 0) > 0.6 ? 'border-bull/30' : 'border-surface-700/50'">
              <p class="text-xs font-mono font-bold text-primary-400">{{ k }}</p>
              <p class="text-xl font-bold mt-1" :class="(v.win_rate_5d ?? 0) > 0.6 ? 'text-bull' : 'text-surface-200'">
                {{ ((v.win_rate_5d ?? 0) * 100).toFixed(1) }}%
              </p>
              <p class="text-xs text-surface-500">{{ v.n_signals }} signals</p>
            </div>
          </div>
        </div>

        <!-- Day-of-week chart -->
        <div class="glass p-4">
          <h3 class="text-sm font-semibold text-surface-200 mb-3">Day-of-Week Effect</h3>
          <VChart v-if="dowOption" :option="dowOption" autoresize style="height:200px" />
        </div>

        <!-- Drawdown stats -->
        <div class="grid grid-cols-3 gap-3">
          <div class="glass p-3 text-center">
            <p class="text-xs text-surface-400 mb-1">Max Drawdown</p>
            <p class="text-xl font-bold text-bear">{{ edge.drawdown_stats.max_drawdown_pct?.toFixed(1) }}%</p>
          </div>
          <div class="glass p-3 text-center">
            <p class="text-xs text-surface-400 mb-1">Avg Drawdown</p>
            <p class="text-xl font-bold text-side">{{ edge.drawdown_stats.avg_drawdown_pct?.toFixed(1) }}%</p>
          </div>
          <div class="glass p-3 text-center">
            <p class="text-xs text-surface-400 mb-1">Avg Recovery</p>
            <p class="text-xl font-bold text-surface-200">{{ edge.drawdown_stats.avg_recovery_days?.toFixed(0) }} days</p>
          </div>
        </div>
      </template>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import TickerSearch from '@/components/shared/TickerSearch.vue'
import TickerBadge  from '@/components/shared/TickerBadge.vue'
import { tradeApi } from '@/api/tradeApi'
import { useMarketStore } from '@/stores/marketStore'
import { BASE_TOOLTIP, BASE_GRID, BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE } from '@/components/charts/chartTheme'
import { useRouter } from 'vue-router'

const marketStore = useMarketStore()
const router      = useRouter()

// ── Global state ──────────────────────────────────────────────────────────────
const ticker      = ref('SPY')
const capital     = ref(100_000)
const holdingDays = ref(5)
const loading     = ref(false)
const activeTab   = ref<'setup' | 'scan' | 'edge'>('setup')
const tabs = [
  { key: 'setup' as const, label: '🎯 Trade Setup' },
  { key: 'scan'  as const, label: '🔍 Opportunity Scan' },
  { key: 'edge'  as const, label: '📊 Statistical Edge' },
]

// ── Data ───────────────────────────────────────────────────────────────────────
const setup       = ref<Record<string, any> | null>(null)
const signalData  = ref<Record<string, any> | null>(null)
const coneOption  = ref<Record<string, unknown> | null>(null)

const edgeScoreColor = computed(() => {
  const s = signalData.value?.edge_score ?? 0
  return s >= 65 ? '#22c55e' : s >= 45 ? '#f59e0b' : '#ef4444'
})

async function loadAll() {
  loading.value = true
  setup.value   = null
  try {
    const [sigRes, setupRes] = await Promise.all([
      tradeApi.signals(ticker.value, holdingDays.value),
      tradeApi.setup(ticker.value, capital.value, 1.0),
    ])
    signalData.value = sigRes.data
    setup.value      = setupRes.data
    buildConeChart(setupRes.data.cone)
  } finally {
    loading.value = false
  }
}

function buildConeChart(cone: any) {
  if (!cone?.daily?.length) return
  const spot   = setup.value?.entry ?? 100
  const days   = cone.daily.map((d: any) => `Day ${d.day}`)
  const upper  = cone.daily.map((d: any) => d.upper)
  const lower  = cone.daily.map((d: any) => d.lower)
  const mid    = cone.daily.map((d: any) => d.expected)
  const sl     = Array(days.length).fill(setup.value?.stop_price)
  const tp1    = Array(days.length).fill(setup.value?.tp1_price)

  coneOption.value = {
    tooltip: { ...BASE_TOOLTIP },
    legend:  { data: ['Upper 95%', 'Expected', 'Lower 95%', 'Stop-Loss', 'TP1'], bottom: 0, textStyle: { color: '#94a3b8', fontSize: 10 } },
    grid:    { ...BASE_GRID, bottom: '22%' },
    xAxis:   { ...BASE_XAXIS, data: days, axisLabel: { color: '#64748b', fontSize: 10 } },
    yAxis:   { ...BASE_YAXIS, scale: true, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `$${v.toFixed(1)}` } },
    dataZoom: BASE_DATAZONE,
    series: [
      { name: 'Upper 95%', type: 'line', data: upper, symbol: 'none', lineStyle: { color: '#22c55e', width: 1, type: 'dashed' }, areaStyle: { color: 'rgba(34,197,94,0.07)' } },
      { name: 'Expected',  type: 'line', data: mid,   symbol: 'none', lineStyle: { color: '#f1f5f9', width: 2.5 } },
      { name: 'Lower 95%', type: 'line', data: lower, symbol: 'none', lineStyle: { color: '#ef4444', width: 1, type: 'dashed' }, areaStyle: { color: 'rgba(239,68,68,0.07)' } },
      { name: 'Stop-Loss', type: 'line', data: sl,    symbol: 'none', lineStyle: { color: '#ef4444', width: 1.5 } },
      { name: 'TP1',       type: 'line', data: tp1,   symbol: 'none', lineStyle: { color: '#22c55e', width: 1.5 } },
    ],
  }
}

// ── Scan ───────────────────────────────────────────────────────────────────────
const scanLoading  = ref(false)
const scanMinEdge  = ref(45)
const scanMaxVar   = ref(3.0)
const scanResults  = ref<Record<string, any>[]>([])

const scanTickers = computed(() =>
  marketStore.availableTickers
    .map((t) => t.ticker)
    .filter((t) => !['XLK','XLV','XLF','XLE','XLY','XLP','XLI','XLB','XLU','XLRE','XLC'].includes(t))
)

async function runScan() {
  if (!scanTickers.value.length) return
  scanLoading.value = true
  try {
    const res = await tradeApi.scan(scanTickers.value, holdingDays.value, scanMinEdge.value, scanMaxVar.value)
    scanResults.value = res.data.results ?? []
    if (scanResults.value.length) activeTab.value = 'scan'
  } finally {
    scanLoading.value = false
  }
}

function selectFromScan(t: string) {
  ticker.value = t
  activeTab.value = 'setup'
  loadAll()
}

function edgeBarClass(score: number) {
  return score >= 65 ? 'bg-bull' : score >= 45 ? 'bg-side' : 'bg-bear'
}
function edgeTextClass(score: number) {
  return score >= 65 ? 'text-bull' : score >= 45 ? 'text-side' : 'text-bear'
}

// ── Edge stats ─────────────────────────────────────────────────────────────────
const edgeLoading          = ref(false)
const edge                 = ref<Record<string, any> | null>(null)
const holdingPeriodOption  = ref<Record<string, unknown> | null>(null)
const dowOption            = ref<Record<string, unknown> | null>(null)

async function loadEdge() {
  edgeLoading.value = true
  try {
    const res = await tradeApi.edge(ticker.value)
    edge.value = res.data
    buildEdgeCharts(res.data)
  } finally {
    edgeLoading.value = false
  }
}

function buildEdgeCharts(d: any) {
  // By holding period
  const periods = Object.keys(d.by_holding_period)
  const winRates = periods.map((p) => +(d.by_holding_period[p].win_rate * 100).toFixed(2))
  const evs      = periods.map((p) => +(d.by_holding_period[p].expected_value).toFixed(4))

  holdingPeriodOption.value = {
    tooltip: { ...BASE_TOOLTIP },
    legend:  { data: ['Win Rate %', 'EV%'], bottom: 0, textStyle: { color: '#94a3b8' } },
    grid:    { ...BASE_GRID },
    xAxis:   { ...BASE_XAXIS, data: periods },
    yAxis:   [
      { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: '{value}%' } },
      { ...BASE_YAXIS, position: 'right', axisLabel: { color: '#64748b', formatter: '{value}%' } },
    ],
    series: [
      { name: 'Win Rate %', type: 'bar', data: winRates, yAxisIndex: 0, barMaxWidth: 40,
        itemStyle: { color: (p: { value: number }) => p.value > 50 ? '#22c55e' : '#ef4444', borderRadius: [4,4,0,0] } },
      { name: 'EV%', type: 'line', data: evs, yAxisIndex: 1, symbol: 'circle', symbolSize: 6,
        lineStyle: { color: '#3b82f6', width: 2 }, itemStyle: { color: '#3b82f6' } },
    ],
  }

  // Day-of-week
  const dow = d.by_day_of_week
  const dowDays = Object.keys(dow)
  const dowWR   = dowDays.map((day) => +(dow[day].win_rate * 100).toFixed(2))
  const dowAvg  = dowDays.map((day) => +(dow[day].avg_return_pct).toFixed(4))
  dowOption.value = {
    tooltip: { ...BASE_TOOLTIP },
    grid:    { ...BASE_GRID },
    xAxis:   { ...BASE_XAXIS, data: dowDays },
    yAxis:   { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: '{value}%' } },
    series: [{
      type: 'bar', data: dowAvg, barMaxWidth: 40,
      itemStyle: { color: (p: { value: number }) => p.value > 0 ? '#22c55e' : '#ef4444', borderRadius: [4,4,0,0] },
    }],
  }
}

onMounted(() => {
  if (!marketStore.availableTickers.length) marketStore.loadAvailable()
  loadAll()
})
</script>
