import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSEO } from '@/hooks/useSEO'
import { useAuthStore } from '@/store/authStore'

export default function ThankYou() {
  const auth = useAuthStore()
  const nav  = useNavigate()

  useSEO({
    title: 'ยินดีต้อนรับ! — QuantDash',
    description: 'ขอบคุณที่สมัครสมาชิก QuantDash เริ่มวิเคราะห์หุ้นด้วยข้อมูล 20 ปีได้เลย',
    noindex: true, // no need to index this page
  })

  // Auto redirect after 8s
  useEffect(() => {
    const t = setTimeout(() => nav('/dashboard'), 8000)
    return () => clearTimeout(t)
  }, [nav])

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center p-4">
      <div className="max-w-lg w-full text-center space-y-8 animate-slide-up">

        {/* Success icon */}
        <div
          role="img"
          aria-label="ยินดีต้อนรับสู่ QuantDash"
          className="w-20 h-20 rounded-2xl bg-bull/20 border border-bull/30 flex items-center justify-center text-4xl mx-auto">
          🎉
        </div>

        <div className="space-y-3">
          <h1 className="text-3xl font-black text-surface-100">
            ยินดีต้อนรับ{auth.user?.display_name ? `, ${auth.user.display_name}` : ''}!
          </h1>
          <p className="text-surface-400 leading-relaxed">
            บัญชีของคุณพร้อมแล้ว — เริ่มวิเคราะห์หุ้นด้วยข้อมูลย้อนหลัง 20 ปี
            OCaml Probability Engine และ AI Chat ได้เลย
          </p>
        </div>

        {/* Next steps */}
        <div className="glass rounded-2xl p-6 text-left space-y-4">
          <h2 className="text-sm font-semibold text-surface-200">Next Steps</h2>
          <div className="space-y-3">
            {[
              { n:'1', title:'ดาวน์โหลดข้อมูล', desc:'กด "Download Data" บน Dashboard เพื่อโหลด 37 tickers แรก (~5 นาที)', href:'/dashboard', cta:'ไป Dashboard' },
              { n:'2', title:'ลอง Backtest',     desc:'ทดสอบ SMA Crossover บน AAPL, MSFT ระหว่างปี 2018-2024', href:'/backtest', cta:'Backtest Lab' },
              { n:'3', title:'คุยกับ QuantAI',  desc:'ถามเรื่อง Kelly Criterion, VaR, Mean Reversion ได้เลย', href:'/ai', cta:'QuantAI Chat' },
            ].map(s=>(
              <div key={s.n} className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-primary-600 flex items-center justify-center text-xs font-bold text-white shrink-0 mt-0.5">{s.n}</span>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-surface-100">{s.title}</p>
                  <p className="text-xs text-surface-400 mt-0.5">{s.desc}</p>
                </div>
                <Link to={s.href} className="text-xs text-primary-400 hover:text-primary-300 shrink-0 self-center">{s.cta} →</Link>
              </div>
            ))}
          </div>
        </div>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link to="/dashboard" className="btn-primary px-6 py-2.5 shadow-glow">
            เริ่มต้น — ไป Dashboard
          </Link>
          <Link to="/case-studies" className="btn-ghost px-6 py-2.5 border border-surface-700">
            ดู Case Studies
          </Link>
        </div>

        <p className="text-xs text-surface-600">
          กำลัง redirect ไป Dashboard ใน 8 วินาที ·{' '}
          <Link to="/faq" className="text-primary-400 hover:underline">FAQ</Link> ·{' '}
          <Link to="/about" className="text-primary-400 hover:underline">About</Link>
        </p>
      </div>
    </div>
  )
}
