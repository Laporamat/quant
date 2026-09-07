import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { DataTable, SectionHeader } from '@/components/shared/ui'
import { useAuthStore } from '@/store/authStore'
import { useToastStore } from '@/store/appStore'
import { authApi } from '@/api/authApi'
import dayjs from 'dayjs'

export default function Profile() {
  const auth  = useAuthStore()
  const toast = useToastStore()
  const nav   = useNavigate()
  const [displayName, setDN]    = useState(auth.displayName)
  const [savingName,  setSN]    = useState(false)
  const [pwd,   setPwd]         = useState({ current:'', new:'', confirm:'' })
  const [pwdMsg, setPwdMsg]     = useState<{ok:boolean;text:string}|null>(null)
  const [savingPwd, setSP]      = useState(false)
  const [sessions,  setSessions]= useState<any[]>([])
  const [auditLogs, setAuditLogs]= useState<any[]>([])

  const auditCols = [
    { key:'event',      label:'Event' },
    { key:'ip_address', label:'IP' },
    { key:'created_at', label:'เวลา', format:(v:unknown) => dayjs(v as string).format('DD/MM/YY HH:mm') },
  ]

  useEffect(() => {
    authApi.sessions().then(r=>setSessions(r.data.sessions)).catch(()=>{})
    authApi.auditLog(20).then(r=>setAuditLogs(r.data.logs)).catch(()=>{})
  }, [])

  async function saveName() {
    setSN(true)
    await auth.updateProfile(displayName)
    setSN(false)
  }

  async function changePwd() {
    setPwdMsg(null)
    if (pwd.new !== pwd.confirm) { setPwdMsg({ ok:false, text:'รหัสผ่านไม่ตรงกัน' }); return }
    setSP(true)
    try {
      await authApi.changePassword(pwd.current, pwd.new)
      setPwdMsg({ ok:true, text:'เปลี่ยนรหัสผ่านสำเร็จ กรุณาเข้าสู่ระบบใหม่' })
      setPwd({ current:'', new:'', confirm:'' })
      setTimeout(() => { auth.logout(); nav('/login') }, 2000)
    } catch (e: any) {
      setPwdMsg({ ok:false, text: e.response?.data?.detail || 'เกิดข้อผิดพลาด' })
    } finally { setSP(false) }
  }

  async function revokeOne(id: string) {
    await authApi.revokeSession(id)
    setSessions(s=>s.filter(x=>x.id!==id))
    toast.success('ยกเลิก session แล้ว')
  }

  return (
    <div className="max-w-2xl mx-auto space-y-5 animate-fade-in">
      <SectionHeader title="โปรไฟล์ของฉัน" description="จัดการข้อมูลบัญชีและความปลอดภัย"/>

      {/* Profile */}
      <div className="glass p-6 space-y-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-primary-600/20 border border-primary-600/30 flex items-center justify-center text-2xl font-bold text-primary-300">
            {auth.displayName[0]?.toUpperCase()}
          </div>
          <div>
            <p className="font-semibold text-surface-100">{auth.displayName}</p>
            <p className="text-sm text-surface-400">{auth.user?.email}</p>
            <span className="badge badge-blue mt-1">{auth.user?.role}</span>
          </div>
        </div>
        <div className="space-y-2 pt-2 border-t border-surface-700/50">
          <label className="text-xs font-medium text-surface-300">ชื่อที่แสดง</label>
          <div className="flex gap-2">
            <input value={displayName} onChange={e=>setDN(e.target.value)} maxLength={64} className="flex-1 input-base"/>
            <button onClick={saveName} disabled={savingName} className="btn-primary text-sm px-4">{savingName?'…':'บันทึก'}</button>
          </div>
        </div>
      </div>

      {/* Change password */}
      <div className="glass p-6 space-y-4">
        <h3 className="text-sm font-semibold text-surface-200">เปลี่ยนรหัสผ่าน</h3>
        {pwdMsg && (
          <div className={`text-sm px-3 py-2 rounded-lg ${pwdMsg.ok?'bg-bull/10 text-bull':'bg-bear/10 text-bear'}`}>{pwdMsg.text}</div>
        )}
        {[{k:'current',l:'รหัสผ่านปัจจุบัน'},{k:'new',l:'รหัสผ่านใหม่'},{k:'confirm',l:'ยืนยันรหัสผ่านใหม่'}].map(f=>(
          <div key={f.k} className="space-y-1">
            <label className="text-xs text-surface-400">{f.l}</label>
            <input type="password" value={(pwd as any)[f.k]} onChange={e=>setPwd(p=>({...p,[f.k]:e.target.value}))} className="input-base"/>
          </div>
        ))}
        <button onClick={changePwd} disabled={savingPwd} className="btn-primary w-full">{savingPwd?'กำลังเปลี่ยน…':'เปลี่ยนรหัสผ่าน'}</button>
      </div>

      {/* Sessions */}
      <div className="glass p-6 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-surface-200">Sessions ที่ใช้งานอยู่</h3>
          <button onClick={()=>{ authApi.revokeAll(); setSessions([]); toast.success('ยกเลิกทั้งหมดแล้ว') }}
            className="text-xs text-bear hover:text-bear/80 transition-colors">ยกเลิกทั้งหมด</button>
        </div>
        {sessions.map(s=>(
          <div key={s.id} className="flex items-start justify-between py-2.5 border-b border-surface-700/30 last:border-0">
            <div>
              <p className="text-xs text-surface-200">{s.device_info||'Unknown device'}</p>
              <p className="text-xs text-surface-500 mt-0.5">IP: {s.ip_address} · {dayjs(s.last_used_at).format('DD/MM/YY HH:mm')}</p>
            </div>
            <button onClick={()=>revokeOne(s.id)} className="text-xs text-bear/70 hover:text-bear ml-4">ยกเลิก</button>
          </div>
        ))}
        {!sessions.length && <p className="text-xs text-surface-500 text-center py-3">ไม่พบ session</p>}
      </div>

      {/* Audit */}
      <div className="glass p-6 space-y-3">
        <h3 className="text-sm font-semibold text-surface-200">ประวัติการใช้งาน</h3>
        <DataTable columns={auditCols} rows={auditLogs as any} pageSize={10}/>
      </div>

      <button onClick={()=>{ auth.logout(); nav('/login') }}
        className="w-full py-2.5 rounded-xl border border-bear/30 text-bear hover:bg-bear/10 transition-all text-sm font-medium">
        ออกจากระบบ
      </button>
    </div>
  )
}
