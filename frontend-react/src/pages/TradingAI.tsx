import { useState, useEffect, useRef } from 'react'
import { aiApi, type ChatMessage } from '@/api/aiApi'
import clsx from 'clsx'

function md(text: string) {
  return text
    .replace(/```([\s\S]*?)```/g, '<pre class="bg-surface-900 border border-surface-700 rounded-lg p-3 text-xs overflow-x-auto my-2"><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code class="bg-surface-900 border border-surface-700 text-primary-300 text-xs px-1.5 py-0.5 rounded font-mono">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-surface-100 font-semibold">$1</strong>')
    .replace(/^### (.+)$/gm, '<h3 class="text-sm font-bold text-surface-100 mt-3 mb-1">$1</h3>')
    .replace(/^[-•] (.+)$/gm, '<div class="flex gap-1.5 items-start my-0.5"><span class="text-primary-400 shrink-0">•</span><span>$1</span></div>')
    .replace(/\n\n/g, '<br/><br/>').replace(/\n/g, '<br/>')
}

interface Msg extends ChatMessage { provider?: string; streaming?: boolean }

const STARTERS = ['RSI < 30 ควรซื้อเลยไหม?','Kelly Criterion คืออะไร?','Mean Reversion vs Trend Following','Backtest ดูตัวชี้วัดอะไรบ้าง?','วิเคราะห์ SPY ตอนนี้']

export default function TradingAI() {
  const [messages,  setMessages]  = useState<Msg[]>([])
  const [input,     setInput]     = useState('')
  const [ticker,    setTicker]    = useState('')
  const [provider,  setProvider]  = useState('auto')
  const [loading,   setLoading]   = useState(false)
  const [providers, setProviders] = useState<any[]>([])
  const [suggestions, setSuggestions] = useState<string[]>(STARTERS)
  const [tab, setTab] = useState<'chat'|'benchmark'>('chat')
  const [benchQ, setBenchQ]       = useState('')
  const [benchLoading, setBenchL] = useState(false)
  const [benchResults, setBenchR] = useState<any[]>([])
  const scrollEl = useRef<HTMLDivElement>(null)

  useEffect(() => { aiApi.providers().then(r => setProviders(r.data.providers)).catch(() => {}) }, [])
  useEffect(() => { scrollEl.current?.scrollTo({ top: scrollEl.current.scrollHeight, behavior: 'smooth' }) }, [messages])

  async function send(text?: string) {
    const q = (text ?? input).trim()
    if (!q || loading) return
    setInput('')
    setMessages(m => [...m, { role:'user', content:q }])
    setLoading(true)
    const idx = messages.length + 1
    setMessages(m => [...m, { role:'assistant', content:'', streaming:true }])

    const url = aiApi.streamUrl(q, ticker || undefined, provider as any)
    const es  = new EventSource(url)
    let buf   = ''

    es.onmessage = e => {
      const d = JSON.parse(e.data)
      if (d.done) {
        es.close()
        setMessages(m => m.map((msg,i) => i === idx ? { ...msg, streaming:false, provider } : msg))
        setLoading(false)
      } else if (d.delta) {
        buf += d.delta
        setMessages(m => m.map((msg,i) => i === idx ? { ...msg, content:buf } : msg))
      }
    }
    es.onerror = async () => {
      es.close()
      if (!buf) {
        const r = await aiApi.chat(q, [], ticker || undefined, provider as any).catch(() => null)
        if (r) buf = r.data.content
      }
      setMessages(m => m.map((msg,i) => i === idx ? { ...msg, content: buf || 'เกิดข้อผิดพลาด', streaming:false } : msg))
      setLoading(false)
    }
  }

  async function runBenchmark() {
    if (!benchQ.trim()) return
    setBenchL(true); setBenchR([])
    const r = await aiApi.benchmark(benchQ.trim(), ticker || undefined).catch(() => null)
    if (r) setBenchR(r.data.results)
    setBenchL(false)
  }

  const provIcon = (p?: string) => p === 'openai' ? '🟢' : p === 'anthropic' ? '🟠' : '⚡'
  const provLabel = (p?: string) => p === 'openai' ? 'GPT-4o-mini' : p === 'anthropic' ? 'Claude Haiku' : 'Built-in'

  return (
    <div className="flex h-[calc(100vh-3.5rem)] gap-0 overflow-hidden animate-fade-in">
      {/* Sidebar */}
      <aside className="hidden lg:flex flex-col w-64 shrink-0 border-r border-surface-700/50 bg-surface-900/50">
        <div className="p-4 border-b border-surface-700/50 space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center shrink-0 text-white text-sm">✦</div>
            <div><p className="text-xs font-semibold text-surface-100">QuantAI</p><p className="text-xs text-surface-500">Trading Assistant</p></div>
          </div>
          {/* Provider */}
          <div className="space-y-1">
            <label className="text-xs text-surface-400">AI Provider</label>
            <div className="space-y-1">
              {[{ id:'auto',label:'Auto (Best)' }, ...providers.filter(p=>p.id!=='local')].map(p => (
                <button key={p.id ?? 'auto'} onClick={() => setProvider(p.id ?? 'auto')}
                  disabled={p.available === false}
                  className={clsx('w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-all border',
                    provider === (p.id ?? 'auto')
                      ? 'bg-primary-600/20 border-primary-600/40 text-primary-300'
                      : p.available === false
                        ? 'bg-surface-800/20 border-surface-700/20 text-surface-600 cursor-not-allowed'
                        : 'bg-surface-800/50 border-surface-700/30 text-surface-300 hover:border-primary-600/30')}>
                  <span>{p.icon ?? '⚡'}</span>
                  <span className="flex-1 text-left truncate">{p.label ?? p.name ?? 'Auto'}</span>
                  {p.available === false && <span className="text-surface-600">✗</span>}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-surface-400">Market Context</label>
            <input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())}
              placeholder="SPY, AAPL, ..." className="input-base text-xs py-1.5"/>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          <p className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">คำถามแนะนำ</p>
          {suggestions.map(s => (
            <button key={s} onClick={() => send(s)}
              className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs text-surface-400 bg-surface-800/50 hover:bg-primary-600/15 hover:text-primary-300 border border-surface-700/30 transition-all leading-snug">
              {s}
            </button>
          ))}
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Tabs */}
        <div className="flex items-center border-b border-surface-700/50 px-4 gap-1 shrink-0">
          {[{ k:'chat',l:'💬 Chat' },{ k:'benchmark',l:'⚡ Benchmark' }].map(t => (
            <button key={t.k} onClick={() => setTab(t.k as any)}
              className={clsx('tab-item', tab === t.k && 'tab-active')}>
              {t.l}
            </button>
          ))}
        </div>

        {/* Chat Tab */}
        {tab === 'chat' && (
          <>
            <div ref={scrollEl} className="flex-1 overflow-y-auto p-4 space-y-4">
              {!messages.length && (
                <div className="flex flex-col items-center justify-center h-full min-h-[260px] gap-5 text-center">
                  <div className="w-14 h-14 rounded-2xl bg-primary-600/15 border border-primary-600/25 flex items-center justify-center text-2xl">✦</div>
                  <div>
                    <h2 className="text-lg font-bold text-surface-100">QuantAI Trading Assistant</h2>
                    <p className="text-sm text-surface-400 mt-1 max-w-xs">ถามได้ทุกเรื่องเกี่ยวกับการเทรด · ข้อมูลจริง 20 ปี</p>
                  </div>
                  <div className="flex flex-wrap justify-center gap-2">
                    {STARTERS.map(s => (
                      <button key={s} onClick={() => send(s)}
                        className="px-3 py-1.5 rounded-full text-xs bg-surface-800 text-surface-300 hover:bg-primary-600/15 hover:text-primary-300 border border-surface-700/30 transition-all">
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((msg, i) => (
                msg.role === 'user'
                  ? <div key={i} className="flex justify-end">
                      <div className="max-w-[75%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-primary-600 text-white text-sm">{msg.content}</div>
                    </div>
                  : <div key={i} className="flex gap-2.5 items-start">
                      <div className="w-7 h-7 rounded-xl bg-primary-600/15 border border-primary-600/25 flex items-center justify-center shrink-0 text-xs">{provIcon(msg.provider)}</div>
                      <div className="flex-1">
                        <div className="glass px-4 py-3 rounded-2xl rounded-tl-sm text-sm text-surface-200 leading-relaxed"
                          dangerouslySetInnerHTML={{ __html: md(msg.content + (msg.streaming ? '<span class="inline-block w-1.5 h-4 bg-primary-400 animate-pulse ml-0.5 rounded-sm align-middle"/>' : '')) }}/>
                        {!msg.streaming && <p className="text-xs text-surface-600 mt-1 px-1">{provLabel(msg.provider)}</p>}
                      </div>
                    </div>
              ))}
              {loading && !messages.at(-1)?.streaming && (
                <div className="flex gap-2.5 items-start">
                  <div className="w-7 h-7 rounded-xl bg-primary-600/15 border border-primary-600/25 flex items-center justify-center shrink-0 text-xs">✦</div>
                  <div className="glass px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5">
                    {[0,1,2].map(j => <span key={j} className="w-1.5 h-1.5 rounded-full bg-primary-400 animate-bounce" style={{ animationDelay:`${j*.15}s` }}/>)}
                  </div>
                </div>
              )}
            </div>
            <div className="shrink-0 border-t border-surface-700/50 p-3">
              <div className="flex items-end gap-2 bg-surface-800 border border-surface-700 rounded-2xl px-4 py-2.5 focus-within:border-primary-500 transition-colors">
                <textarea value={input} onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
                  disabled={loading} rows={1}
                  placeholder="ถามเกี่ยวกับการเทรด… (Enter ส่ง)"
                  className="flex-1 bg-transparent text-sm text-surface-100 placeholder-surface-500 outline-none resize-none leading-relaxed"
                  style={{ maxHeight: 100 }}/>
                {messages.length > 0 && (
                  <button onClick={() => setMessages([])} className="text-surface-500 hover:text-surface-300 shrink-0 self-center">✕</button>
                )}
                <button onClick={() => send()} disabled={!input.trim() || loading}
                  className="w-8 h-8 rounded-xl bg-primary-600 hover:bg-primary-500 disabled:opacity-40 flex items-center justify-center transition-all shrink-0 self-center">
                  {loading ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/> : '→'}
                </button>
              </div>
            </div>
          </>
        )}

        {/* Benchmark Tab */}
        {tab === 'benchmark' && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="glass p-4 space-y-3">
              <textarea value={benchQ} onChange={e => setBenchQ(e.target.value)} rows={2}
                placeholder="พิมพ์คำถามแล้วกด Run Benchmark — ส่งถาม OpenAI, Claude, Built-in พร้อมกัน"
                className="input-base resize-none"/>
              <div className="flex flex-wrap items-center gap-2">
                {['RSI คืออะไร?','Kelly Criterion คืออะไร?','Stop Loss วางที่ไหน?'].map(q => (
                  <button key={q} onClick={() => setBenchQ(q)}
                    className="px-2.5 py-1 text-xs bg-surface-800 text-surface-400 hover:bg-primary-600/15 hover:text-primary-300 border border-surface-700/30 rounded-full transition-all">{q}</button>
                ))}
                <button onClick={runBenchmark} disabled={!benchQ.trim() || benchLoading}
                  className="btn-primary ml-auto flex items-center gap-2 text-sm">
                  {benchLoading ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>Running…</> : '⚡ Run All'}
                </button>
              </div>
            </div>
            {benchLoading && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {[0,1,2].map(i => <div key={i} className="glass rounded-2xl p-4 h-48 animate-skeleton"/>)}
              </div>
            )}
            {benchResults.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {benchResults.map(r => (
                  <div key={r.provider} className={clsx('glass rounded-2xl flex flex-col overflow-hidden', !r.available && 'opacity-50')}>
                    <div className={clsx('px-4 py-3 border-b flex items-center gap-2',
                      r.provider==='openai' ? 'bg-[#10a37f]/10 border-[#10a37f]/20' :
                      r.provider==='anthropic' ? 'bg-[#cc785c]/10 border-[#cc785c]/20' : 'bg-primary-600/10 border-primary-600/20')}>
                      <span className="text-xl">{provIcon(r.provider)}</span>
                      <div>
                        <p className="text-xs font-bold text-surface-100">{provLabel(r.provider)}</p>
                        <p className="text-xs text-surface-500">{r.model ?? 'built-in'} · {r.latency_ms}ms</p>
                      </div>
                    </div>
                    <div className="flex-1 p-4 overflow-y-auto max-h-80">
                      {r.error ? <p className="text-sm text-bear">⚠️ {r.error}</p>
                        : r.content ? <div className="text-sm text-surface-200 leading-relaxed" dangerouslySetInnerHTML={{ __html: md(r.content) }}/>
                        : <p className="text-sm text-surface-500 italic">ไม่มีคำตอบ</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
