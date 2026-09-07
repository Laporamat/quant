import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSEO, breadcrumbSchema } from '@/hooks/useSEO'
import Breadcrumbs from '@/components/shared/Breadcrumbs'

const FAQS = [
  {
    q: 'QuantDash ใช้งานฟรีหรือเปล่า?',
    a: 'ฟรีทั้งหมดครับ — ดาวน์โหลดข้อมูลย้อนหลัง 20 ปีจาก Yahoo Finance ไม่มีค่าใช้จ่าย ไม่ต้องใช้ API key ภายนอก ทุกฟีเจอร์ (Backtest, OCaml Engine, AI Chat, Bubble Detection) ใช้งานได้ฟรีหลังสมัครสมาชิก',
  },
  {
    q: 'ข้อมูลมาจากไหน และแม่นยำแค่ไหน?',
    a: 'ข้อมูลราคาหุ้นมาจาก Yahoo Finance ผ่าน yfinance library (adjusted close, split & dividend adjusted) ย้อนหลัง 20 ปี ครอบคลุม SP100, SET50, Sector ETFs รวมกว่า 105 tickers ข้อมูลอัปเดตได้ตลอดเวลาผ่านหน้า Dashboard',
  },
  {
    q: 'OCaml Engine คืออะไร? ต่างจาก Python ยังไง?',
    a: 'OCaml เป็นภาษาที่ Jane Street ใช้เป็นหลักสำหรับ trading systems เนื่องจากความปลอดภัยของ type system และประสิทธิภาพสูง QuantDash implement Black-Scholes, Binomial CRR, Bayesian Regime Detection, GBM Probability Cone ด้วย OCaml algorithm เดียวกัน — แต่ run บน Python interpreter (port line-by-line) เพื่อให้ไม่ต้องติดตั้ง OCaml compiler ถ้ามี binary อยู่จะ delegate ไปให้ทันที',
  },
  {
    q: 'Backtest ใช้กลยุทธ์อะไรได้บ้าง?',
    a: 'ปัจจุบันรองรับ 10 กลยุทธ์: Buy & Hold, SMA Crossover, Momentum, Mean Reversion, Breakout, Pairs Trading, Multi-Factor, Volatility Targeting, Trend Following, และ Machine Learning Strategy คุณสามารถปรับ parameter, commission, slippage, position sizing (Equal/Vol-Target/Kelly) และดู equity curve, drawdown, monthly heatmap, trade log ได้ทันที',
  },
  {
    q: 'ข้อมูลส่วนตัวและรหัสผ่านปลอดภัยไหม?',
    a: 'ปลอดภัยมากครับ — รหัสผ่านเข้ารหัสด้วย bcrypt cost-12 (industry standard), JWT access token อายุ 15 นาที, refresh token เก็บเป็น SHA-256 hash, account lockout หลัง 5 ครั้งผิด (exponential backoff), security headers ครบ (CSP, X-Frame-Options, HSTS), ทุก event บันทึกใน audit log',
  },
  {
    q: 'Bubble Detection ทำงานอย่างไร?',
    a: 'QuantDash ใช้ 4 signal รวมกัน: (1) Log-price acceleration — วัด 2nd derivative ของ log price ถ้าเป็น super-exponential = สัญญาณ bubble, (2) Rolling Z-score — cumulative return 1Y vs historical distribution, (3) LPPL-inspired growth test, (4) Volatility regime spike นอกจากนี้ยังสแกน historical episodes ทั้งหมดในช่วงเวลาที่เลือกและระบุ known bubbles (Dot-com, GFC, COVID, etc.)',
  },
  {
    q: 'Edge Trading ต่างจาก Backtest ยังไง?',
    a: 'Backtest ทดสอบ strategy แบบ systematic โดยรันทุก signal ตามกฎ ส่วน Edge Trading คำนวณ statistical edge จากข้อมูลอดีตทั้งหมด — win rate, expected value, Kelly criterion, optimal position size — สำหรับ setup เฉพาะ (เช่น เมื่อ Z-score < -2 ใน 5 วัน ชนะกี่ %) เน้นกำไรน้อยแต่ต่อเนื่อง ขาดทุนน้อยที่สุด',
  },
  {
    q: 'QuantAI chatbot ใช้ AI อะไร?',
    a: 'QuantAI มี 3 layers: (1) Built-in knowledge base — 20+ หัวข้อ trading (RSI, MACD, Kelly, VaR, Backtest, จิตวิทยา) ตอบได้โดยไม่ต้อง API, (2) ถ้ามี OpenAI API key → ใช้ GPT-4o-mini, (3) ถ้ามี Anthropic key → ใช้ Claude 3 Haiku มี Benchmark mode ให้เปรียบเทียบคำตอบทั้ง 3 พร้อมกัน และ inject live market data (RSI, regime, Kelly) ของ ticker ที่เลือก',
  },
  {
    q: 'รองรับหุ้นไทย SET50 ไหม?',
    a: 'รองรับครับ — SET50 tickers (เช่น PTT.BK, KBANK.BK, AOT.BK) ดาวน์โหลดได้จาก Yahoo Finance ผ่าน quickstart script รัน python scripts/quickstart_download.py --universe set50 ในระบบ ทุกฟีเจอร์รองรับ SET50 เหมือนกับ SP100 ทั้งหมด',
  },
  {
    q: 'Monte Carlo Simulator ทำงานอย่างไร?',
    a: 'ใช้ 2 วิธี: (1) Bootstrap — สุ่ม return จาก historical distribution จริงของหุ้น (non-parametric, ไม่สมมุติ distribution), (2) Parametric — สร้าง path จาก GBM (Geometric Brownian Motion) ด้วย μ และ σ ที่คำนวณจาก historical data จากนั้นสร้าง 100-5,000 paths แสดง P5/P25/P50/P75/P95 percentile bands พร้อม probability of gain/loss',
  },
]

function FAQItem({ q, a, open, toggle }: { q:string; a:string; open:boolean; toggle:()=>void }) {
  return (
    <div className="border border-surface-700/50 rounded-xl overflow-hidden">
      <button
        onClick={toggle}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-surface-800/50 transition-colors"
        aria-expanded={open}>
        <span className="font-semibold text-surface-100 pr-4">{q}</span>
        <span className={`text-primary-400 transition-transform duration-200 shrink-0 ${open ? 'rotate-180' : ''}`}>▼</span>
      </button>
      {open && (
        <div className="px-5 pb-4 text-sm text-surface-300 leading-relaxed border-t border-surface-700/30 pt-3">
          {a}
        </div>
      )}
    </div>
  )
}

export default function FAQ() {
  const [open, setOpen] = useState<number | null>(0)

  useSEO({
    title: 'คำถามที่พบบ่อย (FAQ)',
    description: 'ตอบทุกข้อสงสัยเกี่ยวกับ QuantDash — ข้อมูลมาจากไหน, OCaml คืออะไร, Backtest ทำงานอย่างไร, ปลอดภัยแค่ไหน',
    schema: {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: FAQS.map(f => ({
        '@type': 'Question',
        name: f.q,
        acceptedAnswer: { '@type': 'Answer', text: f.a },
      })),
    },
  })

  return (
    <div className="max-w-3xl mx-auto space-y-8 py-8 animate-fade-in">
      <Breadcrumbs/>

      <div className="text-center space-y-3">
        <h1 className="text-3xl font-black text-surface-100">คำถามที่พบบ่อย</h1>
        <p className="text-surface-400">ไม่เจอคำตอบ? <Link to="/about#reviews" className="text-primary-400 hover:underline">ติดต่อทีมงาน</Link> — ตอบภายใน 24 ชั่วโมง</p>
      </div>

      {/* CTA above the fold */}
      <div className="glass border border-primary-600/20 rounded-2xl p-5 flex flex-col sm:flex-row items-center gap-4">
        <div className="flex-1">
          <p className="font-semibold text-surface-100">พร้อมเริ่มต้นแล้ว?</p>
          <p className="text-sm text-surface-400">สมัครฟรี · ข้อมูล 20 ปี · ไม่ต้อง API key · ไม่ต้องบัตรเครดิต</p>
        </div>
        <Link to="/register" className="btn-primary shrink-0">เริ่มเลย →</Link>
      </div>

      <div className="space-y-3">
        {FAQS.map((f, i) => (
          <FAQItem key={i} q={f.q} a={f.a} open={open===i} toggle={() => setOpen(open===i ? null : i)}/>
        ))}
      </div>

      {/* Internal links */}
      <div className="glass rounded-2xl p-5 space-y-3">
        <p className="text-sm font-semibold text-surface-200">อ่านเพิ่มเติม</p>
        <div className="flex flex-wrap gap-2">
          {[{h:'/about',l:'เกี่ยวกับเรา'},{h:'/case-studies',l:'Case Studies'},{h:'/privacy',l:'Privacy Policy'},{h:'/backtest',l:'Backtest Lab'},{h:'/ai',l:'QuantAI Chat'}].map(l=>(
            <Link key={l.h} to={l.h} className="text-xs text-primary-400 hover:underline px-2 py-0.5 bg-primary-600/10 rounded-full">{l.l}</Link>
          ))}
        </div>
      </div>
    </div>
  )
}
