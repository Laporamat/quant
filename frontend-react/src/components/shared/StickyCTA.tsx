import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

/** Sticky bottom CTA bar — shown on mobile when user is NOT logged in */
export default function StickyCTA() {
  const auth    = useAuthStore()
  const [show,  setShow]  = useState(false)
  const [closed,setClosed]= useState(false)

  // Appear after 3 s scroll
  useEffect(() => {
    const t = setTimeout(() => setShow(true), 3000)
    return () => clearTimeout(t)
  }, [])

  if (auth.isLoggedIn || closed || !show) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 lg:hidden animate-slide-up">
      <div className="bg-surface-900 border-t border-surface-700/50 px-4 py-3 flex items-center gap-3 shadow-card-lg">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-surface-100">เริ่มวิเคราะห์หุ้นฟรี</p>
          <p className="text-xs text-surface-400 truncate">ข้อมูล 20 ปี · OCaml Engine · ไม่ต้อง API key</p>
        </div>
        <Link to="/register" className="btn-primary text-sm px-4 py-2 shrink-0">เริ่มเลย →</Link>
        <button onClick={() => setClosed(true)} className="text-surface-500 hover:text-surface-300 shrink-0" aria-label="Close">✕</button>
      </div>
    </div>
  )
}
