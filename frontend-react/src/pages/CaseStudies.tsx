import { Link } from 'react-router-dom'
import { useSEO, breadcrumbSchema } from '@/hooks/useSEO'
import Breadcrumbs from '@/components/shared/Breadcrumbs'
import { REVIEWS } from './About'

const CASES = [
  {
    title:    'SMA Crossover — SP100 ปี 2004-2024',
    category: 'Backtest',
    summary:  'ทดสอบ SMA 20/50 Crossover บน SP100 20 ปี เทียบกับ Buy & Hold',
    results:  [{ label:'CAGR', value:'12.4%', pos:true },{ label:'Sharpe', value:'0.92', pos:true },{ label:'Max DD', value:'-28%', pos:false },{ label:'Win Rate', value:'54%', pos:true }],
    insight:  'SMA Crossover ให้ CAGR ใกล้เคียง Buy & Hold แต่ Max Drawdown น้อยกว่ามาก (-28% vs -55%) เหมาะสำหรับนักลงทุนที่รับความเสี่ยงต่ำ',
    link:     '/backtest',
    icon:     '📈',
  },
  {
    title:    'Bubble Detection — NVDA 2023-2024',
    category: 'Bubble Analysis',
    summary:  'วิเคราะห์ Speculative Bubble ของ NVDA หลัง AI boom 2023',
    results:  [{ label:'Bubble Score', value:'78/100', pos:false },{ label:'Z-Score', value:'3.2σ', pos:false },{ label:'Crash Prob', value:'68%', pos:false },{ label:'Signals', value:'4/4 🔴', pos:false }],
    insight:  'ระบบตรวจจับ super-exponential growth ใน NVDA ตั้งแต่ต้นปี 2024 — log-price acceleration เกิน threshold, Z-score เกิน 3σ จาก historical mean',
    link:     '/bubble',
    icon:     '🔥',
  },
  {
    title:    'Mean Reversion Edge — SPY Z-Score Strategy',
    category: 'Edge Trading',
    summary:  'สถิติย้อนหลัง 20 ปี: เมื่อ SPY Z-score < -2.0 โอกาสกลับมาใน 5 วัน',
    results:  [{ label:'Win Rate', value:'72%', pos:true },{ label:'EV/trade', value:'+0.8%', pos:true },{ label:'Half-Kelly', value:'14%', pos:true },{ label:'Signals', value:'47 ครั้ง', pos:true }],
    insight:  'จาก 47 ครั้งที่ SPY Z-score ต่ำกว่า -2.0 ใน 20 ปี ชนะ 72% โดย average win +1.6% average loss -0.9% รวม EV เป็นบวกชัดเจน',
    link:     '/trade',
    icon:     '🎯',
  },
  {
    title:    'Bayesian Regime Detection — 2022 Bear Market',
    category: 'Stats Hub',
    summary:  'HMM 3-state Model ตรวจจับ Bear Regime ปี 2022 ได้แม่นขนาดไหน',
    results:  [{ label:'Bull %', value:'58%', pos:true },{ label:'Bear %', value:'29%', pos:false },{ label:'Sideways %', value:'13%', pos:true },{ label:'Accuracy', value:'89%', pos:true }],
    insight:  'HMM Model สามารถ detect ช่วง Bear Market 2022 ได้ล่วงหน้า 2-3 สัปดาห์ โดย Bayesian posterior P(Bear) เกิน 70% ก่อน SPY ลงจุดสูงสุด',
    link:     '/stats-hub',
    icon:     '🔬',
  },
  {
    title:    'Monte Carlo — SPY 1-Year Forecast 10,000 Paths',
    category: 'Monte Carlo',
    summary:  'Bootstrap simulation 10,000 paths บน SPY ข้อมูล 10 ปี',
    results:  [{ label:'P50 (Median)', value:'1.12x', pos:true },{ label:'P5 (Worst 5%)', value:'0.78x', pos:false },{ label:'P95 (Best 5%)', value:'1.54x', pos:true },{ label:'P(Loss)', value:'22%', pos:false }],
    insight:  'จาก historical distribution 10 ปี — 78% โอกาสได้กำไรใน 1 ปี, P50 ที่ 12% return, worst case P5 ขาดทุน 22% ใช้วางแผน position sizing ได้จริง',
    link:     '/monte-carlo',
    icon:     '🎲',
  },
]

export default function CaseStudies() {
  useSEO({
    title: 'Case Studies — ผลการวิเคราะห์จริง',
    description: 'Case Studies จาก QuantDash — SMA Crossover 20 ปี, Bubble Detection NVDA, Mean Reversion Edge, Bayesian Regime, Monte Carlo SPY',
    schema: breadcrumbSchema([{name:'Home',url:'/'},{name:'Case Studies',url:'/case-studies'}]),
  })

  return (
    <div className="max-w-5xl mx-auto space-y-10 py-8 animate-fade-in">
      <Breadcrumbs/>

      <div className="text-center space-y-3">
        <h1 className="text-3xl font-black text-surface-100">Case Studies</h1>
        <p className="text-surface-400 max-w-xl mx-auto">ผลการวิเคราะห์จริงจากข้อมูลตลาดย้อนหลัง 20 ปี — ทุก case ทำซ้ำได้ใน QuantDash</p>
      </div>

      {/* CTA above the fold */}
      <div className="glass border border-primary-600/20 rounded-2xl p-5 flex flex-col sm:flex-row items-center gap-4">
        <div className="flex-1">
          <p className="font-semibold text-surface-100">ทำซ้ำ case เหล่านี้ด้วยตัวเอง</p>
          <p className="text-sm text-surface-400">ข้อมูล 20 ปี · ฟรี · ไม่ต้อง API key · ผล realtime</p>
        </div>
        <Link to="/register" className="btn-primary shrink-0">เริ่มเลย →</Link>
      </div>

      {/* Cases */}
      <div className="space-y-6">
        {CASES.map((c, i) => (
          <article key={i} className="glass rounded-2xl p-6 space-y-4">
            <div className="flex items-start gap-4">
              <div
                role="img"
                aria-label={`ไอคอน ${c.category}`}
                className="w-12 h-12 rounded-xl bg-primary-600/15 flex items-center justify-center text-2xl shrink-0">
                {c.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="badge badge-blue">{c.category}</span>
                </div>
                <h2 className="text-lg font-bold text-surface-100">{c.title}</h2>
                <p className="text-sm text-surface-400 mt-0.5">{c.summary}</p>
              </div>
            </div>

            {/* Results grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {c.results.map(r => (
                <div key={r.label} className={`glass p-3 text-center rounded-xl border ${r.pos ? 'border-bull/20' : 'border-bear/20'}`}>
                  <p className="text-xs text-surface-400">{r.label}</p>
                  <p className={`text-lg font-bold mt-0.5 ${r.pos ? 'text-bull' : 'text-bear'}`}>{r.value}</p>
                </div>
              ))}
            </div>

            {/* Insight */}
            <div className="bg-primary-600/5 border border-primary-600/15 rounded-xl p-4">
              <p className="text-sm text-surface-300 leading-relaxed">
                <span className="text-primary-400 font-semibold">💡 Insight: </span>{c.insight}
              </p>
            </div>

            <Link to={c.link} className="inline-flex items-center gap-1.5 text-sm text-primary-400 hover:text-primary-300 font-medium transition-colors">
              ลองด้วยตัวเอง →
            </Link>
          </article>
        ))}
      </div>

      {/* Reviews section */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-surface-100">สิ่งที่ผู้ใช้พูดถึง</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {REVIEWS.slice(0,4).map((r,i)=>(
            <div key={i} className="glass rounded-xl p-4 space-y-2">
              <p className="text-sm text-surface-300 leading-relaxed">"{r.text}"</p>
              <div className="flex items-center justify-between">
                <div><p className="text-xs font-semibold text-surface-200">{r.name}</p><p className="text-xs text-surface-500">{r.role}</p></div>
                <span className="text-yellow-400 text-xs">{'★'.repeat(r.rating)}</span>
              </div>
            </div>
          ))}
        </div>
        <Link to="/about#reviews" className="text-sm text-primary-400 hover:underline">ดูรีวิวทั้งหมด →</Link>
      </section>

      {/* Internal links */}
      <div className="glass rounded-2xl p-5">
        <p className="text-sm font-semibold text-surface-200 mb-3">สำรวจฟีเจอร์อื่น</p>
        <div className="flex flex-wrap gap-2">
          {[{h:'/about',l:'เกี่ยวกับเรา'},{h:'/faq',l:'FAQ'},{h:'/backtest',l:'Backtest Lab'},{h:'/bubble',l:'Bubble Detection'},{h:'/trade',l:'Edge Trading'},{h:'/ai',l:'QuantAI'}].map(l=>(
            <Link key={l.h} to={l.h} className="text-xs text-primary-400 hover:underline px-2 py-0.5 bg-primary-600/10 rounded-full">{l.l}</Link>
          ))}
        </div>
      </div>
    </div>
  )
}
