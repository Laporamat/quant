import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useToastStore } from '@/store/appStore'
import clsx from 'clsx'

export default function Login() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const auth = useAuthStore()
  const toast = useToastStore()

  const [form, setForm] = useState({ login: '', password: '' })
  const [showPwd, setShowPwd] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { if (auth.isLoggedIn) nav(params.get('redirect') || '/dashboard') }, [auth.isLoggedIn])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!form.login.trim()) { setError('กรุณากรอกอีเมลหรือชื่อผู้ใช้'); return }
    if (!form.password)     { setError('กรุณากรอกรหัสผ่าน'); return }
    const r = await auth.login(form.login.trim(), form.password)
    if (r.ok) {
      toast.success(`ยินดีต้อนรับกลับ ${auth.displayName}!`)
      nav(params.get('redirect') || '/dashboard')
    } else {
      setError(r.error || 'เข้าสู่ระบบไม่สำเร็จ')
    }
  }

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary-600/8 blur-3xl"/>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-accent-600/8 blur-3xl"/>
      </div>

      <div className="relative w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="3 17 9 11 13 15 21 7" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="text-xl font-bold text-surface-100">QuantDash</span>
          </Link>
          <p className="text-surface-400 text-sm mt-2">Quantitative Trading Platform</p>
          <p className="text-surface-500 text-xs mt-1">
            OCaml Engine · Python Analytics · React UI
          </p>
        </div>

        <div className="glass rounded-2xl p-8 shadow-card-lg border border-surface-700/50">
          <h1 className="text-xl font-bold text-surface-100 mb-1">เข้าสู่ระบบ</h1>
          <p className="text-sm text-surface-400 mb-6">
            ยังไม่มีบัญชี?{' '}
            <Link to="/register" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
              สมัครสมาชิก
            </Link>
          </p>

          {error && (
            <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-bear/10 border border-bear/30 mb-5 text-sm text-bear animate-fade-in">
              <span className="shrink-0">⚠</span> {error}
            </div>
          )}

          <form onSubmit={submit} className="space-y-4" noValidate>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-surface-300">อีเมล หรือ ชื่อผู้ใช้</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500 text-sm">👤</span>
                <input
                  type="text" autoComplete="username" required
                  value={form.login} onChange={e => setForm(f => ({ ...f, login: e.target.value }))}
                  placeholder="email@example.com หรือ username"
                  className="input-base pl-9"/>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between">
                <label className="text-xs font-medium text-surface-300">รหัสผ่าน</label>
                <button type="button" className="text-xs text-primary-400 hover:text-primary-300">ลืมรหัสผ่าน?</button>
              </div>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500 text-sm">🔒</span>
                <input
                  type={showPwd ? 'text' : 'password'} autoComplete="current-password" required
                  value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  placeholder="••••••••"
                  className="input-base pl-9 pr-10"/>
                <button type="button" onClick={() => setShowPwd(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300">
                  {showPwd ? '🙈' : '👁'}
                </button>
              </div>
            </div>

            <button type="submit" disabled={auth.loading}
              className={clsx('w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-semibold text-sm transition-all mt-2',
                auth.loading ? 'bg-primary-600/50 text-white/50 cursor-not-allowed' : 'btn-primary shadow-glow')}>
              {auth.loading
                ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>กำลังเข้าสู่ระบบ…</>
                : 'เข้าสู่ระบบ'}
            </button>
          </form>

          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-surface-700"/><span className="text-xs text-surface-500">หรือ</span><div className="flex-1 h-px bg-surface-700"/>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {[{icon:'🟦',name:'Google'},{icon:'⬛',name:'GitHub'}].map(p => (
              <button key={p.name} disabled
                className="flex items-center justify-center gap-2 py-2 rounded-xl border bg-surface-800/30 border-surface-700/20 text-surface-600 text-sm cursor-not-allowed">
                {p.icon} {p.name}
              </button>
            ))}
          </div>
        </div>

        <p className="text-center text-xs text-surface-600 mt-5 flex items-center justify-center gap-1.5">
          🔒 bcrypt-12 · JWT HS256 · ข้อมูลเข้ารหัส
        </p>
      </div>
    </div>
  )
}
