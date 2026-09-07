import { useState, useEffect, useMemo } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useToastStore } from '@/store/appStore'
import clsx from 'clsx'

function pwdStrength(p: string) {
  let s = 0
  if (p.length >= 8)  s++
  if (p.length >= 12) s++
  if (/[A-Z]/.test(p) && /[a-z]/.test(p)) s++
  if (/\d/.test(p))   s++
  if (/[^a-zA-Z0-9]/.test(p)) s = Math.min(4, s + 1)
  const labels = ['', 'อ่อนมาก', 'อ่อน', 'ปานกลาง', 'แข็งแกร่ง']
  const colors = ['', 'bg-bear', 'bg-side', 'bg-side', 'bg-bull']
  return { score: Math.min(4, s), label: labels[Math.min(4, s)], color: colors[Math.min(4, s)] }
}

export default function Register() {
  const nav   = useNavigate()
  const auth  = useAuthStore()
  const toast = useToastStore()

  const [form, setForm] = useState({ email:'', username:'', display_name:'', password:'', confirm:'' , agree:false })
  const [showPwd, setShowPwd] = useState(false)
  const [error, setError]     = useState('')
  const [pwdErrors, setPwdErrors] = useState<string[]>([])

  const strength = useMemo(() => pwdStrength(form.password), [form.password])

  useEffect(() => { if (auth.isLoggedIn) nav('/dashboard') }, [auth.isLoggedIn])

  function set(k: string, v: string | boolean) { setForm(f => ({ ...f, [k]: v })) }

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError(''); setPwdErrors([])

    if (!/^[^@]+@[^@]+\.[^@]+$/.test(form.email))   { setError('รูปแบบอีเมลไม่ถูกต้อง'); return }
    if (form.username.length < 3)                     { setError('ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร'); return }
    if (!/^[a-zA-Z0-9_\-]+$/.test(form.username))    { setError('ชื่อผู้ใช้ใช้ได้เฉพาะ a-z 0-9 _ -'); return }
    if (form.password.length < 8)                     { setError('รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร'); return }
    if (form.password !== form.confirm)               { setError('รหัสผ่านไม่ตรงกัน'); return }
    if (!form.agree)                                  { setError('กรุณายอมรับข้อกำหนด'); return }

    const r = await auth.register(form.email, form.username, form.password, form.display_name || undefined)
    if (r.ok) {
      toast.success(`ยินดีต้อนรับ ${auth.displayName}! 🎉`)
      nav('/dashboard')
    } else {
      const d = r.error as any
      if (typeof d === 'object' && d?.errors) { setError(d.message || 'รหัสผ่านไม่ผ่าน'); setPwdErrors(d.errors) }
      else setError(String(d))
    }
  }

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-primary-600/8 blur-3xl"/>
        <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-accent-600/8 blur-3xl"/>
      </div>

      <div className="relative w-full max-w-md animate-slide-up">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="3 17 9 11 13 15 21 7" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="text-xl font-bold text-surface-100">QuantDash</span>
          </Link>
        </div>

        <div className="glass rounded-2xl p-8 shadow-card-lg border border-surface-700/50">
          <h1 className="text-xl font-bold text-surface-100 mb-1">สมัครสมาชิก</h1>
          <p className="text-sm text-surface-400 mb-6">
            มีบัญชีแล้ว?{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium">เข้าสู่ระบบ</Link>
          </p>

          {error && (
            <div className="px-4 py-3 rounded-xl bg-bear/10 border border-bear/30 mb-5 text-sm text-bear animate-fade-in">
              <p>{error}</p>
              {pwdErrors.length > 0 && (
                <ul className="list-disc list-inside mt-1 space-y-0.5">
                  {pwdErrors.map(e => <li key={e} className="text-xs">{e}</li>)}
                </ul>
              )}
            </div>
          )}

          <form onSubmit={submit} className="space-y-3.5" noValidate>
            {/* Display name */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-surface-300">ชื่อที่แสดง <span className="text-surface-500">(ไม่บังคับ)</span></label>
              <input type="text" maxLength={64} value={form.display_name}
                onChange={e => set('display_name', e.target.value)}
                placeholder="ชื่อ Trader ของคุณ" className="input-base"/>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-surface-300">อีเมล <span className="text-bear">*</span></label>
              <input type="email" autoComplete="email" required value={form.email}
                onChange={e => set('email', e.target.value)}
                placeholder="email@example.com" className="input-base"/>
            </div>

            {/* Username */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-surface-300">ชื่อผู้ใช้ <span className="text-bear">*</span></label>
              <input type="text" autoComplete="username" required
                minLength={3} maxLength={32} value={form.username}
                onChange={e => set('username', e.target.value)}
                placeholder="trader_username" className="input-base"/>
              <p className="text-xs text-surface-500">3–32 ตัวอักษร a-z 0-9 _ -</p>
            </div>

            {/* Password */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-surface-300">รหัสผ่าน <span className="text-bear">*</span></label>
              <div className="relative">
                <input type={showPwd ? 'text' : 'password'} autoComplete="new-password" required
                  value={form.password} onChange={e => set('password', e.target.value)}
                  placeholder="••••••••" className="input-base pr-10"/>
                <button type="button" onClick={() => setShowPwd(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300">
                  {showPwd ? '🙈' : '👁'}
                </button>
              </div>
              {form.password && (
                <div className="space-y-1">
                  <div className="flex gap-1">
                    {[1,2,3,4].map(i => (
                      <div key={i} className={clsx('flex-1 h-1 rounded-full transition-all',
                        i <= strength.score ? strength.color : 'bg-surface-700')}/>
                    ))}
                  </div>
                  <p className={clsx('text-xs', strength.score <= 1 ? 'text-bear' : strength.score <= 2 ? 'text-side' : 'text-bull')}>
                    {strength.label}
                  </p>
                </div>
              )}
            </div>

            {/* Confirm */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-surface-300">ยืนยันรหัสผ่าน <span className="text-bear">*</span></label>
              <input type={showPwd ? 'text' : 'password'} autoComplete="new-password" required
                value={form.confirm} onChange={e => set('confirm', e.target.value)}
                placeholder="••••••••"
                className={clsx('input-base', form.confirm && form.confirm !== form.password && 'border-bear/60')}/>
              {form.confirm && form.confirm !== form.password && (
                <p className="text-xs text-bear">รหัสผ่านไม่ตรงกัน</p>
              )}
            </div>

            {/* Terms */}
            <label className="flex items-start gap-2.5 cursor-pointer">
              <input type="checkbox" checked={form.agree} onChange={e => set('agree', e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded accent-primary-500 shrink-0"/>
              <span className="text-xs text-surface-400 leading-snug">
                ยอมรับ <a href="#" className="text-primary-400 hover:underline">ข้อกำหนดการใช้งาน</a> และ{' '}
                <a href="#" className="text-primary-400 hover:underline">นโยบายความเป็นส่วนตัว</a>
              </span>
            </label>

            <button type="submit" disabled={auth.loading}
              className={clsx('w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-semibold text-sm transition-all',
                auth.loading ? 'bg-primary-600/50 text-white/50 cursor-not-allowed' : 'btn-primary shadow-glow')}>
              {auth.loading
                ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>กำลังสมัคร…</>
                : 'สมัครสมาชิก'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-surface-600 mt-5">🔒 bcrypt-12 · JWT HS256 · ข้อมูลเข้ารหัส</p>
      </div>
    </div>
  )
}
