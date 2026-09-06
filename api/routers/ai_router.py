"""
api/routers/ai_router.py
─────────────────────────
Trading AI Chatbot — rule-based + knowledge base + live market context

Architecture:
  1. Knowledge base matching (trading_knowledge.py) — ตอบได้แม้ไม่มี LLM
  2. Live market context injection — ดึงข้อมูลจริงจาก loader
  3. Optional OpenAI/compatible LLM — ถ้ามี OPENAI_API_KEY ใน .env
  4. Streaming SSE response — frontend แสดงแบบ typewriter effect

POST /ai/chat          → ส่งข้อความ ได้ JSON response
GET  /ai/stream        → Server-Sent Events (SSE) สำหรับ streaming
GET  /ai/suggestions   → คำถามแนะนำตาม ticker ปัจจุบัน
GET  /ai/context/{ticker} → Market context สำหรับ pre-fill chat
"""
from __future__ import annotations

import json
import math
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ai_engine"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ocaml_engine"))

from trading_knowledge import find_best_match, is_greeting, is_thanks, KNOWLEDGE  # type: ignore
from quant_probability import bayesian_regime_prob, var_parametric, kelly_criterion  # type: ignore

from api.dependencies import get_loader
from data.loader import DataLoader

router = APIRouter(prefix="/ai", tags=["ai-chat"])

# ── Optional OpenAI ────────────────────────────────────────────────────────────
_OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
_openai_available = bool(_OPENAI_KEY)


# ── Pydantic ───────────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role:    str  # "user" | "assistant" | "system"
    content: str

class ChatRequest(BaseModel):
    message:  str = Field(..., min_length=1, max_length=2000)
    history:  list[ChatMessage] = Field(default_factory=list)
    ticker:   Optional[str] = None
    context:  Optional[str] = None   # "analysis" | "backtest" | "general"


# ── System prompt (used with LLM or as intro text) ─────────────────────────────
_SYSTEM_PROMPT = """คุณคือ QuantAI — ผู้ช่วย AI ด้านการเทรดและการลงทุนเชิงปริมาณ (Quantitative Trading)

ความเชี่ยวชาญ:
- Technical Analysis: RSI, MACD, Bollinger Bands, Moving Averages, Chart Patterns
- Statistical Trading: Mean Reversion, Momentum, Trend Following
- Risk Management: Kelly Criterion, VaR, CVaR, Position Sizing
- Quantitative Finance: Black-Scholes, Probability Cone (GBM), Bayesian Regime Detection
- Market Structure: Support/Resistance, Smart Money Concepts, Price Action

กฎการตอบ:
1. ตอบเป็นภาษาไทยเป็นหลัก (ยกเว้นศัพท์เทคนิคที่ใช้ภาษาอังกฤษได้)
2. ถ้ามีข้อมูล Market Context → ใช้ข้อมูลจริงในการตอบ
3. ตอบตรงประเด็น กระชับ มีตัวอย่างเสมอ
4. ใช้ Markdown สำหรับ formatting
5. ไม่แนะนำให้ซื้อขายหุ้นใดหุ้นหนึ่งโดยตรง — แนะนำวิธีวิเคราะห์แทน
6. เตือนเรื่อง Risk เสมอเมื่อกล่าวถึงกลยุทธ์

ข้อมูลระบบ: QuantDash ใช้ข้อมูลย้อนหลัง 20 ปีจาก Yahoo Finance, 
OCaml probability engine สำหรับ Black-Scholes และ GBM, 
Bayesian regime detection และ Kelly Criterion
"""

# ── Market context builder ─────────────────────────────────────────────────────
def _build_market_context(ticker: str, loader: DataLoader) -> str:
    """ดึงข้อมูลจริงและสร้าง context string สำหรับ AI"""
    try:
        df = loader.load(ticker.upper())
        if df.empty or len(df) < 60:
            return f"ไม่พบข้อมูลสำหรับ {ticker}"

        prices  = df["close"]
        returns = prices.pct_change().dropna()
        d_sigma = float(returns.std())
        d_mu    = float(returns.mean())
        spot    = float(prices.iloc[-1])
        ann_vol = d_sigma * math.sqrt(252) * 100
        ann_mu  = d_mu * 252 * 100

        # MA
        ma20  = float(prices.rolling(20).mean().iloc[-1])
        ma50  = float(prices.rolling(50).mean().iloc[-1])
        ma200 = float(prices.rolling(200).mean().iloc[-1]) if len(prices) >= 200 else 0

        # RSI
        delta = prices.diff().dropna()
        gain  = delta.clip(lower=0).rolling(14).mean().iloc[-1]
        loss  = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
        rsi   = 100 - 100 / (1 + gain / loss) if loss > 0 else 100.0

        # 5d return
        ret5d = float((prices.iloc[-1] / prices.iloc[-6] - 1) * 100) if len(prices) >= 6 else 0

        # Regime
        recent   = returns.tail(20).tolist()
        regime_p = bayesian_regime_prob(0.6, 0.0006, 0.008, -0.001, 0.018, recent) if recent else 0.6

        # Risk
        var1d  = var_parametric(d_mu, d_sigma, 0.95) * 100
        win_r  = float((returns > 0).mean())
        avg_w  = float(returns[returns > 0].mean()) if (returns > 0).any() else 0
        avg_l  = float(abs(returns[returns < 0].mean())) if (returns < 0).any() else 1e-6
        wlr    = avg_w / avg_l if avg_l > 0 else 1
        kelly  = max(0, kelly_criterion(win_r, wlr)) * 100

        return (
            f"📊 **ข้อมูลปัจจุบัน {ticker.upper()}** (ข้อมูลจริงจากระบบ)\n"
            f"- ราคาล่าสุด: ${spot:.2f}\n"
            f"- ผลตอบแทน 5 วัน: {ret5d:+.2f}%\n"
            f"- MA20: ${ma20:.2f} | MA50: ${ma50:.2f} | MA200: ${ma200:.2f}\n"
            f"- RSI(14): {rsi:.1f} {'🔴 Overbought' if rsi > 70 else '🟢 Oversold' if rsi < 30 else '⚪ Neutral'}\n"
            f"- Volatility (Ann): {ann_vol:.1f}% | Drift (Ann): {ann_mu:+.1f}%\n"
            f"- VaR 1-day 95%: {var1d:.2f}%\n"
            f"- Win Rate (5d hold): {win_r*100:.1f}% | W/L Ratio: {wlr:.2f}\n"
            f"- Kelly Criterion: {kelly:.1f}% (ใช้ Half={kelly/2:.1f}%)\n"
            f"- Bayesian Regime: {'🟢 Bull' if regime_p > 0.5 else '🔴 Bear'} ({regime_p*100:.0f}% bull)\n"
            f"- ราคา vs MA200: {'เหนือ ✅' if spot > ma200 else 'ต่ำกว่า ⚠️'}\n"
        )
    except Exception as e:
        return f"ไม่สามารถโหลดข้อมูล {ticker}: {str(e)}"


# ── Response builder ──────────────────────────────────────────────────────────
def _build_response(
    query: str,
    history: list[ChatMessage],
    ticker: Optional[str],
    market_ctx: Optional[str],
    loader: Optional[DataLoader] = None,
) -> str:
    """
    Rule-based response pipeline:
    1. Greetings / Thanks
    2. Knowledge base match
    3. Market-specific query
    4. Fallback
    """
    q = query.strip()

    # ── Greetings ──────────────────────────────────────────────────────────────
    if is_greeting(q):
        ticker_intro = f" กำลังดู **{ticker.upper()}** อยู่" if ticker else ""
        return (
            f"สวัสดีครับ! ผม **QuantAI** ผู้ช่วยด้านการเทรดและวิเคราะห์ตลาด{ticker_intro} 📈\n\n"
            "สามารถถามผมได้เกี่ยวกับ:\n"
            "- 📊 Technical Analysis (RSI, MACD, Bollinger, MA)\n"
            "- ⚠️ Risk Management (Kelly, VaR, Position Sizing)\n"
            "- 🎯 Strategy (Mean Reversion, Trend Following, Breakout)\n"
            "- 🧠 จิตวิทยาการเทรด\n"
            "- 📉 การอ่านกราฟและ Pattern\n\n"
            "หรือพิมพ์ชื่อหุ้น เช่น **`วิเคราะห์ AAPL`** เพื่อดูข้อมูลจริงจากระบบ"
        )

    if is_thanks(q):
        return "ยินดีครับ! ถ้ามีคำถามเพิ่มเติมเกี่ยวกับการเทรดหรือ indicator ใดๆ ถามได้เลยนะครับ 😊"

    # ── Market-specific: "วิเคราะห์ AAPL" ────────────────────────────────────
    import re
    ticker_in_query = re.search(
        r"\b([A-Z]{1,5}(?:\.[A-Z]{2})?)\b|วิเคราะห์\s+([A-Za-z.]+)|ดู\s+([A-Za-z.]+)", 
        q.upper()
    )
    
    active_ticker = ticker
    if ticker_in_query:
        found = next((g for g in ticker_in_query.groups() if g), None)
        if found and len(found) >= 2 and found not in {"OR", "IS", "AT", "IN", "ON", "MA", "OR", "TO", "BE", "IF", "OF"}:
            active_ticker = found.upper().strip()

    # ── Build market context ───────────────────────────────────────────────────
    mctx = ""
    if active_ticker and loader:
        mctx = _build_market_context(active_ticker, loader)

    # ── Knowledge base match ──────────────────────────────────────────────────
    match = find_best_match(q)

    # ── Compose response ──────────────────────────────────────────────────────
    response_parts = []

    if mctx and active_ticker:
        response_parts.append(mctx)
        response_parts.append("")

    if match:
        _topic, answer, confidence = match
        response_parts.append(answer)

        # Add market-specific commentary if we have both
        if mctx and active_ticker and confidence >= 0.4:
            response_parts.append(
                f"\n---\n"
                f"💡 **สำหรับ {active_ticker}**: ดูรายละเอียดเพิ่มเติมได้ที่ **Ticker Deep Dive** หรือ **Edge Trading** ในแอป"
            )
    elif mctx:
        # Market context แต่ไม่มี knowledge match
        response_parts.append(
            f"นี่คือข้อมูลของ **{active_ticker}** จากระบบครับ\n\n"
            "💡 ต้องการวิเคราะห์เพิ่มเติม ลองถามเรื่อง:\n"
            "- RSI หรือ MACD ของ " + active_ticker + "\n"
            "- แนวรับแนวต้านของ " + active_ticker + "\n"
            "- ควรใช้ Strategy ไหนดี"
        )
    else:
        # General fallback
        topic_list = []
        for k, v in KNOWLEDGE.items():
            topic_list.append(v["keywords"][0])

        response_parts.append(
            "ขอโทษครับ ผมยังไม่เข้าใจคำถามนี้ชัดเจนพอ\n\n"
            "**ลองถามเกี่ยวกับ**:\n"
            + "\n".join(f"- {t.title()}" for t in topic_list[:10])
            + "\n\nหรือ พิมพ์ชื่อหุ้น เช่น **`วิเคราะห์ SPY`** เพื่อดูข้อมูลจริง"
        )

    return "\n".join(response_parts)


# ── Streaming generator ────────────────────────────────────────────────────────
async def _stream_response(text: str, chunk_size: int = 8) -> AsyncGenerator[str, None]:
    """Stream text ทีละ chunk เป็น SSE format."""
    words = text.split(" ")
    buffer = []
    for w in words:
        buffer.append(w)
        if len(buffer) >= chunk_size:
            chunk = " ".join(buffer) + " "
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
            buffer = []
            await asyncio.sleep(0.02)
    if buffer:
        chunk = " ".join(buffer)
        yield f"data: {json.dumps({'delta': chunk})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(
    req:    ChatRequest,
    loader: DataLoader = Depends(get_loader),
):
    """
    Main chat endpoint — ส่งข้อความ รับ JSON response
    รองรับ: knowledge base + live market data
    """
    # Try OpenAI first if available
    if _openai_available:
        try:
            return await _openai_chat(req, loader)
        except Exception:
            pass  # fall through to rule-based

    # Rule-based response
    response = _build_response(
        query=req.message,
        history=req.history,
        ticker=req.ticker,
        market_ctx=req.context,
        loader=loader,
    )

    return {
        "role":    "assistant",
        "content": response,
        "engine":  "rule_based",
        "ticker":  req.ticker,
        "ts":      datetime.utcnow().isoformat(),
    }


@router.get("/stream")
async def stream_chat(
    message: str = Query(..., min_length=1),
    ticker:  Optional[str] = Query(None),
    loader:  DataLoader = Depends(get_loader),
):
    """Streaming SSE endpoint สำหรับ typewriter effect."""
    response = _build_response(
        query=message,
        history=[],
        ticker=ticker,
        market_ctx=None,
        loader=loader,
    )

    return StreamingResponse(
        _stream_response(response),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/suggestions")
async def get_suggestions(
    ticker:  Optional[str] = Query(None),
    context: Optional[str] = Query(None),
    loader:  DataLoader = Depends(get_loader),
):
    """คำถามแนะนำตาม context ปัจจุบัน."""
    base = [
        "RSI คืออะไร และอ่านค่าอย่างไร?",
        "วิธีกำหนด Stop Loss ที่ดีที่สุด",
        "Kelly Criterion คืออะไร ใช้อย่างไร?",
        "Mean Reversion กับ Trend Following ต่างกันอย่างไร?",
        "Position Sizing คำนวณอย่างไร?",
        "Bollinger Bands Squeeze คืออะไร?",
    ]

    if ticker:
        base = [
            f"วิเคราะห์ {ticker.upper()} ตอนนี้",
            f"RSI ของ {ticker.upper()} บอกอะไร?",
            f"แนวรับแนวต้านของ {ticker.upper()} อยู่ที่ไหน?",
            f"ควร Trade {ticker.upper()} ด้วย Strategy ไหน?",
            f"Risk ของการเทรด {ticker.upper()} คือ?",
            "วิธีกำหนด Stop Loss ที่ดีที่สุด",
            "Kelly Criterion คืออะไร?",
        ]

    if context == "backtest":
        base += [
            "Sharpe Ratio > 1.0 หมายความว่าอะไร?",
            "Max Drawdown 15% ดีหรือไม่ดี?",
            "Overfitting ใน Backtest คืออะไร?",
        ]

    return {"suggestions": base[:8]}


@router.get("/context/{ticker}")
async def get_market_context(
    ticker: str,
    loader: DataLoader = Depends(get_loader),
):
    """Market context สำหรับ pre-fill ใน chat."""
    ctx = _build_market_context(ticker, loader)
    return {"ticker": ticker.upper(), "context": ctx}


# ── Optional OpenAI integration ────────────────────────────────────────────────
async def _openai_chat(req: ChatRequest, loader: DataLoader) -> dict:
    """ใช้ OpenAI GPT ถ้ามี key — inject trading knowledge + market context"""
    import httpx  # noqa

    market_ctx = ""
    if req.ticker:
        market_ctx = _build_market_context(req.ticker, loader)

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

    if market_ctx:
        messages.append({
            "role": "system",
            "content": f"ข้อมูลตลาดปัจจุบัน:\n{market_ctx}"
        })

    for h in req.history[-10:]:   # last 10 turns context
        messages.append({"role": h.role, "content": h.content})

    messages.append({"role": "user", "content": req.message})

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {_OPENAI_KEY}"},
            json={
                "model":       "gpt-4o-mini",
                "messages":    messages,
                "temperature": 0.7,
                "max_tokens":  1000,
            },
        )
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

    return {
        "role":    "assistant",
        "content": content,
        "engine":  "openai_gpt",
        "ticker":  req.ticker,
        "ts":      datetime.utcnow().isoformat(),
    }
