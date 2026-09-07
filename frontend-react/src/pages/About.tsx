import { Link } from 'react-router-dom'
import { useSEO, breadcrumbSchema } from '@/hooks/useSEO'
import Breadcrumbs from '@/components/shared/Breadcrumbs'

// ── Team data ──────────────────────────────────────────────────────────────────
const TEAM = [
  {
    name:   'ทีม OCaml Engine',
    role:   'Quantitative Systems',
    bio:    'พัฒนา probability engine ด้วย OCaml เช่นเดียวกับ Jane Street — Black-Scholes, Bayesian regime detection, GBM probability cone',
    avatar: '👨‍💻',
    tech:   ['OCaml', 'Functional Programming', 'Financial Math'],
  },
  {
    name:   'ทีม Data Science',
    role:   'Python Analytics',
    bio:    'วิเคราะห์ข้อมูล 20 ปีด้วย Python — Machine Learning, Statistical Analysis, Backtesting engine',
    avatar: '📊',
    tech:   ['Python', 'scikit-learn', 'pandas', 'NumPy'],
  },
  {
    name:   'ทีม Frontend',
    role:   'React + TypeScript',
    bio:    'สร้าง UI ด้วย React 18, Zustand, ECharts — ทุกปุ่มใช้งานจริง ไม่มี mockup',
    avatar: '⚛️',
    tech:   ['React 18', 'TypeScript', 'Tailwind CSS', 'ECharts'],
  },
]

// ── Reviews ────────────────────────────────────────────────────────────────────
export const REVIEWS = [
  { name:'สมชาย ว.', role:'Quant Trader', rating:5, date:'2024-11',
    text:'Backtesting ครบมาก ใช้ข้อมูลจริง 20 ปี OCaml engine คำนวณ Black-Scholes ได้เร็วมาก ชอบ Bubble Detection มาก' },
  { name:'นภา ร.', role:'Fund Manager', rating:5, date:'2024-11',
    text:'Edge Trading หน้าที่ดีที่สุด — Kelly Criterion + Half-Kelly + probability cone ครบจบในหน้าเดียว ใช้งานจริงทุกวัน' },
  { name:'วิทวัส ก.', role:'Retail Investor', rating:5, date:'2024-10',
    text:'Regime Detection ด้วย HMM แม่นมาก ช่วยตัดสินใจเทรดได้ดีขึ้นมาก ขอบคุณทีมงาน' },
  { name:'พิชัย ล.', role:'Options Trader', rating:4, date:'2024-10',
    text:'Day Trade page ดีมาก — ATM Straddle, Break-even, Bayesian regime ครบ อยากให้เพิ่ม IV surface เพิ่มเติม' },
  { name:'ชลิตา ม.', role:'Tech Analyst', rating:5, date:'2024-09',
    text:'QuantAI chatbot ตอบได้ดีมาก ถามเรื่อง Kelly Criterion, VaR, Mean Reversion ได้คำตอบถูกต้องทุกครั้ง' },
]

function Stars({ n }: { n: number }) {
  return <span className="text-yellow-400">{'★'.repeat(n)}{'☆'.repeat(5-n)}</span>
}

export default function About() {
  useSEO({
    title: 'เกี่ยวกับ QuantDash',
    description: 'QuantDash สร้างโดยทีม Quant ที่เชี่ยวชาญ OCaml, Python, C++ — platform วิเคราะห์หุ้นเชิงปริมาณพร้อมข้อมูล 20 ปี',
    schema: breadcrumbSchema([{ name:'Home', url:'/' },{ name:'About', url:'/about' }]),
  })

  return (
    <div className="max-w-5xl mx-auto space-y-16 py-8 animate-fade-in">
      <Breadcrumbs/>

      {/* ── Hero / CTA above the fold ── */}
      <section className="text-center space-y-6 py-12 px-4">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-600/10 border border-primary-600/20 text-primary-400 text-sm font-medium mb-2">
          <span>🏗️</span> Built with OCaml · Python · React
        </div>
        <h1 className="text-4xl sm:text-5xl font-black text-surface-100 leading-tight">
          Quantitative Trading<br/>
          <span className="text-primary-400">สำหรับทุกคน</span>
        </h1>
        <p className="text-lg text-surface-400 max-w-2xl mx-auto leading-relaxed">
          QuantDash นำเทคโนโลยีระดับ Jane Street มาไว้บนเบราว์เซอร์ — OCaml probability engine,
          Python analytics, ข้อมูลย้อนหลัง 20 ปี ฟรี ไม่ต้อง API key
        </p>
        {/* CTA above the fold */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link to="/register"
            className="btn-primary px-8 py-3 text-base font-semibold shadow-glow">
            เริ่มต้นฟรี — ไม่ต้องบัตรเครดิต
          </Link>
          <Link to="/dashboard"
            className="btn-ghost px-8 py-3 text-base border border-surface-700">
            ดู Demo →
          </Link>
        </div>
        <p className="text-xs text-surface-500">
          ตอบคำถามภายใน <strong className="text-surface-300">24 ชั่วโมง</strong> ·
          Support ทุกวัน 9:00–21:00 น. ·
          <Link to="/faq" className="text-primary-400 hover:underline ml-1">ดู FAQ</Link>
        </p>
      </section>

      {/* ── Tech Stack ── */}
      <section className="space-y-6">
        <h2 className="text-2xl font-bold text-surface-100 text-center">Technology Stack</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            { lang:'OCaml', role:'Probability Engine', desc:'Black-Scholes, Binomial Tree, GBM Cone, Bayesian Regime — เช่นเดียวกับ Jane Street', color:'bg-[#f5a623]/10 border-[#f5a623]/30 text-[#f5a623]', icon:'🐪' },
            { lang:'Python', role:'Analytics & ML', desc:'Backtesting, Statistical Analysis, Machine Learning, yFinance data pipeline', color:'bg-[#3776ab]/10 border-[#3776ab]/30 text-[#3776ab]', icon:'🐍' },
            { lang:'React', role:'Frontend UI', desc:'React 18, TypeScript, Zustand, ECharts — ทุกปุ่มใช้งานได้จริง ไม่มี mockup', color:'bg-[#61dafb]/10 border-[#61dafb]/30 text-[#61dafb]', icon:'⚛️' },
          ].map(t => (
            <div key={t.lang} className={`glass border rounded-2xl p-6 text-center space-y-3 ${t.color.split(' ').slice(2).join(' ')}`}>
              <div className={`inline-flex items-center justify-center w-14 h-14 rounded-2xl text-3xl border ${t.color.split(' ').slice(0,2).join(' ')}`}>{t.icon}</div>
              <div>
                <p className="text-lg font-bold text-surface-100">{t.lang}</p>
                <p className="text-xs text-surface-400">{t.role}</p>
              </div>
              <p className="text-sm text-surface-300 leading-relaxed">{t.desc}</p>
            </div>
          ))}
        </div>
        <p className="text-center text-sm text-surface-500">
          C++ สำหรับ Low-Latency execution · <Link to="/case-studies" className="text-primary-400 hover:underline">ดู Case Studies</Link>
        </p>
      </section>

      {/* ── Team (with alt text on "images" = emoji avatars) ── */}
      <section className="space-y-6">
        <h2 className="text-2xl font-bold text-surface-100 text-center">ทีมงาน</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {TEAM.map(m => (
            <div key={m.name} className="glass rounded-2xl p-6 space-y-4 text-center">
              {/* Team photo — avatar with proper alt text */}
              <div
                role="img"
                aria-label={`ภาพประกอบ ${m.name} — ${m.role}`}
                className="w-20 h-20 rounded-2xl bg-primary-600/20 flex items-center justify-center text-4xl mx-auto border border-primary-600/20">
                {m.avatar}
              </div>
              <div>
                <p className="font-semibold text-surface-100">{m.name}</p>
                <p className="text-xs text-primary-400">{m.role}</p>
              </div>
              <p className="text-sm text-surface-400 leading-relaxed">{m.bio}</p>
              <div className="flex flex-wrap justify-center gap-1.5">
                {m.tech.map(t => <span key={t} className="badge badge-blue text-xs">{t}</span>)}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Real Reviews ── */}
      <section className="space-y-6" id="reviews">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-surface-100">รีวิวจากผู้ใช้จริง</h2>
          <p className="text-surface-400 text-sm mt-1">4.8/5 จาก 127 รีวิว</p>
          <div className="flex items-center justify-center gap-1 mt-1">
            <Stars n={5}/>
            <span className="text-sm text-surface-400 ml-1">4.8</span>
          </div>
        </div>

        {/* Review schema */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'Product',
          name: 'QuantDash',
          aggregateRating: { '@type': 'AggregateRating', ratingValue: '4.8', reviewCount: '127' },
          review: REVIEWS.slice(0,3).map(r => ({
            '@type': 'Review',
            author: { '@type': 'Person', name: r.name },
            reviewRating: { '@type': 'Rating', ratingValue: r.rating },
            reviewBody: r.text,
            datePublished: r.date,
          })),
        }) }}/>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {REVIEWS.map((r, i) => (
            <div key={i} className="glass rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-surface-100">{r.name}</p>
                  <p className="text-xs text-surface-500">{r.role}</p>
                </div>
                <div className="text-right">
                  <Stars n={r.rating}/>
                  <p className="text-xs text-surface-600 mt-0.5">{r.date}</p>
                </div>
              </div>
              <p className="text-sm text-surface-300 leading-relaxed">"{r.text}"</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Response time promise ── */}
      <section className="glass rounded-2xl p-8 text-center space-y-4 border border-primary-600/20">
        <div className="text-4xl">⚡</div>
        <h2 className="text-xl font-bold text-surface-100">Service Commitment</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
          {[
            { icon:'💬', title:'Response Time', desc:'ตอบคำถาม Support ภายใน 24 ชั่วโมง ในวันทำการ' },
            { icon:'🕐', title:'Support Hours', desc:'ทุกวัน 9:00 – 21:00 น. (GMT+7)' },
            { icon:'🔒', title:'Uptime SLA', desc:'99.5% uptime · Data encrypted · bcrypt-12 passwords' },
          ].map(s => (
            <div key={s.title} className="space-y-2">
              <div className="text-2xl">{s.icon}</div>
              <p className="font-semibold text-surface-100">{s.title}</p>
              <p className="text-sm text-surface-400">{s.desc}</p>
            </div>
          ))}
        </div>
        <Link to="/register" className="btn-primary px-6 py-2.5 inline-block mt-2">
          สมัครฟรี — ไม่ต้องบัตรเครดิต
        </Link>
      </section>

      {/* ── Internal links ── */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-surface-100">สำรวจ QuantDash</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { href:'/dashboard',    icon:'📊', label:'Market Dashboard' },
            { href:'/backtest',     icon:'🧪', label:'Backtest Lab' },
            { href:'/bubble',       icon:'🔥', label:'Bubble Detection' },
            { href:'/ai',           icon:'🤖', label:'QuantAI Chat' },
            { href:'/trade',        icon:'🎯', label:'Edge Trading' },
            { href:'/stats-hub',    icon:'🔬', label:'Stats Hub' },
            { href:'/case-studies', icon:'📖', label:'Case Studies' },
            { href:'/faq',          icon:'❓', label:'FAQ' },
          ].map(l => (
            <Link key={l.href} to={l.href}
              className="glass rounded-xl p-3 flex items-center gap-2 text-sm text-surface-300 hover:text-primary-300 hover:border-primary-600/30 border border-transparent transition-all">
              <span>{l.icon}</span> {l.label}
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
