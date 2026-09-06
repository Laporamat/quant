<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden gap-0 animate-fade-in">

    <!-- ══ LEFT SIDEBAR — context panel ══════════════════════════════════════ -->
    <aside class="hidden lg:flex flex-col w-72 shrink-0 border-r border-surface-700/50 bg-surface-900/50">

      <!-- Ticker selector -->
      <div class="p-4 border-b border-surface-700/50 space-y-3">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center shrink-0">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
            </svg>
          </div>
          <div>
            <p class="text-xs font-semibold text-surface-100">QuantAI</p>
            <p class="text-xs text-surface-500">Trading Assistant</p>
          </div>
          <span class="ml-auto flex items-center gap-1 text-xs text-bull">
            <span class="w-1.5 h-1.5 rounded-full bg-bull animate-pulse inline-block" />
            Online
          </span>
        </div>

        <!-- Ticker input -->
        <div class="space-y-1">
          <label class="text-xs text-surface-400">วิเคราะห์หุ้น</label>
          <TickerSearch
            :model-value="activeTicker ? [activeTicker] : []"
            @update:model-value="onTickerChange"
            :multi="false"
            placeholder="เลือกหุ้น..."
          />
        </div>
      </div>

      <!-- Live market context -->
      <div class="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-3">
        <div v-if="activeTicker && marketCtx" class="space-y-2">
          <p class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Market Context</p>
          <div class="glass p-3 text-xs space-y-1.5 leading-relaxed text-surface-300"
            v-html="renderMarkdown(marketCtx)" />
        </div>

        <div v-else-if="activeTicker && ctxLoading" class="space-y-2">
          <div v-for="i in 8" :key="i" class="h-3 bg-surface-700 rounded animate-skeleton" />
        </div>

        <!-- Quick questions -->
        <div v-if="suggestions.length" class="space-y-1.5">
          <p class="text-xs font-semibold text-surface-400 uppercase tracking-wider pt-1">คำถามแนะนำ</p>
          <button
            v-for="s in suggestions" :key="s"
            @click="sendMessage(s)"
            class="w-full text-left px-3 py-2 rounded-lg text-xs text-surface-300 bg-surface-800/50 hover:bg-primary-600/20 hover:text-primary-300 border border-surface-700/30 hover:border-primary-600/30 transition-all duration-150 leading-snug"
          >{{ s }}</button>
        </div>
      </div>

      <!-- Knowledge topics -->
      <div class="p-3 border-t border-surface-700/50">
        <p class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">หัวข้อ</p>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="topic in quickTopics" :key="topic.q"
            @click="sendMessage(topic.q)"
            class="px-2 py-0.5 rounded-full text-xs bg-surface-800 text-surface-400 hover:bg-primary-600/20 hover:text-primary-300 border border-surface-700/30 transition-all"
          >{{ topic.label }}</button>
        </div>
      </div>
    </aside>

    <!-- ══ MAIN CHAT AREA ═════════════════════════════════════════════════════ -->
    <div class="flex flex-col flex-1 min-w-0">

      <!-- Top bar (mobile) -->
      <div class="flex lg:hidden items-center gap-2 px-4 h-12 border-b border-surface-700/50 shrink-0">
        <div class="w-32">
          <TickerSearch
            :model-value="activeTicker ? [activeTicker] : []"
            @update:model-value="onTickerChange"
            :multi="false" placeholder="หุ้น..."
          />
        </div>
        <span class="text-xs text-surface-400 ml-auto">QuantAI · Trading Assistant</span>
      </div>

      <!-- Messages area -->
      <div ref="messagesEl" class="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">

        <!-- Welcome screen -->
        <div v-if="!messages.length" class="flex flex-col items-center justify-center h-full min-h-[300px] gap-6 text-center px-4">
          <div class="w-16 h-16 rounded-2xl bg-primary-600/20 border border-primary-600/30 flex items-center justify-center">
            <svg class="w-8 h-8 text-primary-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"/>
            </svg>
          </div>
          <div>
            <h2 class="text-xl font-bold text-surface-100">QuantAI — Trading Assistant</h2>
            <p class="text-sm text-surface-400 mt-1.5 max-w-sm">
              ถามได้ทุกเรื่องเกี่ยวกับการเทรด · Technical Analysis · Risk Management
              · Strategy · ข้อมูลหุ้นจริง 20 ปี
            </p>
          </div>
          <!-- Starter chips -->
          <div class="flex flex-wrap justify-center gap-2 max-w-lg">
            <button
              v-for="s in starterQuestions" :key="s"
              @click="sendMessage(s)"
              class="px-3 py-1.5 rounded-full text-sm bg-surface-800 text-surface-300 hover:bg-primary-600/20 hover:text-primary-300 border border-surface-700/30 hover:border-primary-600/30 transition-all"
            >{{ s }}</button>
          </div>
        </div>

        <!-- Chat messages -->
        <template v-for="(msg, i) in messages" :key="i">

          <!-- User bubble -->
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="max-w-[75%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-primary-600 text-white text-sm leading-relaxed">
              {{ msg.content }}
            </div>
          </div>

          <!-- AI bubble -->
          <div v-else class="flex gap-3 items-start">
            <div class="w-8 h-8 rounded-xl bg-primary-600/20 border border-primary-600/30 flex items-center justify-center shrink-0 mt-0.5">
              <svg class="w-4 h-4 text-primary-400" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div
                class="glass px-4 py-3 rounded-2xl rounded-tl-sm text-sm text-surface-200 leading-relaxed prose prose-invert prose-sm max-w-none"
                v-html="renderMarkdown(msg.content + (msg.streaming ? '<span class=\'inline-block w-2 h-4 bg-primary-400 animate-pulse ml-0.5 rounded-sm align-middle\'/>' : ''))"
              />
              <div v-if="!msg.streaming && msg.engine" class="flex items-center gap-2 mt-1.5 px-1">
                <span class="text-xs text-surface-600">
                  {{ msg.engine === 'openai_gpt' ? '🤖 GPT-4o-mini' : '⚡ Built-in Engine' }}
                </span>
                <span v-if="msg.ticker" class="text-xs text-surface-600">· {{ msg.ticker }}</span>
              </div>
            </div>
          </div>

        </template>

        <!-- Loading dots -->
        <div v-if="loading && !streamingMsg" class="flex gap-3 items-start">
          <div class="w-8 h-8 rounded-xl bg-primary-600/20 border border-primary-600/30 flex items-center justify-center shrink-0">
            <svg class="w-4 h-4 text-primary-400" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
            </svg>
          </div>
          <div class="glass px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5">
            <span v-for="j in 3" :key="j"
              class="w-2 h-2 rounded-full bg-primary-400 animate-bounce"
              :style="{ animationDelay: `${(j-1) * 0.15}s` }" />
          </div>
        </div>

      </div>

      <!-- ── Input bar ─────────────────────────────────────────────────────── -->
      <div class="shrink-0 border-t border-surface-700/50 p-4">
        <div class="flex items-end gap-3 bg-surface-800 border border-surface-700 rounded-2xl px-4 py-2.5 focus-within:border-primary-500 transition-colors">

          <!-- Textarea -->
          <textarea
            ref="inputEl"
            v-model="inputText"
            @keydown.enter.exact.prevent="handleEnter"
            @keydown.enter.shift.exact="() => {}"
            :disabled="loading"
            placeholder="ถามเกี่ยวกับการเทรด... (Enter ส่ง, Shift+Enter ขึ้นบรรทัดใหม่)"
            rows="1"
            class="flex-1 bg-transparent text-sm text-surface-100 placeholder-surface-500 outline-none resize-none leading-relaxed min-h-[24px] max-h-[120px]"
            @input="autoResize"
          />

          <!-- Ticker badge (mobile) -->
          <span v-if="activeTicker"
            class="hidden sm:flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-primary-600/20 text-primary-300 border border-primary-600/30 shrink-0 self-center">
            {{ activeTicker }}
          </span>

          <!-- Clear button -->
          <button v-if="messages.length" @click="clearChat"
            class="text-surface-500 hover:text-surface-300 transition-colors shrink-0 self-center"
            title="Clear chat">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/>
            </svg>
          </button>

          <!-- Send button -->
          <button @click="() => sendMessage()"
            :disabled="!inputText.trim() || loading"
            class="w-8 h-8 rounded-xl bg-primary-600 hover:bg-primary-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all shrink-0 self-center">
            <svg v-if="!loading" class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"/>
            </svg>
            <svg v-else class="w-4 h-4 text-white animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          </button>
        </div>

        <!-- Hint -->
        <p class="text-xs text-surface-600 text-center mt-2">
          QuantAI ใช้ข้อมูลย้อนหลัง 20 ปีและ OCaml engine · ไม่ใช่คำแนะนำลงทุน
        </p>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import TickerSearch from '@/components/shared/TickerSearch.vue'
import { aiApi, type ChatMessage } from '@/api/aiApi'
import { useMarketStore } from '@/stores/marketStore'

const marketStore = useMarketStore()

// ── State ─────────────────────────────────────────────────────────────────────
interface Message {
  role:      'user' | 'assistant'
  content:   string
  engine?:   string
  ticker?:   string
  streaming?: boolean
}

const messages     = ref<Message[]>([])
const inputText    = ref('')
const loading      = ref(false)
const streamingMsg = ref('')
const activeTicker = ref<string | null>(null)
const marketCtx    = ref('')
const ctxLoading   = ref(false)
const suggestions  = ref<string[]>([])
const messagesEl   = ref<HTMLElement>()
const inputEl      = ref<HTMLTextAreaElement>()

// ── Quick topics ───────────────────────────────────────────────────────────────
const quickTopics = [
  { label: 'RSI',        q: 'RSI คืออะไร อ่านค่าอย่างไร?' },
  { label: 'MACD',       q: 'MACD ใช้งานอย่างไร?' },
  { label: 'Kelly',      q: 'Kelly Criterion คืออะไร?' },
  { label: 'VaR',        q: 'VaR คืออะไร ใช้อะไร?' },
  { label: 'Bollinger',  q: 'Bollinger Bands อ่านอย่างไร?' },
  { label: 'Stop Loss',  q: 'วิธีกำหนด Stop Loss ที่ดี' },
  { label: 'Backtest',   q: 'Backtest คืออะไร ต้องระวังอะไร?' },
  { label: 'จิตวิทยา',  q: 'จิตวิทยาการเทรดสำคัญอย่างไร?' },
  { label: 'FVG/SMC',   q: 'Smart Money Concepts คืออะไร?' },
  { label: 'Fibonacci',  q: 'Fibonacci Retracement ใช้อย่างไร?' },
]

const starterQuestions = [
  'RSI < 30 หมายความว่าอะไร?',
  'วิธีกำหนด Position Size ที่ปลอดภัย',
  'Mean Reversion vs Trend Following',
  'Backtest ดีต้องดูตัวชี้วัดอะไร?',
  'จิตวิทยาการเทรดสำคัญอย่างไร?',
  'วิเคราะห์ SPY ตอนนี้',
]

// ── Markdown renderer (lightweight, no external lib) ─────────────────────────
function renderMarkdown(text: string): string {
  if (!text) return ''
  return text
    // Code blocks
    .replace(/```([\s\S]*?)```/g, '<pre class="bg-surface-900 border border-surface-700 rounded-lg p-3 text-xs overflow-x-auto my-2 text-surface-200"><code>$1</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="bg-surface-900 border border-surface-700 text-primary-300 text-xs px-1.5 py-0.5 rounded font-mono">$1</code>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-surface-100 font-semibold">$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em class="text-surface-200">$1</em>')
    // Headers
    .replace(/^### (.+)$/gm, '<h3 class="text-sm font-bold text-surface-100 mt-3 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2 class="text-base font-bold text-surface-100 mt-3 mb-1.5">$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1 class="text-lg font-bold text-surface-100 mt-3 mb-2">$1</h1>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr class="border-surface-700/50 my-3"/>')
    // Tables (basic)
    .replace(/\|(.+)\|/g, (match) => {
      if (match.includes('---')) return ''
      const cells = match.split('|').filter(c => c.trim())
      const isHeader = false
      return `<tr>${cells.map(c => `<td class="px-2 py-1 border border-surface-700/50 text-xs">${c.trim()}</td>`).join('')}</tr>`
    })
    // List items  
    .replace(/^[-•] (.+)$/gm, '<li class="flex gap-1.5 items-start"><span class="text-primary-400 mt-0.5 shrink-0">•</span><span>$1</span></li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="flex gap-1.5 items-start"><span class="text-primary-400 font-mono text-xs mt-0.5 shrink-0 w-4">$1.</span><span>$2</span></li>')
    // Emoji coloring
    .replace(/(🟢|✅)/g, '<span class="text-bull">$1</span>')
    .replace(/(🔴|⚠️|❌)/g, '<span class="text-bear">$1</span>')
    .replace(/(🟡|💡|⚡)/g, '<span class="text-side">$1</span>')
    // Newlines
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>')
}

// ── Ticker change ─────────────────────────────────────────────────────────────
async function onTickerChange(v: string[]) {
  activeTicker.value = v[0] ?? null
  if (!activeTicker.value) { marketCtx.value = ''; return }
  ctxLoading.value = true
  try {
    const [ctxRes, sugRes] = await Promise.all([
      aiApi.marketContext(activeTicker.value),
      aiApi.suggestions(activeTicker.value),
    ])
    marketCtx.value = ctxRes.data.context
    suggestions.value = sugRes.data.suggestions
  } catch { marketCtx.value = '' }
  finally { ctxLoading.value = false }
}

// ── Send message ──────────────────────────────────────────────────────────────
async function sendMessage(text?: string) {
  const q = (text ?? inputText.value).trim()
  if (!q || loading.value) return

  // Add user message
  messages.value.push({ role: 'user', content: q })
  inputText.value = ''
  resetInputHeight()
  loading.value = true
  await scrollBottom()

  // Add streaming placeholder
  const streamIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', streaming: true })

  try {
    // Use SSE stream for typewriter effect
    const url = aiApi.streamUrl(q, activeTicker.value ?? undefined)
    const es  = new EventSource(url)
    let buffer = ''

    es.onmessage = async (e) => {
      const data = JSON.parse(e.data)
      if (data.done) {
        es.close()
        messages.value[streamIdx].streaming = false
        messages.value[streamIdx].engine    = 'rule_based'
        messages.value[streamIdx].ticker    = activeTicker.value ?? undefined
        loading.value = false
        await scrollBottom()
        // Load suggestions update
        if (activeTicker.value) {
          const s = await aiApi.suggestions(activeTicker.value).catch(() => null)
          if (s) suggestions.value = s.data.suggestions
        }
      } else if (data.delta) {
        buffer += data.delta
        messages.value[streamIdx].content = buffer
        await scrollBottom()
      }
    }

    es.onerror = async () => {
      es.close()
      // Fallback to non-streaming
      if (!buffer) {
        try {
          const history = messages.value
            .slice(0, streamIdx - 1)
            .map(m => ({ role: m.role, content: m.content }))
          const res = await aiApi.chat(q, history, activeTicker.value ?? undefined)
          messages.value[streamIdx].content   = res.data.content
          messages.value[streamIdx].engine    = res.data.engine
          messages.value[streamIdx].ticker    = res.data.ticker
        } catch { messages.value[streamIdx].content = 'เกิดข้อผิดพลาด ลองใหม่อีกครั้ง' }
      }
      messages.value[streamIdx].streaming = false
      loading.value = false
      await scrollBottom()
    }
  } catch {
    messages.value[streamIdx].content  = 'เกิดข้อผิดพลาด กรุณาลองใหม่'
    messages.value[streamIdx].streaming = false
    loading.value = false
  }
}

function handleEnter() { sendMessage() }

function clearChat() {
  messages.value = []
  marketCtx.value = ''
}

// ── Auto-resize textarea ──────────────────────────────────────────────────────
function autoResize() {
  if (!inputEl.value) return
  inputEl.value.style.height = 'auto'
  inputEl.value.style.height = Math.min(inputEl.value.scrollHeight, 120) + 'px'
}
function resetInputHeight() {
  if (inputEl.value) inputEl.value.style.height = 'auto'
}

// ── Scroll ────────────────────────────────────────────────────────────────────
async function scrollBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
onMounted(async () => {
  if (!marketStore.availableTickers.length) marketStore.loadAvailable()
  // Load default suggestions
  try {
    const s = await aiApi.suggestions()
    suggestions.value = s.data.suggestions
  } catch { /* ignore */ }
})
</script>

<style scoped>
/* Smooth message entrance */
.flex.justify-end,
.flex.gap-3 {
  animation: slideIn 0.2s ease-out;
}
@keyframes slideIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
