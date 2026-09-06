<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden animate-fade-in">

    <!-- ══ LEFT SIDEBAR ══════════════════════════════════════════════════════ -->
    <aside class="hidden lg:flex flex-col w-64 shrink-0 border-r border-surface-700/50 bg-surface-900/50">

      <!-- Header + provider status -->
      <div class="p-4 border-b border-surface-700/50 space-y-3">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center shrink-0">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-semibold text-surface-100">QuantAI</p>
            <p class="text-xs text-surface-500 truncate">{{ activeProviderLabel }}</p>
          </div>
        </div>

        <!-- Provider selector -->
        <div class="space-y-1">
          <label class="text-xs text-surface-400">AI Provider</label>
          <div class="space-y-1">
            <button
              v-for="pv in providers" :key="pv.id"
              @click="selectedProvider = pv.id as any"
              :disabled="!pv.available"
              class="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs transition-all"
              :class="selectedProvider === pv.id
                ? 'bg-primary-600/20 border border-primary-600/40 text-primary-300'
                : pv.available
                  ? 'bg-surface-800/50 border border-surface-700/30 text-surface-300 hover:border-primary-600/30 hover:text-surface-200'
                  : 'bg-surface-800/20 border border-surface-700/20 text-surface-600 cursor-not-allowed'"
            >
              <span class="text-base leading-none">{{ pv.icon }}</span>
              <span class="flex-1 text-left truncate">{{ pv.name }}</span>
              <span v-if="selectedProvider === pv.id" class="w-1.5 h-1.5 rounded-full bg-primary-400 shrink-0" />
              <span v-else-if="!pv.available" class="text-xs text-surface-600">✗</span>
            </button>
          </div>
        </div>

        <!-- Ticker -->
        <div class="space-y-1">
          <label class="text-xs text-surface-400">Market Context</label>
          <TickerSearch
            :model-value="activeTicker ? [activeTicker] : []"
            @update:model-value="onTickerChange"
            :multi="false" placeholder="เลือกหุ้น..."
          />
        </div>
      </div>

      <!-- Live context -->
      <div class="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-3">
        <div v-if="activeTicker && marketCtx" class="space-y-1.5">
          <p class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Live Data</p>
          <div class="glass p-2.5 rounded-lg text-xs text-surface-400 font-mono leading-relaxed whitespace-pre-wrap break-all">{{ marketCtx }}</div>
        </div>
        <div v-else-if="ctxLoading">
          <div v-for="i in 6" :key="i" class="h-3 bg-surface-700 rounded animate-skeleton mb-1.5" />
        </div>

        <div v-if="suggestions.length" class="space-y-1.5 pt-1">
          <p class="text-xs font-semibold text-surface-400 uppercase tracking-wider">คำถามแนะนำ</p>
          <button v-for="s in suggestions" :key="s"
            @click="activeTab === 'benchmark' ? setBenchmarkQ(s) : sendMessage(s)"
            class="w-full text-left px-2.5 py-1.5 rounded-lg text-xs text-surface-400 bg-surface-800/50 hover:bg-primary-600/15 hover:text-primary-300 border border-surface-700/30 transition-all leading-snug">
            {{ s }}
          </button>
        </div>
      </div>

      <!-- Topics -->
      <div class="p-3 border-t border-surface-700/50">
        <div class="flex flex-wrap gap-1">
          <button v-for="t in quickTopics" :key="t.q"
            @click="activeTab === 'benchmark' ? setBenchmarkQ(t.q) : sendMessage(t.q)"
            class="px-2 py-0.5 rounded-full text-xs bg-surface-800 text-surface-500 hover:bg-primary-600/15 hover:text-primary-300 border border-surface-700/30 transition-all">
            {{ t.label }}
          </button>
        </div>
      </div>
    </aside>

    <!-- ══ MAIN AREA ══════════════════════════════════════════════════════════ -->
    <div class="flex flex-col flex-1 min-w-0">

      <!-- Tabs -->
      <div class="flex items-center border-b border-surface-700/50 px-4 gap-1 shrink-0">
        <button v-for="tab in tabs" :key="tab.key"
          @click="activeTab = tab.key"
          class="tab-item text-sm" :class="{ active: activeTab === tab.key }">
          {{ tab.label }}
        </button>
        <div class="ml-auto flex items-center gap-2 py-2">
          <!-- Mobile ticker + provider -->
          <div class="flex lg:hidden items-center gap-2">
            <div class="w-28">
              <TickerSearch :model-value="activeTicker ? [activeTicker] : []"
                @update:model-value="onTickerChange" :multi="false" placeholder="Ticker..." />
            </div>
          </div>
          <span v-if="activeTicker" class="hidden sm:flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-primary-600/15 text-primary-300 border border-primary-600/25">
            {{ activeTicker }}
          </span>
        </div>
      </div>

      <!-- ══ TAB: CHAT ══ -->
      <div v-show="activeTab === 'chat'" class="flex flex-col flex-1 min-h-0">

        <!-- Messages -->
        <div ref="messagesEl" class="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">

          <!-- Welcome -->
          <div v-if="!messages.length" class="flex flex-col items-center justify-center h-full min-h-[260px] gap-5 text-center px-4">
            <div class="w-14 h-14 rounded-2xl bg-primary-600/15 border border-primary-600/25 flex items-center justify-center">
              <svg class="w-7 h-7 text-primary-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
              </svg>
            </div>
            <div>
              <h2 class="text-lg font-bold text-surface-100">QuantAI — Trading Assistant</h2>
              <p class="text-sm text-surface-400 mt-1 max-w-xs">ถามได้ทุกเรื่องเกี่ยวกับการเทรด · Technical Analysis · Risk Management · ข้อมูลจริง 20 ปี</p>
            </div>
            <div class="flex flex-wrap justify-center gap-2 max-w-md">
              <button v-for="s in starterQ" :key="s"
                @click="sendMessage(s)"
                class="px-3 py-1.5 rounded-full text-xs bg-surface-800 text-surface-300 hover:bg-primary-600/15 hover:text-primary-300 border border-surface-700/30 transition-all">
                {{ s }}
              </button>
            </div>
          </div>

          <!-- Messages -->
          <template v-for="(msg, i) in messages" :key="i">
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="max-w-[75%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-primary-600 text-white text-sm leading-relaxed">
                {{ msg.content }}
              </div>
            </div>
            <div v-else class="flex gap-2.5 items-start">
              <div class="w-7 h-7 rounded-xl bg-primary-600/15 border border-primary-600/25 flex items-center justify-center shrink-0 mt-0.5 text-xs">
                {{ providerEmoji(msg.provider) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="glass px-4 py-3 rounded-2xl rounded-tl-sm text-sm text-surface-200 leading-relaxed"
                  v-html="md(msg.content + (msg.streaming ? '<span class=\'inline-block w-1.5 h-4 bg-primary-400 animate-pulse ml-0.5 rounded-sm align-middle\'/>' : ''))" />
                <div v-if="!msg.streaming" class="flex items-center gap-2 mt-1 px-1">
                  <span class="text-xs text-surface-600">{{ providerLabel(msg.provider) }}</span>
                  <span v-if="msg.ticker" class="text-xs text-surface-600">· {{ msg.ticker }}</span>
                </div>
              </div>
            </div>
          </template>

          <!-- Typing indicator -->
          <div v-if="loading && !streamActive" class="flex gap-2.5 items-start">
            <div class="w-7 h-7 rounded-xl bg-primary-600/15 border border-primary-600/25 flex items-center justify-center shrink-0 text-xs">
              {{ providerEmoji(selectedProvider) }}
            </div>
            <div class="glass px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5">
              <span v-for="j in 3" :key="j" class="w-1.5 h-1.5 rounded-full bg-primary-400 animate-bounce"
                :style="{ animationDelay: `${(j-1)*0.15}s` }" />
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="shrink-0 border-t border-surface-700/50 p-3">
          <div class="flex items-end gap-2 bg-surface-800 border border-surface-700 rounded-2xl px-4 py-2.5 focus-within:border-primary-500 transition-colors">
            <textarea ref="inputEl" v-model="inputText"
              @keydown.enter.exact.prevent="handleEnter"
              :disabled="loading"
              placeholder="ถามเกี่ยวกับการเทรด... (Enter ส่ง)"
              rows="1"
              class="flex-1 bg-transparent text-sm text-surface-100 placeholder-surface-500 outline-none resize-none leading-relaxed min-h-[22px] max-h-[100px]"
              @input="autoResize" />
            <button v-if="messages.length" @click="clearChat"
              class="text-surface-500 hover:text-surface-300 shrink-0 self-center" title="Clear">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
            <button @click="() => sendMessage()"
              :disabled="!inputText.trim() || loading"
              class="w-8 h-8 rounded-xl bg-primary-600 hover:bg-primary-500 disabled:opacity-40 flex items-center justify-center transition-all shrink-0 self-center">
              <svg v-if="!loading" class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"/>
              </svg>
              <svg v-else class="w-4 h-4 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
            </button>
          </div>
          <p class="text-xs text-surface-600 text-center mt-1.5">
            QuantAI · ไม่ใช่คำแนะนำลงทุน · ข้อมูล 20 ปีจาก Yahoo Finance
          </p>
        </div>
      </div>

      <!-- ══ TAB: BENCHMARK ══ -->
      <div v-show="activeTab === 'benchmark'" class="flex flex-col flex-1 min-h-0 overflow-hidden">
        <div class="shrink-0 p-4 border-b border-surface-700/50 space-y-3">
          <div class="flex items-start gap-3">
            <div class="flex-1 space-y-1">
              <label class="text-xs text-surface-400">คำถามสำหรับทดสอบ</label>
              <textarea v-model="benchmarkQ"
                rows="2"
                placeholder="พิมพ์คำถาม แล้วกด Run Benchmark เพื่อส่งถาม OpenAI, Claude, และ Built-in พร้อมกัน..."
                class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-xl px-3 py-2.5 outline-none focus:border-primary-500 resize-none placeholder-surface-500" />
            </div>
            <button @click="runBenchmark" :disabled="!benchmarkQ.trim() || benchLoading"
              class="btn-primary flex items-center gap-2 mt-5 shrink-0">
              <svg v-if="benchLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/>
              </svg>
              Run All
            </button>
          </div>

          <!-- Presets -->
          <div class="flex flex-wrap gap-1.5">
            <span class="text-xs text-surface-500 self-center">Quick test:</span>
            <button v-for="p in benchPresets" :key="p"
              @click="benchmarkQ = p"
              class="px-2.5 py-1 rounded-full text-xs bg-surface-800 text-surface-400 hover:bg-primary-600/15 hover:text-primary-300 border border-surface-700/30 transition-all">
              {{ p }}
            </button>
          </div>
        </div>

        <!-- Results -->
        <div class="flex-1 overflow-y-auto scrollbar-thin p-4">

          <!-- Loading -->
          <div v-if="benchLoading" class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div v-for="i in 3" :key="i" class="glass rounded-2xl p-4 space-y-3 animate-pulse">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-xl bg-surface-700" />
                <div class="flex-1 h-4 bg-surface-700 rounded" />
              </div>
              <div v-for="j in 5" :key="j" class="h-3 bg-surface-700 rounded" :style="{ width: `${70+j*5}%` }" />
            </div>
          </div>

          <!-- Benchmark results -->
          <div v-else-if="benchResults.length" class="space-y-4">
            <!-- Question echo + market ctx -->
            <div class="glass p-3 rounded-xl">
              <p class="text-xs text-surface-400 mb-1">คำถาม</p>
              <p class="text-sm text-surface-200 font-medium">{{ benchQuestion }}</p>
              <p v-if="benchMarketCtx" class="text-xs text-surface-500 mt-2 font-mono">{{ benchMarketCtx }}</p>
            </div>

            <!-- 3 columns -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div v-for="r in benchResults" :key="r.provider"
                class="glass rounded-2xl flex flex-col overflow-hidden"
                :class="bestProvider === r.provider ? 'border border-primary-500/50 shadow-glow' : ''">

                <!-- Provider header -->
                <div class="px-4 py-3 border-b flex items-center justify-between"
                  :class="{
                    'bg-[#10a37f]/10 border-[#10a37f]/20': r.provider === 'openai',
                    'bg-[#cc785c]/10 border-[#cc785c]/20': r.provider === 'anthropic',
                    'bg-primary-600/10 border-primary-600/20': r.provider === 'rule_based',
                  }">
                  <div class="flex items-center gap-2">
                    <span class="text-xl">{{ providerEmoji(r.provider) }}</span>
                    <div>
                      <p class="text-xs font-bold text-surface-100">{{ providerLabel(r.provider) }}</p>
                      <p class="text-xs text-surface-500">{{ r.model ?? 'built-in' }}</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <div v-if="bestProvider === r.provider"
                      class="text-xs font-bold text-primary-300 bg-primary-600/20 px-2 py-0.5 rounded-full border border-primary-600/30">
                      🏆 แนะนำ
                    </div>
                  </div>
                </div>

                <!-- Stats bar -->
                <div class="px-4 py-2 flex items-center gap-4 text-xs border-b border-surface-700/30">
                  <div class="flex items-center gap-1" :class="r.available ? 'text-bull' : 'text-bear'">
                    <span>{{ r.available ? '🟢' : '🔴' }}</span>
                    <span>{{ r.available ? 'Ready' : 'Unavailable' }}</span>
                  </div>
                  <div v-if="r.available" class="text-surface-400">
                    ⏱ {{ r.latency_ms }}ms
                  </div>
                  <div v-if="r.char_count" class="text-surface-400">
                    {{ r.char_count }} chars
                  </div>
                </div>

                <!-- Answer -->
                <div class="flex-1 p-4 overflow-y-auto scrollbar-thin max-h-96">
                  <div v-if="r.error" class="text-sm text-bear">
                    ⚠️ {{ r.error }}
                  </div>
                  <div v-else-if="r.content"
                    class="text-sm text-surface-200 leading-relaxed"
                    v-html="md(r.content)" />
                  <div v-else class="text-sm text-surface-500 italic">ไม่มีคำตอบ</div>
                </div>
              </div>
            </div>

            <!-- Comparison table -->
            <div class="glass p-4 rounded-xl">
              <h3 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">เปรียบเทียบ</h3>
              <div class="overflow-x-auto">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="border-b border-surface-700/50">
                      <th class="text-left py-2 px-3 text-surface-400">Provider</th>
                      <th class="text-right py-2 px-3 text-surface-400">สถานะ</th>
                      <th class="text-right py-2 px-3 text-surface-400">Latency</th>
                      <th class="text-right py-2 px-3 text-surface-400">ความยาวคำตอบ</th>
                      <th class="text-center py-2 px-3 text-surface-400">คะแนน</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="r in benchResults" :key="r.provider"
                      class="border-b border-surface-700/20 hover:bg-surface-700/10 transition-colors"
                      :class="bestProvider === r.provider ? 'bg-primary-600/5' : ''">
                      <td class="py-2.5 px-3">
                        <span class="mr-1.5">{{ providerEmoji(r.provider) }}</span>
                        <span class="font-medium text-surface-200">{{ providerLabel(r.provider) }}</span>
                      </td>
                      <td class="py-2.5 px-3 text-right">
                        <span :class="r.available ? 'text-bull' : 'text-bear'">{{ r.available ? '✓' : '✗' }}</span>
                      </td>
                      <td class="py-2.5 px-3 text-right tabular-nums"
                        :class="r.latency_ms < 1000 ? 'text-bull' : r.latency_ms < 3000 ? 'text-side' : 'text-bear'">
                        {{ r.available ? r.latency_ms + 'ms' : '—' }}
                      </td>
                      <td class="py-2.5 px-3 text-right tabular-nums text-surface-300">
                        {{ r.char_count ?? '—' }}
                      </td>
                      <td class="py-2.5 px-3 text-center">
                        <span v-if="bestProvider === r.provider" class="text-primary-300 font-bold">🏆 ดีที่สุด</span>
                        <span v-else-if="!r.available" class="text-surface-600">—</span>
                        <span v-else class="text-surface-400">—</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-else class="flex flex-col items-center justify-center h-full min-h-[300px] text-surface-500 gap-4">
            <svg class="w-12 h-12 opacity-20" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/>
            </svg>
            <div class="text-center">
              <p class="text-sm font-medium text-surface-400">Benchmark Mode</p>
              <p class="text-xs mt-1">พิมพ์คำถามแล้วกด Run All — ทดสอบ OpenAI, Claude, Built-in พร้อมกัน</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import TickerSearch from '@/components/shared/TickerSearch.vue'
import { aiApi, type ChatMessage, type Provider, type ProviderInfo, type BenchmarkResult } from '@/api/aiApi'
import { useMarketStore } from '@/stores/marketStore'

const marketStore = useMarketStore()

// ── Tabs ──────────────────────────────────────────────────────────────────────
const activeTab = ref<'chat' | 'benchmark'>('chat')
const tabs = [
  { key: 'chat'      as const, label: '💬 Chat' },
  { key: 'benchmark' as const, label: '⚡ Benchmark' },
]

// ── Provider state ─────────────────────────────────────────────────────────────
const providers         = ref<ProviderInfo[]>([])
const selectedProvider  = ref<Provider>('auto')

const activeProviderLabel = computed(() => {
  if (selectedProvider.value === 'auto') return 'Auto (best available)'
  return providers.value.find(p => p.id === selectedProvider.value)?.name ?? selectedProvider.value
})

function providerEmoji(p?: string) {
  if (p === 'openai')     return '🟢'
  if (p === 'anthropic')  return '🟠'
  if (p?.includes('fallback')) return '⚡'
  return '⚡'
}
function providerLabel(p?: string) {
  if (p === 'openai')                return `OpenAI GPT-4o-mini`
  if (p === 'anthropic')             return `Claude 3 Haiku`
  if (p === 'rule_based')            return 'Built-in Knowledge'
  if (p === 'rule_based_fallback')   return 'Built-in (fallback)'
  return p ?? 'Unknown'
}

// ── Chat state ─────────────────────────────────────────────────────────────────
interface Message {
  role: 'user' | 'assistant'
  content: string
  provider?: string
  ticker?: string
  streaming?: boolean
}

const messages     = ref<Message[]>([])
const inputText    = ref('')
const loading      = ref(false)
const streamActive = ref(false)
const activeTicker = ref<string | null>(null)
const marketCtx    = ref('')
const ctxLoading   = ref(false)
const suggestions  = ref<string[]>([])
const messagesEl   = ref<HTMLElement>()
const inputEl      = ref<HTMLTextAreaElement>()

// ── Benchmark state ────────────────────────────────────────────────────────────
const benchmarkQ    = ref('')
const benchLoading  = ref(false)
const benchResults  = ref<BenchmarkResult[]>([])
const benchQuestion = ref('')
const benchMarketCtx = ref('')

const benchPresets = [
  'RSI 30 ต่ำกว่า ควรซื้อเลยไหม?',
  'Kelly Criterion คืออะไร ใช้อย่างไร?',
  'Stop Loss ควรวางที่ไหน?',
  'Mean Reversion กับ Trend Following ต่างกันอย่างไร?',
  'Backtest ที่ดีต้องมี Sharpe เท่าไหร่?',
]

const bestProvider = computed(() => {
  if (!benchResults.value.length) return null
  const avail = benchResults.value.filter(r => r.available && r.content && !r.error)
  if (!avail.length) return null
  // Rank: openai > anthropic > rule_based (by quality preference + latency)
  const priority: Record<string, number> = { openai: 3, anthropic: 2, rule_based: 1 }
  avail.sort((a, b) => (priority[b.provider] ?? 0) - (priority[a.provider] ?? 0))
  return avail[0].provider
})

// ── Quick topics ───────────────────────────────────────────────────────────────
const quickTopics = [
  { label: 'RSI',       q: 'RSI คืออะไร อ่านค่าอย่างไร?' },
  { label: 'MACD',      q: 'MACD ใช้งานอย่างไร?' },
  { label: 'Kelly',     q: 'Kelly Criterion คืออะไร?' },
  { label: 'VaR',       q: 'VaR กับ CVaR ต่างกันอย่างไร?' },
  { label: 'Bollinger', q: 'Bollinger Bands Squeeze คืออะไร?' },
  { label: 'SL/TP',     q: 'วิธีกำหนด Stop Loss ที่ดี' },
  { label: 'Backtest',  q: 'Backtest ต้องระวังอะไรบ้าง?' },
  { label: 'จิตวิทยา', q: 'จิตวิทยาการเทรดสำคัญอย่างไร?' },
  { label: 'SMC',       q: 'Smart Money Concepts คืออะไร?' },
  { label: 'Fib',       q: 'Fibonacci Retracement ใช้อย่างไร?' },
]

const starterQ = [
  'RSI < 30 ควรซื้อเลยไหม?',
  'กำหนด Position Size อย่างไรให้ปลอดภัย?',
  'Mean Reversion vs Trend Following',
  'Backtest ดูตัวชี้วัดอะไรบ้าง?',
  'วิเคราะห์ SPY ตอนนี้',
]

// ── Markdown ──────────────────────────────────────────────────────────────────
function md(text: string): string {
  if (!text) return ''
  return text
    .replace(/```([\s\S]*?)```/g, '<pre class="bg-surface-900 border border-surface-700 rounded-lg p-3 text-xs overflow-x-auto my-2"><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code class="bg-surface-900 border border-surface-700 text-primary-300 text-xs px-1.5 py-0.5 rounded font-mono">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-surface-100 font-semibold">$1</strong>')
    .replace(/^### (.+)$/gm, '<h3 class="text-sm font-bold text-surface-100 mt-3 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2 class="font-bold text-surface-100 mt-3 mb-1.5">$1</h2>')
    .replace(/^---$/gm, '<hr class="border-surface-700/50 my-3"/>')
    .replace(/^[-•] (.+)$/gm, '<div class="flex gap-1.5 items-start my-0.5"><span class="text-primary-400 shrink-0">•</span><span>$1</span></div>')
    .replace(/^(\d+)\. (.+)$/gm, '<div class="flex gap-1.5 items-start my-0.5"><span class="text-primary-400 font-mono text-xs shrink-0 w-4">$1.</span><span>$2</span></div>')
    .replace(/(🟢|✅)/g, '<span class="text-bull">$1</span>')
    .replace(/(🔴|⚠️)/g, '<span class="text-bear">$1</span>')
    .replace(/(💡|⚡|🟡)/g, '<span class="text-side">$1</span>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>')
}

// ── Ticker change ─────────────────────────────────────────────────────────────
async function onTickerChange(v: string[]) {
  activeTicker.value = v[0] ?? null
  if (!activeTicker.value) { marketCtx.value = ''; return }
  ctxLoading.value = true
  try {
    const [ctxR, sugR] = await Promise.all([
      aiApi.marketContext(activeTicker.value),
      aiApi.suggestions(activeTicker.value),
    ])
    marketCtx.value   = ctxR.data.context
    suggestions.value = sugR.data.suggestions
  } catch { marketCtx.value = '' }
  finally { ctxLoading.value = false }
}

// ── Send chat message ─────────────────────────────────────────────────────────
async function sendMessage(text?: string) {
  const q = (text ?? inputText.value).trim()
  if (!q || loading.value) return
  messages.value.push({ role: 'user', content: q })
  inputText.value = ''
  if (inputEl.value) inputEl.value.style.height = 'auto'
  loading.value = true
  await scrollBottom()

  const idx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', streaming: true })
  streamActive.value = true

  const url = aiApi.streamUrl(q, activeTicker.value ?? undefined, selectedProvider.value)
  const es  = new EventSource(url)
  let buf   = ''

  es.onmessage = async (e) => {
    const data = JSON.parse(e.data)
    if (data.done) {
      es.close()
      messages.value[idx].streaming  = false
      messages.value[idx].provider   = selectedProvider.value === 'auto' ? undefined : selectedProvider.value
      streamActive.value = false
      loading.value      = false
      await scrollBottom()
    } else if (data.delta) {
      buf += data.delta
      messages.value[idx].content = buf
      await scrollBottom()
    }
  }

  es.onerror = async () => {
    es.close()
    if (!buf) {
      try {
        const r = await aiApi.chat(q, [], activeTicker.value ?? undefined, selectedProvider.value)
        messages.value[idx].content  = r.data.content
        messages.value[idx].provider = r.data.provider
      } catch { messages.value[idx].content = 'เกิดข้อผิดพลาด กรุณาลองใหม่' }
    }
    messages.value[idx].streaming = false
    streamActive.value = false
    loading.value = false
    await scrollBottom()
  }
}

function handleEnter() { sendMessage() }
function clearChat() { messages.value = [] }

// ── Benchmark ─────────────────────────────────────────────────────────────────
function setBenchmarkQ(q: string) {
  benchmarkQ.value = q
  activeTab.value = 'benchmark'
}

async function runBenchmark() {
  if (!benchmarkQ.value.trim() || benchLoading.value) return
  benchLoading.value = true
  benchResults.value = []
  try {
    const r = await aiApi.benchmark(benchmarkQ.value.trim(), activeTicker.value ?? undefined)
    benchResults.value  = r.data.results
    benchQuestion.value = r.data.question
    benchMarketCtx.value = r.data.market_ctx
  } finally {
    benchLoading.value = false
  }
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function autoResize() {
  if (!inputEl.value) return
  inputEl.value.style.height = 'auto'
  inputEl.value.style.height = Math.min(inputEl.value.scrollHeight, 100) + 'px'
}

async function scrollBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

// ── Init ──────────────────────────────────────────────────────────────────────
onMounted(async () => {
  if (!marketStore.availableTickers.length) marketStore.loadAvailable()
  try {
    const [pRes, sRes] = await Promise.all([
      aiApi.providers(),
      aiApi.suggestions(),
    ])
    providers.value   = pRes.data.providers
    suggestions.value = sRes.data.suggestions
  } catch { /* ignore */ }
})
</script>

<style scoped>
.flex.justify-end, .flex.gap-2\.5 { animation: slideIn .18s ease-out; }
@keyframes slideIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
