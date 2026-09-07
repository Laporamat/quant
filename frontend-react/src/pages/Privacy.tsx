import { Link } from 'react-router-dom'
import { useSEO, breadcrumbSchema } from '@/hooks/useSEO'
import Breadcrumbs from '@/components/shared/Breadcrumbs'

const LAST_UPDATED = '1 ธันวาคม 2024'

export default function Privacy() {
  useSEO({
    title: 'นโยบายความเป็นส่วนตัว (Privacy Policy)',
    description: 'QuantDash เก็บข้อมูลอะไรบ้าง ใช้อย่างไร และปกป้องข้อมูลส่วนตัวของคุณอย่างไร',
    schema: breadcrumbSchema([{name:'Home',url:'/'},{name:'Privacy Policy',url:'/privacy'}]),
  })

  const Section = ({ id, title, children }: { id:string; title:string; children: React.ReactNode }) => (
    <section id={id} className="space-y-3">
      <h2 className="text-lg font-bold text-surface-100 border-b border-surface-700/50 pb-2">{title}</h2>
      <div className="text-sm text-surface-300 leading-relaxed space-y-2">{children}</div>
    </section>
  )

  return (
    <div className="max-w-3xl mx-auto space-y-8 py-8 animate-fade-in">
      <Breadcrumbs/>

      <div className="space-y-2">
        <h1 className="text-3xl font-black text-surface-100">นโยบายความเป็นส่วนตัว</h1>
        <p className="text-surface-500 text-sm">อัปเดตล่าสุด: {LAST_UPDATED}</p>
      </div>

      {/* Quick nav */}
      <div className="glass rounded-xl p-4">
        <p className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">สารบัญ</p>
        <div className="flex flex-wrap gap-2">
          {['ข้อมูลที่เก็บ','การใช้ข้อมูล','การเปิดเผย','ความปลอดภัย','สิทธิ์ของคุณ','คุกกี้','ติดต่อ'].map((t,i)=>(
            <a key={t} href={`#sec-${i+1}`} className="text-xs text-primary-400 hover:underline px-2 py-0.5 bg-primary-600/10 rounded-full">{t}</a>
          ))}
        </div>
      </div>

      <Section id="sec-1" title="1. ข้อมูลที่เราเก็บรวบรวม">
        <p><strong className="text-surface-200">ข้อมูลที่คุณให้:</strong></p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>อีเมล, ชื่อผู้ใช้, ชื่อที่แสดง (สมัครสมาชิก)</li>
          <li>รหัสผ่าน (เก็บเป็น bcrypt hash เท่านั้น ไม่เก็บ plaintext)</li>
        </ul>
        <p><strong className="text-surface-200">ข้อมูลที่เก็บอัตโนมัติ:</strong></p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>IP address และ User-Agent (สำหรับ security audit log)</li>
          <li>เวลาเข้าสู่ระบบล่าสุด</li>
          <li>Google Analytics 4 (pageviews, anonymized — IP anonymization enabled)</li>
        </ul>
        <p><strong className="text-surface-200">ข้อมูลที่ไม่เก็บ:</strong> ข้อมูลบัตรเครดิต, ข้อมูลทางการเงินส่วนตัว, เบอร์โทร</p>
      </Section>

      <Section id="sec-2" title="2. วัตถุประสงค์การใช้ข้อมูล">
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>ยืนยันตัวตนและให้บริการ Platform</li>
          <li>ส่ง email แจ้งเตือนความปลอดภัย (รหัสผ่านเปลี่ยน, login จาก device ใหม่)</li>
          <li>วิเคราะห์การใช้งาน (aggregated, anonymized) เพื่อปรับปรุง UX</li>
          <li>ป้องกัน abuse และ fraud</li>
        </ul>
        <p>เราไม่ขายข้อมูลส่วนตัวให้บุคคลที่สาม</p>
      </Section>

      <Section id="sec-3" title="3. การเปิดเผยข้อมูล">
        <p>เราอาจแชร์ข้อมูลกับ:</p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li><strong className="text-surface-200">Google Analytics</strong> — anonymized usage data (IP anonymized)</li>
          <li><strong className="text-surface-200">OpenAI / Anthropic</strong> — เฉพาะ chat messages ที่คุณส่ง ถ้าเลือกใช้ AI provider เหล่านี้</li>
          <li><strong className="text-surface-200">หน่วยงานกฎหมาย</strong> — ตามที่กฎหมายกำหนดเท่านั้น</li>
        </ul>
      </Section>

      <Section id="sec-4" title="4. ความปลอดภัย">
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>รหัสผ่าน: bcrypt cost-12 (ไม่มี plaintext ในระบบ)</li>
          <li>Authentication: JWT HS256, access token TTL 15 นาที, refresh token 7 วัน</li>
          <li>Account lockout: 5 failed attempts → exponential backoff (15 นาที → 30 นาที → ...)</li>
          <li>Security headers: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy</li>
          <li>Audit log: ทุก login/logout/password change บันทึกพร้อม IP และ timestamp</li>
          <li>HTTPS: ทุก connection เข้ารหัส</li>
        </ul>
      </Section>

      <Section id="sec-5" title="5. สิทธิ์ของคุณ">
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li><strong className="text-surface-200">เข้าถึงข้อมูล</strong>: ดูข้อมูลส่วนตัวได้ที่ Profile</li>
          <li><strong className="text-surface-200">แก้ไขข้อมูล</strong>: เปลี่ยน display name ได้ที่ Profile</li>
          <li><strong className="text-surface-200">ลบข้อมูล</strong>: ติดต่อ support เพื่อขอลบบัญชี</li>
          <li><strong className="text-surface-200">Export ข้อมูล</strong>: ขอ export audit log ได้</li>
          <li><strong className="text-surface-200">ยกเลิกความยินยอม</strong>: ปิด GA ได้ผ่าน browser extension</li>
        </ul>
      </Section>

      <Section id="sec-6" title="6. คุกกี้และ Local Storage">
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li><strong className="text-surface-200">qd_access</strong> (localStorage): JWT access token</li>
          <li><strong className="text-surface-200">qd_refresh</strong> (HttpOnly cookie): Refresh token</li>
          <li><strong className="text-surface-200">theme</strong> (localStorage): Dark/light preference</li>
          <li><strong className="text-surface-200">GA4 cookies</strong>: _ga, _ga_XXXXXXX (anonymized analytics)</li>
        </ul>
      </Section>

      <Section id="sec-7" title="7. ติดต่อ">
        <p>หากมีคำถามเกี่ยวกับ Privacy Policy ติดต่อได้ที่:</p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>Email: privacy@quantdash.app</li>
          <li>Response time: ภายใน 24 ชั่วโมงในวันทำการ</li>
        </ul>
      </Section>

      {/* Links */}
      <div className="glass rounded-xl p-4 flex flex-wrap gap-3 text-sm">
        <Link to="/terms"        className="text-primary-400 hover:underline">Terms of Service</Link>
        <span className="text-surface-700">·</span>
        <Link to="/about"        className="text-primary-400 hover:underline">เกี่ยวกับเรา</Link>
        <span className="text-surface-700">·</span>
        <Link to="/faq"          className="text-primary-400 hover:underline">FAQ</Link>
        <span className="text-surface-700">·</span>
        <Link to="/profile"      className="text-primary-400 hover:underline">Profile Settings</Link>
      </div>
    </div>
  )
}
