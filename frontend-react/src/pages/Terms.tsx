import { Link } from 'react-router-dom'
import { useSEO, breadcrumbSchema } from '@/hooks/useSEO'
import Breadcrumbs from '@/components/shared/Breadcrumbs'

export default function Terms() {
  useSEO({
    title: 'ข้อกำหนดการใช้งาน (Terms of Service)',
    description: 'ข้อกำหนดและเงื่อนไขการใช้งาน QuantDash — Quantitative Trading Platform',
    schema: breadcrumbSchema([{ name: 'Home', url: '/' }, { name: 'Terms', url: '/terms' }]),
  })

  const S = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <section className="space-y-2">
      <h2 className="text-lg font-bold text-surface-100 border-b border-surface-700/50 pb-2">{title}</h2>
      <div className="text-sm text-surface-300 leading-relaxed space-y-2">{children}</div>
    </section>
  )

  return (
    <div className="max-w-3xl mx-auto space-y-8 py-8 animate-fade-in">
      <Breadcrumbs />
      <div>
        <h1 className="text-3xl font-black text-surface-100">ข้อกำหนดการใช้งาน</h1>
        <p className="text-surface-500 text-sm mt-1">อัปเดตล่าสุด: 1 ธันวาคม 2024</p>
      </div>

      <S title="1. การยอมรับข้อกำหนด">
        <p>การใช้งาน QuantDash ("Platform") ถือว่าคุณยอมรับข้อกำหนดเหล่านี้ทั้งหมด หากไม่ยอมรับ กรุณาหยุดใช้งาน</p>
      </S>

      <S title="2. คำอธิบายบริการ">
        <p>QuantDash เป็น Quantitative Trading Platform สำหรับวิเคราะห์ข้อมูลตลาดหุ้นย้อนหลัง ประกอบด้วย:</p>
        <ul className="list-disc list-inside ml-2 space-y-1">
          <li>ข้อมูลราคาหุ้นย้อนหลัง 20 ปี จาก Yahoo Finance</li>
          <li>OCaml Probability Engine (Black-Scholes, GBM, Bayesian)</li>
          <li>Backtesting สำหรับ 10 กลยุทธ์การเทรด</li>
          <li>AI Chatbot สำหรับคำถามด้านการเทรด</li>
          <li>เครื่องมือวิเคราะห์ทางสถิติและ Bubble Detection</li>
        </ul>
      </S>

      <S title="3. ข้อจำกัดความรับผิดชอบ (Disclaimer)">
        <div className="bg-bear/5 border border-bear/20 rounded-xl p-4 space-y-2">
          <p className="font-semibold text-surface-100">⚠️ QuantDash ไม่ใช่คำแนะนำการลงทุน</p>
          <ul className="list-disc list-inside ml-2 space-y-1">
            <li>ผลการ Backtest ในอดีตไม่ได้รับประกันผลในอนาคต</li>
            <li>การวิเคราะห์ทางสถิติและ Probability เป็นเพียงเครื่องมือช่วยตัดสินใจ ไม่ใช่คำแนะนำซื้อขาย</li>
            <li>QuantDash ไม่มีใบอนุญาตที่ปรึกษาการลงทุน (Investment Advisor)</li>
            <li>ผู้ใช้รับผิดชอบการตัดสินใจลงทุนทั้งหมดด้วยตนเอง</li>
            <li>QuantDash ไม่รับผิดชอบต่อความสูญเสียทางการเงินใดๆ</li>
          </ul>
        </div>
      </S>

      <S title="4. บัญชีผู้ใช้">
        <ul className="list-disc list-inside ml-2 space-y-1">
          <li>คุณรับผิดชอบรักษาความปลอดภัยของบัญชี</li>
          <li>ห้ามใช้บัญชีในทางที่ผิดกฎหมายหรือก่อความเสียหาย</li>
          <li>เราสงวนสิทธิ์ระงับบัญชีที่ละเมิดข้อกำหนด</li>
          <li>แจ้งทันทีหากพบการใช้งานโดยไม่ได้รับอนุญาต</li>
        </ul>
      </S>

      <S title="5. ทรัพย์สินทางปัญญา">
        <p>Source code, อัลกอริทึม, UI และเนื้อหาทั้งหมดเป็นทรัพย์สินของ QuantDash ห้ามคัดลอก แก้ไข หรือนำไปใช้เชิงพาณิชย์โดยไม่ได้รับอนุญาต</p>
        <p>ข้อมูลราคาหุ้นมาจาก Yahoo Finance ซึ่งมีข้อกำหนดการใช้งานของตัวเอง</p>
      </S>

      <S title="6. ข้อมูลจาก Third Party">
        <ul className="list-disc list-inside ml-2 space-y-1">
          <li><strong className="text-surface-200">Yahoo Finance</strong>: ข้อมูลราคาหุ้น — อาจมีความล่าช้าหรือคลาดเคลื่อน</li>
          <li><strong className="text-surface-200">OpenAI / Anthropic</strong>: AI responses — ตอบตามความรู้ที่มี อาจไม่ถูกต้อง 100%</li>
          <li>QuantDash ไม่รับประกันความถูกต้องของข้อมูลจาก third party</li>
        </ul>
      </S>

      <S title="7. การเปลี่ยนแปลงข้อกำหนด">
        <p>เราอาจแก้ไขข้อกำหนดได้ตลอดเวลา การแจ้งเตือนจะส่งผ่าน email หรือแสดงบน Platform การใช้งานต่อเนื่องถือว่ายอมรับข้อกำหนดที่แก้ไข</p>
      </S>

      <S title="8. กฎหมายที่ใช้บังคับ">
        <p>ข้อกำหนดนี้อยู่ภายใต้กฎหมายไทย ข้อพิพาทจะแก้ไขโดยศาลในประเทศไทย</p>
      </S>

      <div className="glass rounded-xl p-4 flex flex-wrap gap-3 text-sm">
        <Link to="/privacy" className="text-primary-400 hover:underline">Privacy Policy</Link>
        <span className="text-surface-700">·</span>
        <Link to="/about"   className="text-primary-400 hover:underline">เกี่ยวกับเรา</Link>
        <span className="text-surface-700">·</span>
        <Link to="/faq"     className="text-primary-400 hover:underline">FAQ</Link>
      </div>
    </div>
  )
}
