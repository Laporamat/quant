"""
ai_engine/trading_knowledge.py
────────────────────────────────
Trading knowledge base สำหรับ AI Chatbot
ข้อมูลมาจากเอกสารที่ให้มา + ความรู้ quantitative finance

ระบบ: Rule-based + Vector similarity (ไม่ต้องใช้ OpenAI)
      ถ้ามี OPENAI_API_KEY ใน env จะใช้ GPT เสริม
"""
from __future__ import annotations

import math
import re
from typing import Optional

# ── Knowledge Base ────────────────────────────────────────────────────────────
KNOWLEDGE: dict[str, dict] = {

    # ─────────────── พื้นฐาน ───────────────
    "long_short": {
        "keywords": ["long", "short", "ลอง", "ชอร์ต", "เปิดซื้อ", "เปิดขาย"],
        "answer": (
            "**Long vs Short**\n\n"
            "- **Long (ซื้อ)**: คาดว่าราคาจะ **ขึ้น** → ซื้อก่อน ขายทีหลัง กำไรเมื่อราคาสูงขึ้น\n"
            "- **Short (ขาย)**: คาดว่าราคาจะ **ลง** → ยืมหุ้นมาขายก่อน ซื้อคืนทีหลังในราคาต่ำกว่า\n\n"
            "**ความเสี่ยง**: Long เสียได้มากสุดเท่าที่ลงทุน แต่ Short เสียได้ไม่จำกัด (ราคาขึ้นได้ไม่มีขีดจำกัด)\n\n"
            "**สูตร PnL**:\n"
            "- Long: PnL = (ราคาขาย - ราคาซื้อ) × จำนวนหุ้น\n"
            "- Short: PnL = (ราคาขาย - ราคาซื้อคืน) × จำนวนหุ้น"
        ),
    },

    "bid_ask_spread": {
        "keywords": ["bid", "ask", "spread", "สเปรด", "ราคาซื้อ", "ราคาขาย"],
        "answer": (
            "**Bid / Ask / Spread**\n\n"
            "- **Bid**: ราคาสูงสุดที่ผู้ซื้อยินดีจ่าย\n"
            "- **Ask**: ราคาต่ำสุดที่ผู้ขายยินดีรับ\n"
            "- **Spread** = Ask − Bid → เป็น **ต้นทุนซ่อน** ทุกครั้งที่เทรด\n\n"
            "**ตัวอย่าง**: Bid 100.00 / Ask 100.05 → Spread = 0.05 (0.05%)\n\n"
            "💡 **Tip**: Spread กว้างมาก = สภาพคล่องต่ำ ควรหลีกเลี่ยงช่วงนอกเวลาตลาด"
        ),
    },

    "stop_loss_take_profit": {
        "keywords": ["stop loss", "take profit", "sl", "tp", "ตัดขาดทุน", "จุดออก", "หยุดขาดทุน"],
        "answer": (
            "**Stop Loss & Take Profit**\n\n"
            "**Stop Loss (SL)** — จุดตัดขาดทุน\n"
            "- วางก่อนเข้าเทรดทุกครั้ง ห้ามเลื่อนออกไปเรื่อยๆ\n"
            "- วิธีกำหนด: ใช้ ATR × 1.5–2 หรือใต้แนวรับ\n\n"
            "**Take Profit (TP)** — จุดทำกำไร\n"
            "- TP1: Risk:Reward = 1:1.5 (ปิดบางส่วน)\n"
            "- TP2: Risk:Reward = 1:2.5 (ปิดที่เหลือ)\n\n"
            "**สูตร Position Size**:\n"
            "```\nPosition Size = เงินที่ยอมเสี่ยง ÷ ระยะ SL\n"
            "เงินที่ยอมเสี่ยง = 1% ของพอร์ต (แนะนำ)\n```\n\n"
            "💡 **กฎทอง**: วาง SL ก่อนเข้า ไม่ใช่หลังจากเข้าแล้ว"
        ),
    },

    "risk_reward": {
        "keywords": ["risk reward", "rr", "r:r", "risk to reward", "ความเสี่ยง", "ผลตอบแทน"],
        "answer": (
            "**Risk:Reward Ratio**\n\n"
            "- R:R 1:2 = เสี่ยง 1 บาท ได้กำไร 2 บาท\n"
            "- ขั้นต่ำแนะนำ: **1:1.5** ขึ้นไป\n\n"
            "**ทำไมสำคัญ?** แม้ win rate แค่ 40% แต่ถ้า R:R = 1:2\n"
            "- กำไร 2 ครั้ง (40%) = +4R\n"
            "- ขาดทุน 3 ครั้ง (60%) = -3R\n"
            "- **สุทธิ +1R → ยังได้กำไร!**\n\n"
            "**สูตร Expectancy**:\n"
            "```\nE = (Win% × AvgWin) - (Loss% × AvgLoss)\nE > 0 = ระบบมี edge\n```"
        ),
    },

    "position_sizing": {
        "keywords": ["position size", "position sizing", "ขนาด", "lot", "จำนวนหุ้น", "kelly"],
        "answer": (
            "**Position Sizing — การกำหนดขนาด Position**\n\n"
            "**Fixed Risk Method** (แนะนำ):\n"
            "```\nPosition = (Capital × Risk%) ÷ (Entry - Stop Loss)\n```\n"
            "ตัวอย่าง: พอร์ต ฿1,000,000, Risk 1%, Entry 100, SL 97\n"
            "→ Position = (1,000,000 × 0.01) ÷ (100-97) = **3,333 หุ้น**\n\n"
            "**Kelly Criterion** (ระบบนี้ใช้):\n"
            "```\nKelly% = Win% - (Loss% ÷ Win:Loss ratio)\n```\n"
            "⚠️ ใช้ **Half-Kelly** จริงเพื่อความปลอดภัย\n\n"
            "**กฎ**: ไม่ควรเสี่ยงเกิน **1-2%** ต่อเทรด"
        ),
    },

    "risk_management": {
        "keywords": ["risk management", "บริหารความเสี่ยง", "money management", "mm", "drawdown", "การจัดการ"],
        "answer": (
            "**Risk Management — กฎสำคัญ**\n\n"
            "1. เสี่ยงไม่เกิน **1%** ต่อเทรด (สูงสุด 2%)\n"
            "2. วาง **Stop Loss ทุกครั้ง** ก่อนเข้า\n"
            "3. ตั้ง **Daily Loss Limit** (เช่น -3% หยุดเทรด)\n"
            "4. ไม่ถัวเฉลี่ยขาดทุน (Averaging Down)\n"
            "5. ห้าม **Revenge Trading** — หยุดหลังขาดทุนติดต่อกัน 3 ครั้ง\n"
            "6. ระวัง **Leverage** → เพิ่มทั้งกำไรและขาดทุน\n"
            "7. หลีกเลี่ยง **Overtrading** — น้อยแต่มีคุณภาพดีกว่า\n\n"
            "**Max Drawdown แนะนำ**: ไม่เกิน 10-15% ของพอร์ต\n"
            "ถ้าเกิน → **หยุด review ระบบก่อน**"
        ),
    },

    # ─────────────── อินดิเคเตอร์ ───────────────
    "rsi": {
        "keywords": ["rsi", "relative strength", "oversold", "overbought", "โอเวอร์บอต", "โอเวอร์โซลด์"],
        "answer": (
            "**RSI — Relative Strength Index**\n\n"
            "- ค่า 0–100, มาตรฐาน period = **14**\n"
            "- **> 70**: Overbought (ซื้อมากเกิน) → ระวังกลับตัว\n"
            "- **< 30**: Oversold (ขายมากเกิน) → ระวังดีดตัว\n"
            "- **> 50**: momentum เอนบวก\n"
            "- **< 50**: momentum เอนลบ\n\n"
            "**Divergence (สัญญาณแรง)**:\n"
            "- **Bullish**: ราคาทำ Low ต่ำลง แต่ RSI ทำ Low สูงขึ้น → กลับตัวขึ้น\n"
            "- **Bearish**: ราคาทำ High สูงขึ้น แต่ RSI ทำ High ต่ำลง → กลับตัวลง\n\n"
            "⚠️ RSI > 70 ≠ สัญญาณขายทันที (ใน Uptrend แรงๆ อาจอยู่เหนือ 70 นาน)"
        ),
    },

    "macd": {
        "keywords": ["macd", "moving average convergence", "signal line", "histogram"],
        "answer": (
            "**MACD — Moving Average Convergence Divergence**\n\n"
            "ประกอบด้วย 3 ส่วน:\n"
            "- **MACD Line** = EMA(12) - EMA(26)\n"
            "- **Signal Line** = EMA(9) ของ MACD Line\n"
            "- **Histogram** = MACD - Signal (แสดงแรงโมเมนตัม)\n\n"
            "**สัญญาณหลัก**:\n"
            "- MACD ตัด Signal ขึ้น → **สัญญาณซื้อ**\n"
            "- MACD ตัด Signal ลง → **สัญญาณขาย**\n"
            "- อยู่เหนือ 0: momentum บวก | ต่ำกว่า 0: momentum ลบ\n"
            "- Divergence: เหมือน RSI → สัญญาณแรง\n\n"
            "💡 ใช้ร่วมกับ Trend filter (EMA 200) ให้ได้ผลดีกว่า"
        ),
    },

    "bollinger_bands": {
        "keywords": ["bollinger", "bb", "bollinger bands", "แบนด์", "squeeze", "expansion"],
        "answer": (
            "**Bollinger Bands**\n\n"
            "- **Middle Band** = SMA(20)\n"
            "- **Upper Band** = SMA(20) + 2×SD\n"
            "- **Lower Band** = SMA(20) - 2×SD\n\n"
            "**การอ่าน**:\n"
            "- **Squeeze** (แคบ): volatility ต่ำ → ใกล้มีการเคลื่อนไหวแรง\n"
            "- **Expansion** (กว้าง): volatility สูง → เทรนด์กำลังวิ่ง\n"
            "- ราคาแตะ Upper: ไม่ได้แปลว่าขายทันที (อาจ ride trend ต่อ)\n"
            "- ราคาแตะ Lower: เช่นกัน\n\n"
            "💡 **Mean Reversion setup**: Z-score < -2 + RSI < 30 = โอกาสดีด"
        ),
    },

    "moving_average": {
        "keywords": ["sma", "ema", "moving average", "ma", "ค่าเฉลี่ย", "golden cross", "death cross"],
        "answer": (
            "**Moving Averages (MA)**\n\n"
            "**ประเภท**: SMA, EMA, WMA, VWMA, HMA\n"
            "- **EMA**: ให้น้ำหนักราคาล่าสุดมากกว่า → ตอบสนองเร็วกว่า SMA\n\n"
            "**ค่าที่นิยม**: 9, 20, 50, 100, 200\n\n"
            "**การใช้**:\n"
            "- ราคา > MA200 → แนวโน้มใหญ่เป็นบวก\n"
            "- **Golden Cross**: MA50 ตัด MA200 ขึ้น → สัญญาณบวกระยะยาว\n"
            "- **Death Cross**: MA50 ตัด MA200 ลง → สัญญาณลบระยะยาว\n"
            "- MA ทำหน้าที่เป็น Dynamic Support/Resistance\n\n"
            "💡 ระบบนี้ใช้ MA20, MA50, MA200 ใน Ticker Deep Dive"
        ),
    },

    "vwap": {
        "keywords": ["vwap", "volume weighted", "ราคาเฉลี่ยถ่วงน้ำหนัก"],
        "answer": (
            "**VWAP — Volume Weighted Average Price**\n\n"
            "ราคาเฉลี่ยถ่วงน้ำหนักด้วยปริมาณซื้อขายตลอดวัน\n\n"
            "**การอ่าน**:\n"
            "- ราคา > VWAP: Bullish intraday\n"
            "- ราคา < VWAP: Bearish intraday\n"
            "- VWAP ทำหน้าที่เป็น **Fair Value** ของวัน\n\n"
            "**Institutional use**: กองทุนใช้ VWAP เป็น Benchmark\n"
            "ซื้อใต้ VWAP = ได้ราคาดีกว่าเฉลี่ย\n\n"
            "💡 **Volume Profile** ใช้คู่กันได้ดี — หา POC (Point of Control)"
        ),
    },

    "atr": {
        "keywords": ["atr", "average true range", "volatility", "ความผันผวน"],
        "answer": (
            "**ATR — Average True Range**\n\n"
            "วัด **ความผันผวน** ของราคา ไม่ได้บอกทิศทาง\n\n"
            "**การใช้งาน**:\n"
            "- **Stop Loss** = Entry ± (ATR × 1.5–2.0)\n"
            "- **Position Size**: ใช้ ATR แทน fixed pip → ปรับตาม volatility\n"
            "- ATR สูง = ตลาดผันผวนมาก → ควรลด position size\n"
            "- ATR ต่ำ = Squeeze → ระวัง breakout\n\n"
            "**สูตร**: True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)\n\n"
            "💡 ระบบนี้ใช้ ATR คำนวณ Stop Loss ใน Trade Setup"
        ),
    },

    "adx": {
        "keywords": ["adx", "average directional", "trend strength", "ความแข็งแรง"],
        "answer": (
            "**ADX — Average Directional Index**\n\n"
            "วัด **ความแข็งแรงของเทรนด์** ไม่ใช่ทิศทาง (0–100)\n\n"
            "- ADX < 20: ไม่มีเทรนด์ชัดเจน (Sideways)\n"
            "- ADX 20–40: เทรนด์เริ่มต้น → **จังหวะเข้า**\n"
            "- ADX > 40: เทรนด์แข็งแรง\n"
            "- ADX > 60: เทรนด์แข็งมาก (หายาก)\n\n"
            "**+DI/-DI**: ใช้คู่กับ ADX\n"
            "- +DI > -DI = แรงซื้อมากกว่า\n"
            "- -DI > +DI = แรงขายมากกว่า\n\n"
            "💡 ADX < 20 → ระวังสัญญาณ MA Crossover เพราะอาจ false signal"
        ),
    },

    # ─────────────── รูปแบบกราฟ ───────────────
    "candlestick": {
        "keywords": ["candlestick", "candle", "แท่งเทียน", "doji", "hammer", "shooting star", "engulfing"],
        "answer": (
            "**Candlestick Patterns**\n\n"
            "**แท่งเดี่ยว**:\n"
            "- 🕯️ **Doji**: เปิด=ปิด → ความลังเลของตลาด\n"
            "- 🔨 **Hammer**: ไส้ล่างยาว หลังขาลง → Bullish reversal\n"
            "- ⭐ **Shooting Star**: ไส้บนยาว หลังขาขึ้น → Bearish reversal\n"
            "- 📊 **Marubozu**: แท่งยาวไม่มีไส้ → แรงซื้อ/ขายชัด\n\n"
            "**หลายแท่ง**:\n"
            "- **Bullish Engulfing**: แท่งเขียวกลืนแท่งแดง → กลับตัวขึ้น\n"
            "- **Bearish Engulfing**: แท่งแดงกลืนแท่งเขียว → กลับตัวลง\n"
            "- **Morning Star**: 3 แท่ง → กลับตัวขึ้นหลังขาลง\n"
            "- **Evening Star**: 3 แท่ง → กลับตัวลงหลังขาขึ้น\n\n"
            "⚠️ Pattern เดียวไม่พอ ต้องดู context + volume"
        ),
    },

    "chart_patterns": {
        "keywords": ["double top", "double bottom", "head and shoulders", "flag", "triangle", "wedge", "pattern", "รูปแบบ"],
        "answer": (
            "**Chart Patterns**\n\n"
            "**กลับตัว (Reversal)**:\n"
            "- **Double Top**: ขึ้นมา 2 รอบ แล้วลง → ขาย\n"
            "- **Double Bottom**: ลงมา 2 รอบ แล้วขึ้น → ซื้อ\n"
            "- **Head & Shoulders**: 3 ยอด กลาง=สูงสุด → ลง\n"
            "- **Inverse H&S**: 3 ฐาน กลาง=ต่ำสุด → ขึ้น\n\n"
            "**ต่อเนื่อง (Continuation)**:\n"
            "- **Flag/Pennant**: พักตัวสั้นๆ ก่อนวิ่งต่อ\n"
            "- **Ascending Triangle**: แนวต้านราบ ฐานสูงขึ้น → Bullish\n"
            "- **Descending Triangle**: แนวรับราบ ยอดต่ำลง → Bearish\n"
            "- **Cup & Handle**: กลับตัวขึ้นระยะยาว\n\n"
            "💡 **Target**: วัด Pattern height แล้วฉายขึ้น/ลงจากจุด Breakout"
        ),
    },

    "support_resistance": {
        "keywords": ["support", "resistance", "แนวรับ", "แนวต้าน", "sr", "role reversal"],
        "answer": (
            "**Support & Resistance**\n\n"
            "- **Support**: บริเวณที่แรงซื้อเคยเข้า → ราคามักหยุดตก\n"
            "- **Resistance**: บริเวณที่แรงขายเคยเข้า → ราคามักหยุดขึ้น\n\n"
            "**วิธีหา**:\n"
            "- Previous High/Low\n"
            "- Round Numbers (100, 1000)\n"
            "- Fibonacci (38.2%, 50%, 61.8%)\n"
            "- Volume Profile POC\n"
            "- MA200\n\n"
            "**Role Reversal**: แนวต้านที่เบรกผ่านไปแล้ว → กลายเป็นแนวรับ\n\n"
            "💡 **Zone ดีกว่า Line** — S/R เป็นโซน ไม่ใช่เส้นตรง"
        ),
    },

    "fibonacci": {
        "keywords": ["fibonacci", "fib", "ฟีโบ", "retracement", "extension", "61.8", "38.2"],
        "answer": (
            "**Fibonacci Retracement & Extension**\n\n"
            "**Retracement** — หาจุด Pullback:\n"
            "- 23.6%, **38.2%**, **50%**, **61.8%** (Golden Ratio), 78.6%\n"
            "- ลาก Swing Low → Swing High (หรือกลับกัน)\n"
            "- ราคามักพักที่ 38.2%, 50%, 61.8% แล้ววิ่งต่อ\n\n"
            "**Extension** — หาเป้าหมาย:\n"
            "- 127.2%, 161.8%, 200%, 261.8%\n"
            "- ใช้หา TP เมื่อราคาวิ่งเกินจุด Swing เดิม\n\n"
            "💡 **61.8% (Golden Ratio)** = จุด Retracement แรงที่สุด\n"
            "⚠️ ใช้ร่วมกับ S/R และ Pattern เพื่อเพิ่มความน่าเชื่อถือ"
        ),
    },

    # ─────────────── Smart Money / Price Action ───────────────
    "smart_money": {
        "keywords": ["smart money", "smc", "order block", "ob", "fvg", "fair value gap", "liquidity", "bos", "choch"],
        "answer": (
            "**Smart Money Concepts (SMC)**\n\n"
            "**โครงสร้าง**:\n"
            "- **BOS** (Break of Structure): ราคาทะลุ High/Low เดิม → เทรนด์เปลี่ยน\n"
            "- **CHOCH** (Change of Character): สัญญาณแรกว่าโครงสร้างกำลังเปลี่ยน\n\n"
            "**Order Block (OB)**:\n"
            "- โซนที่ Smart Money วางคำสั่ง → ราคามักกลับมา Retest\n"
            "- Bullish OB: แท่งแดงสุดท้ายก่อนวิ่งขึ้น\n"
            "- Bearish OB: แท่งเขียวสุดท้ายก่อนวิ่งลง\n\n"
            "**Fair Value Gap (FVG)**:\n"
            "- ช่องว่างระหว่างแท่งที่ 1 กับ 3 เมื่อแท่ง 2 วิ่งแรง\n"
            "- ราคามักกลับมาเติมก่อนวิ่งต่อ\n\n"
            "**Liquidity Hunt**: Smart Money ล่า SL ของ Retail → จุดที่มี SL เยอะ"
        ),
    },

    "price_action": {
        "keywords": ["price action", "pa", "breakout", "retest", "pullback", "fakeout"],
        "answer": (
            "**Price Action — การเทรดตาม Price เพียวๆ**\n\n"
            "**Breakout**: ราคาทะลุแนวสำคัญ\n"
            "- Volume ควรเพิ่มขึ้น\n"
            "- รอ **Retest** แนวที่เบรก ก่อนเข้า (ความเสี่ยงต่ำกว่า)\n\n"
            "**Fakeout / False Breakout**:\n"
            "- ราคาทะลุแต่กลับเข้ากรอบ → เป็นกับดัก\n"
            "- ป้องกัน: รอ Close เหนือแนว + Volume ยืนยัน\n\n"
            "**Pullback**:\n"
            "- การย่อระหว่างเทรนด์ → โอกาสเข้า\n"
            "- Ideal: ย่อมา 38.2–61.8% Fibonacci แล้ววิ่งต่อ\n\n"
            "**Premium/Discount**:\n"
            "- Premium: ราคาสูงกว่าช่วงราคาหลัก (ขาย)\n"
            "- Discount: ราคาต่ำกว่าช่วงราคาหลัก (ซื้อ)"
        ),
    },

    # ─────────────── รูปแบบการเทรด ───────────────
    "trading_styles": {
        "keywords": ["scalping", "day trading", "swing", "position", "style", "รูปแบบ", "ไทม์เฟรม"],
        "answer": (
            "**รูปแบบการเทรด**\n\n"
            "| รูปแบบ | ถือนาน | TF หลัก | เหมาะกับ |\n"
            "|--------|--------|---------|----------|\n"
            "| **Scalping** | วินาที–นาที | M1–M5 | มีประสบการณ์, ดู chart ตลอด |\n"
            "| **Day Trade** | < 1 วัน | M15–H1 | ตามตลาดแบบ part-time |\n"
            "| **Swing** | 2–14 วัน | H4–Daily | ทำงานประจำ, ดูวันละครั้ง |\n"
            "| **Position** | สัปดาห์–เดือน | Daily–Weekly | Fundamental + Technical |\n\n"
            "💡 **ผู้เริ่มต้น**: แนะนำ **Swing Trading** เพราะ\n"
            "- มีเวลาตัดสินใจมากกว่า\n"
            "- Spread กระทบน้อยกว่า\n"
            "- จิตวิทยาเครียดน้อยกว่า Scalping"
        ),
    },

    "mean_reversion": {
        "keywords": ["mean reversion", "กลับค่าเฉลี่ย", "zscore", "z-score", "reversion"],
        "answer": (
            "**Mean Reversion Strategy**\n\n"
            "**หลักการ**: ราคามักกลับสู่ค่าเฉลี่ยเสมอ\n\n"
            "**Setup**:\n"
            "- Z-score < -1.5 (ราคาต่ำกว่าเฉลี่ยมาก) → ซื้อ\n"
            "- Z-score > +1.5 (ราคาสูงกว่าเฉลี่ยมาก) → ขาย\n"
            "- ยิ่ง Z-score รุนแรง → win rate ยิ่งสูง (จากข้อมูลอดีต)\n\n"
            "**ตัวชี้วัดร่วม**: RSI < 30, Bollinger Lower Touch\n\n"
            "**ข้อควรระวัง**:\n"
            "- ใช้ไม่ได้ใน Strong Trend (ราคาอาจ mean revert ช้ามาก)\n"
            "- ต้องกำหนด SL ป้องกัน Trend ต่อเนื่อง\n\n"
            "💡 ระบบ Edge Trading ในแอปนี้ใช้ Z-score < -1.5 คำนวณ historical win rate"
        ),
    },

    "trend_following": {
        "keywords": ["trend following", "trend", "เทรนด์", "uptrend", "downtrend", "momentum"],
        "answer": (
            "**Trend Following**\n\n"
            "**หลักการ**: 'เทรนด์คือเพื่อน' — เทรดตามทิศทางหลัก\n\n"
            "**ยืนยันเทรนด์ขึ้น**:\n"
            "- Higher High + Higher Low\n"
            "- ราคา > MA50 > MA200\n"
            "- ADX > 25\n"
            "- Volume เพิ่มขึ้นในทิศทางเทรนด์\n\n"
            "**จังหวะเข้า**:\n"
            "- Breakout จาก consolidation\n"
            "- Pullback มา MA20/MA50\n"
            "- Retest แนวรับที่เพิ่ง Breakout\n\n"
            "**ข้อเสีย**: ตอบสนองช้า, Whipsaw ใน Sideways\n\n"
            "💡 กรอง Noise ด้วย ADX > 20 ก่อนเข้า Trend trade"
        ),
    },

    # ─────────────── จิตวิทยา ───────────────
    "psychology": {
        "keywords": ["psychology", "จิตวิทยา", "fomo", "revenge", "emotion", "อารมณ์", "loss aversion"],
        "answer": (
            "**จิตวิทยาการเทรด**\n\n"
            "**ปัญหาที่พบบ่อย**:\n"
            "- 😨 **FOMO**: กลัวพลาด → เข้าช้า ได้ราคาแย่\n"
            "- 💔 **Loss Aversion**: ไม่ยอมตัดขาดทุน → loss ใหญ่ขึ้น\n"
            "- 🎭 **Revenge Trading**: แพ้แล้วเทรดต่อเพื่อเอาคืน → ยิ่งเสีย\n"
            "- 😤 **Overconfidence**: กำไรติด 3 ครั้ง → size ใหญ่ขึ้น\n"
            "- 🔍 **Confirmation Bias**: มองแต่ข้อมูลที่สนับสนุนความคิดตัวเอง\n\n"
            "**แก้ไข**:\n"
            "✅ ใช้ Checklist ก่อนเทรดทุกครั้ง\n"
            "✅ ตั้ง Daily Loss Limit แล้วหยุดทันที\n"
            "✅ บันทึก Journal ทุก trade\n"
            "✅ เทรดตามแผน ไม่ใช่ตามความรู้สึก\n"
            "✅ พักหลังขาดทุนติดต่อกัน 3 ครั้ง"
        ),
    },

    "trading_journal": {
        "keywords": ["journal", "บันทึก", "record", "tracking", "วัดผล"],
        "answer": (
            "**Trading Journal — ทำไมสำคัญที่สุด**\n\n"
            "**สิ่งที่ต้องบันทึก**:\n"
            "- วันที่ / Ticker / TF\n"
            "- Setup ที่เห็น\n"
            "- Entry, SL, TP\n"
            "- Position Size\n"
            "- ผลลัพธ์ (Win/Loss, PnL)\n"
            "- อารมณ์ตอนเทรด\n"
            "- บทเรียน\n\n"
            "**ตัวชี้วัดที่ต้องคำนวณ**:\n"
            "- Win Rate\n"
            "- Average Win / Average Loss\n"
            "- Expectancy = (Win% × AvgWin) - (Loss% × AvgLoss)\n"
            "- Profit Factor = GrossProfit / GrossLoss\n"
            "- Max Drawdown\n\n"
            "💡 **Journal ช่วยหา Pattern ของตัวเอง** — เทรดวันไหนดี ช่วงไหนแย่"
        ),
    },

    # ─────────────── ระบบวิเคราะห์ในแอป ───────────────
    "app_features": {
        "keywords": ["แอป", "ระบบ", "dashboard", "ticker", "backtest", "bubble", "monte carlo", "signal"],
        "answer": (
            "**QuantDash — ฟีเจอร์หลัก**\n\n"
            "🏠 **Dashboard**: ภาพรวม SP100/SET50, Top Movers, Sector Performance\n"
            "📈 **Ticker Dive**: วิเคราะห์หุ้นรายตัว — Candlestick, RSI, MACD, Descriptive Stats, Risk Metrics, Monthly Heatmap\n"
            "⚖️ **Compare**: เปรียบเทียบหลายหุ้น — Correlation, Risk-Return Scatter\n"
            "🔬 **Stats Hub**: Regime Detection (HMM), Seasonality, Tail Risk, Rolling Stats\n"
            "🔥 **Bubble Detect**: ตรวจ Speculative Bubble — Z-Score, LPPL, Log-Price Acceleration\n"
            "🎯 **Edge Trading**: สัญญาณจากข้อมูลอดีต, Kelly Criterion, Trade Setup\n"
            "🧪 **Backtest**: ทดสอบ Strategy 10 แบบ — SMA Crossover, Momentum, Mean Reversion...\n"
            "🎲 **Monte Carlo**: Simulate เส้นทางราคา 1,000–5,000 paths\n"
            "📊 **Optimizer**: Grid Search + Walk-Forward\n\n"
            "ข้อมูลทั้งหมดมาจาก Yahoo Finance ย้อนหลัง **20 ปี** ฟรี"
        ),
    },

    "backtest": {
        "keywords": ["backtest", "ทดสอบ", "forward test", "paper trade", "strategy"],
        "answer": (
            "**Backtesting — ทดสอบระบบกับข้อมูลอดีต**\n\n"
            "**ข้อควรระวัง**:\n"
            "- **Overfitting**: ระบบทำงานดีเฉพาะอดีต แต่ไม่ดีในอนาคต\n"
            "- **Look-ahead Bias**: ใช้ข้อมูลที่ยังไม่มีตอนนั้น\n"
            "- **Survivorship Bias**: ทดสอบเฉพาะหุ้นที่ยังอยู่\n\n"
            "**ตัวชี้วัดสำคัญ**:\n"
            "- **Sharpe Ratio** > 1.0 = ดี, > 2.0 = ดีมาก\n"
            "- **Max Drawdown** < 20% = ยอมรับได้\n"
            "- **Profit Factor** > 1.5 = มี edge\n"
            "- **Win Rate**: 40–60% ปกติ (ขึ้นกับ R:R)\n\n"
            "💡 หลัง Backtest ต้อง **Walk-Forward Test** แยก in-sample/out-of-sample\n\n"
            "ในแอปนี้: ไปที่ **Backtest Lab** → เลือก Strategy → Run"
        ),
    },

    "kelly_criterion": {
        "keywords": ["kelly", "kelly criterion", "position size formula", "optimal"],
        "answer": (
            "**Kelly Criterion — ขนาด Position Optimal**\n\n"
            "```\nKelly% = W - (1-W) / R\nW = Win Rate, R = Win/Loss Ratio\n```\n\n"
            "**ตัวอย่าง**:\n"
            "- Win Rate = 55%, R = 1.5\n"
            "- Kelly = 0.55 - (0.45/1.5) = 0.55 - 0.30 = **25%**\n\n"
            "**ในทางปฏิบัติ → ใช้ Half-Kelly (12.5%)**\n"
            "เพราะ Kelly เต็มมี Drawdown สูง\n\n"
            "**เมื่อไหร่ Kelly < 0?**\n"
            "→ ไม่มี edge → ห้ามเทรด\n\n"
            "💡 ระบบ Edge Trading ในแอปนี้คำนวณ Kelly จากข้อมูลอดีต 20 ปีโดยอัตโนมัติ"
        ),
    },

    "var_cvar": {
        "keywords": ["var", "cvar", "value at risk", "expected shortfall", "ความเสี่ยง", "เสียหาย"],
        "answer": (
            "**VaR & CVaR — วัดความเสี่ยงขาดทุน**\n\n"
            "**VaR (Value at Risk)**:\n"
            "- VaR 95% 1-day = 2% → มีโอกาส 5% ที่จะขาดทุนเกิน 2% ในวันเดียว\n"
            "- ใช้บอกขนาด loss ที่คาดในสถานการณ์ปกติ\n\n"
            "**CVaR (Expected Shortfall)**:\n"
            "- ค่าเฉลี่ยของ loss ที่เกิน VaR\n"
            "- CVaR > VaR เสมอ → บอก worst case ดีกว่า\n\n"
            "**Parametric VaR** (ระบบนี้ใช้ OCaml engine):\n"
            "```\nVaR = -(μ - z × σ)\nz = 1.645 (95%), z = 2.326 (99%)\n```\n\n"
            "💡 ใน Edge Trading: VaR ใช้กำหนด Stop Loss → TP/SL ratio"
        ),
    },

    "fundamental": {
        "keywords": ["fundamental", "pe", "p/e", "p/bv", "roe", "eps", "งบการเงิน", "พื้นฐาน"],
        "answer": (
            "**Fundamental Analysis — วิเคราะห์ปัจจัยพื้นฐาน**\n\n"
            "**ตัวชี้วัดหุ้น**:\n"
            "- **P/E Ratio**: ราคา/กำไรต่อหุ้น → ถูกหรือแพง\n"
            "- **P/BV**: ราคา/มูลค่าทางบัญชี\n"
            "- **ROE**: กำไร/ส่วนของผู้ถือหุ้น → ประสิทธิภาพ\n"
            "- **EPS Growth**: การเติบโตของกำไร\n"
            "- **Debt/Equity**: ระดับหนี้สิน\n\n"
            "**มหภาค**:\n"
            "- อัตราดอกเบี้ย ↑ → หุ้น Growth กดดัน\n"
            "- เงินเฟ้อ ↑ → หุ้น Commodity ได้ประโยชน์\n"
            "- GDP ขยายตัว → ตลาดหุ้นมักขึ้น\n\n"
            "💡 Technical + Fundamental ร่วมกัน = แข็งแกร่งที่สุด"
        ),
    },

    "regime_detection": {
        "keywords": ["regime", "bull", "bear", "sideways", "bayesian", "hmm", "market regime"],
        "answer": (
            "**Market Regime Detection**\n\n"
            "ตลาดมี 3 สภาวะหลัก:\n"
            "- 🟢 **Bull**: ราคาขึ้น momentum บวก\n"
            "- 🔴 **Bear**: ราคาลง momentum ลบ\n"
            "- 🟡 **Sideways**: ราคาเดินในกรอบ\n\n"
            "**วิธีตรวจจับ**:\n"
            "- **HMM** (Hidden Markov Model): ใน Stats Hub\n"
            "- **Bayesian**: ใช้ผลตอบแทนล่าสุด 20 วัน update P(Bull|data)\n"
            "- **MA-based**: ราคา vs MA200\n\n"
            "**ทำไมสำคัญ?**\n"
            "- Mean Reversion ทำงานดีใน Sideways/Bear\n"
            "- Trend Following ทำงานดีใน Bull\n"
            "- ใน Bear market → ลด position size หรือออกทั้งหมด\n\n"
            "💡 ระบบนี้ใช้ Bayesian update ใน Edge Trading + Bubble Detection"
        ),
    },
}

# ── Context Phrases ───────────────────────────────────────────────────────────
GREETINGS = {"สวัสดี", "hello", "hi", "หวัดดี", "ดีครับ", "ดีค่ะ", "hey"}
THANKS    = {"ขอบคุณ", "thanks", "thank you", "ขอบใจ", "thx"}

# ── Tokenizer & Similarity ─────────────────────────────────────────────────────
def _tokenize(text: str) -> list[str]:
    text = text.lower().strip()
    tokens = re.findall(r"[a-zA-Z0-9%/:.]+|[\u0E00-\u0E7F]+", text)
    return tokens

def _score(query_tokens: list[str], keywords: list[str]) -> float:
    """TF-IDF-lite: count keyword hits weighted by length."""
    score = 0.0
    qt = set(query_tokens)
    for kw in keywords:
        kw_tokens = _tokenize(kw)
        kw_set = set(kw_tokens)
        if kw_set <= qt:  # all tokens of keyword present
            score += len(kw_tokens) * 2  # longer keywords score higher
        elif kw_set & qt:  # partial match
            score += len(kw_set & qt) * 0.5
    return score

def find_best_match(query: str) -> Optional[tuple[str, str, float]]:
    """Return (topic, answer, confidence) for best matching knowledge entry."""
    tokens = _tokenize(query)
    best_topic, best_answer, best_score = None, None, 0.0

    for topic, data in KNOWLEDGE.items():
        s = _score(tokens, data["keywords"])
        if s > best_score:
            best_score = s
            best_topic = topic
            best_answer = data["answer"]

    if best_score >= 1.0:
        return best_topic, best_answer, min(1.0, best_score / 5)
    return None

def is_greeting(query: str) -> bool:
    tokens = set(_tokenize(query))
    return bool(tokens & GREETINGS) and len(tokens) < 5

def is_thanks(query: str) -> bool:
    tokens = set(_tokenize(query))
    return bool(tokens & THANKS)
