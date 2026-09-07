import { Link } from 'react-router-dom'
export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-5 animate-fade-in text-center">
      <div className="relative">
        <span className="text-[120px] font-black text-surface-800 select-none leading-none">404</span>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-5xl">📉</span>
        </div>
      </div>
      <div>
        <h1 className="text-2xl font-bold text-surface-100">Page Not Found</h1>
        <p className="text-surface-400 text-sm mt-1">หน้าที่คุณหาไม่มีในระบบ</p>
      </div>
      <Link to="/dashboard" className="btn-primary px-6 py-2.5">← กลับ Dashboard</Link>
    </div>
  )
}
