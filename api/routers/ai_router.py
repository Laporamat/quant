"""
api/routers/ai_router.py
─────────────────────────
Trading AI Chatbot — OpenAI + Anthropic + rule-based fallback

Providers:
  1. openai    — GPT-4o-mini  (sk-nry-... key)
  2. anthropic — Claude 3 Haiku  (sk-n0H... key)
  3. rule_based — built-in knowledge base (always available)

Endpoints:
  POST /ai/chat           → chat (provider auto-selected or specified)
  GET  /ai/stream         → SSE streaming typewriter
  POST /ai/benchmark      → ส่งคำถามเดียว → ตอบทั้ง 3 providers พร้อมกัน
  GET  /ai/suggestions    → คำถามแนะนำ
  GET  /ai/context/{ticker} → live market context
  GET  /ai/providers      → สถานะ provider ที่พร้อมใช้
"""
from __future__ import annotations

import json
import math
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ai_engine"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ocaml_engine"))

from trading_knowledge import find_best_match, is_greeting, is_thanks  # type: ignore
from quant_probability import bayesian_regime_prob, var_parametric, kelly_criterion  # type: ignore

from api.dependencies import get_loader
from data.loader import DataLoader

router = APIRouter(prefix="/ai", tags=["ai-chat"])

# ── Keys ──────────────────────────────────────────────────────────────────────
_OPENAI_KEY    = os.environ.get("OPENAI_API_KEY", "")
_ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

OPENAI_MODEL    = "gpt-4o-mini"
ANTHROPIC_MODEL = "claude-3-haiku-20240307"

# ── System prompt ─────────────────────────────────────────────────────────────
_SYSTEM = """คุณคือ QuantAI ผู้ช่วยด้านการเทรดและการลงทุนเชิงปริมาณ

ความเชี่ยวชาญ: Technical Analysis, Risk Management (Kelly/VaR/CVaR),
Quantitative Finance (Black-Scholes/GBM), Market Regime Detection,
Strategy (Mean Reversion/Trend Following/Momentum)

กฎ:
- ตอบภาษาไทย ใช้ Markdown
- ถ้ามี Market Context → อ้างอิงข้อมูลจริง
- มีตัวอย่างเสมอ กระชับ ตรงประเด็น
- เตือน Risk ทุกครั้งที่แนะนำ Strategy
- ห้ามแนะนำหุ้นใดหุ้นหนึ่งโดยตรง"""


# ── Pydantic models ───────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role:    str
    content: str

class ChatRequest(BaseModel):
    message:  str = Field(..., min_length=1, max_length=2000)
    history:  list[ChatMessage] = Field(default_factory=list)
    ticker:   Optional[str] = None
    provider: Literal["auto", "openai", "anthropic", "rule_based"] = "auto"

class BenchmarkRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    ticker:  Optional[str] = None


# ── Market context ────────────────────────────────────────────────────────────
def _market_context(ticker: str, loader: DataLoader) -> str:
    try:
        df = loader.load(ticker.upper())
        if df.empty or len(df) < 60:
            return f"ไม่พบข้อมูล {ticker}"
        prices  = df["close"]
        rets    = prices.pct_change().dropna()
        d_sigma = float(rets.std())
        d_mu    = float(rets.mean())
        spot    = float(prices.iloc[-1])
        ann_vol = d_sigma * math.sqrt(252) * 100

        ma20  = float(prices.rolling(20).mean().iloc[-1])
        ma50  = float(prices.rolling(50).mean().iloc[-1])
        ma200 = float(prices.rolling(200).mean().iloc[-1]) if len(prices) >= 200 else 0.0

        delta = prices.diff().dropna()
        gain  = delta.clip(lower=0).rolling(14).mean().iloc[-1]
        loss  = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
        rsi   = round(100 - 100 / (1 + gain / loss), 1) if loss > 0 else 100.0

        ret5d = float((prices.iloc[-1] / prices.iloc[-6] - 1) * 100) if len(prices) >= 6 else 0
        regime_p = bayesian_regime_prob(0.6, 0.0006, 0.008, -0.001, 0.018, rets.tail(20).tolist())
        var1d  = var_parametric(d_mu, d_sigma, 0.95) * 100
        win_r  = float((rets > 0).mean())
        avg_w  = float(rets[rets > 0].mean()) if (rets > 0).any() else 0
        avg_l  = float(abs(rets[rets < 0].mean())) if (rets < 0).any() else 1e-6
        kelly  = max(0, kelly_criterion(win_r, avg_w / avg_l if avg_l else 1)) * 100

        return (
            f"[ข้อมูลจริง {ticker.upper()}] "
            f"ราคา ${spot:.2f} | 5d: {ret5d:+.1f}% | "
            f"MA20 ${ma20:.2f} MA50 ${ma50:.2f} MA200 ${ma200:.2f} | "
            f"RSI {rsi} | Vol {ann_vol:.1f}%/yr | VaR1d {var1d:.2f}% | "
            f"WinRate {win_r*100:.0f}% Kelly {kelly:.0f}% | "
            f"Regime {'Bull' if regime_p > 0.5 else 'Bear'} {regime_p*100:.0f}% | "
            f"vs MA200: {'เหนือ' if spot > ma200 else 'ต่ำกว่า'}"
        )
    except Exception as e:
        return f"error loading {ticker}: {e}"


# ── Rule-based response ───────────────────────────────────────────────────────
def _rule_based(query: str, mctx: str) -> str:
    import re
    if is_greeting(query):
        return (
            "สวัสดีครับ! ผม **QuantAI** 📈\n\n"
            "ถามได้เลยเรื่อง RSI, MACD, Kelly Criterion, VaR, Position Sizing, "
            "Backtesting หรือพิมพ์ชื่อหุ้นเพื่อดูข้อมูลจริงจากระบบ"
        )
    if is_thanks(query):
        return "ยินดีครับ! ถามได้เสมอ 😊"

    match = find_best_match(query)
    parts = []
    if mctx:
        parts.append(f"**ข้อมูลตลาดจากระบบ**\n```\n{mctx}\n```\n")
    if match:
        _t, answer, _c = match
        parts.append(answer)
    else:
        parts.append(
            "ขอโทษครับ ยังไม่เข้าใจคำถามนี้\n\n"
            "ลองถามเกี่ยวกับ: RSI, MACD, Bollinger Bands, Kelly Criterion, "
            "Stop Loss, Mean Reversion, Trend Following, Backtest, จิตวิทยาการเทรด"
        )
    return "\n".join(parts)


# ── OpenAI call ───────────────────────────────────────────────────────────────
async def _openai(messages: list[dict], stream: bool = False):
    headers = {
        "Authorization": f"Bearer {_OPENAI_KEY}",
        "Content-Type":  "application/json",
    }
    body = {
        "model":       OPENAI_MODEL,
        "messages":    messages,
        "temperature": 0.7,
        "max_tokens":  1200,
        "stream":      stream,
    }
    async with httpx.AsyncClient(timeout=60) as c:
        if stream:
            async with c.stream("POST", "https://api.openai.com/v1/chat/completions",
                                 headers=headers, json=body) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            d = json.loads(chunk)
                            delta = d["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            pass
        else:
            resp = await c.post("https://api.openai.com/v1/chat/completions",
                                headers=headers, json=body)
            resp.raise_for_status()
            yield resp.json()["choices"][0]["message"]["content"]


# ── Anthropic call ────────────────────────────────────────────────────────────
async def _anthropic(system: str, messages: list[dict], stream: bool = False):
    headers = {
        "x-api-key":         _ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type":      "application/json",
    }
    # Anthropic separates system from messages
    body = {
        "model":      ANTHROPIC_MODEL,
        "system":     system,
        "messages":   messages,
        "max_tokens": 1200,
        "stream":     stream,
    }
    async with httpx.AsyncClient(timeout=60) as c:
        if stream:
            async with c.stream("POST", "https://api.anthropic.com/v1/messages",
                                 headers=headers, json=body) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            d = json.loads(line[6:])
                            if d.get("type") == "content_block_delta":
                                yield d["delta"].get("text", "")
                        except Exception:
                            pass
        else:
            resp = await c.post("https://api.anthropic.com/v1/messages",
                                headers=headers, json=body)
            resp.raise_for_status()
            yield resp.json()["content"][0]["text"]


# ── Build messages list ───────────────────────────────────────────────────────
def _build_messages(req: ChatRequest, mctx: str) -> tuple[list[dict], str]:
    """Returns (messages, system_prompt) in OpenAI format."""
    system = _SYSTEM
    if mctx:
        system += f"\n\nข้อมูลตลาดปัจจุบัน:\n{mctx}"

    msgs = []
    for h in req.history[-12:]:
        msgs.append({"role": h.role, "content": h.content})
    msgs.append({"role": "user", "content": req.message})
    return msgs, system


# ── SSE helpers ───────────────────────────────────────────────────────────────
async def _sse(text_gen) -> AsyncGenerator[str, None]:
    """Wrap async generator into SSE format."""
    async for chunk in text_gen:
        if chunk:
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"


async def _sse_text(text: str, chunk: int = 6) -> AsyncGenerator[str, None]:
    """Stream static text as SSE (rule_based)."""
    words = text.split(" ")
    buf   = []
    for w in words:
        buf.append(w)
        if len(buf) >= chunk:
            yield f"data: {json.dumps({'delta': ' '.join(buf) + ' '})}\n\n"
            buf = []
            await asyncio.sleep(0.018)
    if buf:
        yield f"data: {json.dumps({'delta': ' '.join(buf)})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers():
    """ตรวจสอบว่า provider ไหนพร้อมใช้งาน"""
    return {
        "providers": [
            {
                "id":        "openai",
                "name":      f"OpenAI {OPENAI_MODEL}",
                "available": bool(_OPENAI_KEY),
                "icon":      "🟢" if _OPENAI_KEY else "🔴",
            },
            {
                "id":        "anthropic",
                "name":      f"Anthropic {ANTHROPIC_MODEL}",
                "available": bool(_ANTHROPIC_KEY),
                "icon":      "🟢" if _ANTHROPIC_KEY else "🔴",
            },
            {
                "id":        "rule_based",
                "name":      "Built-in Knowledge Base",
                "available": True,
                "icon":      "🟢",
            },
        ]
    }


@router.post("/chat")
async def chat(req: ChatRequest, loader: DataLoader = Depends(get_loader)):
    """
    Main chat — auto-selects best available provider.
    provider param: "auto" | "openai" | "anthropic" | "rule_based"
    """
    mctx  = _market_context(req.ticker, loader) if req.ticker else ""
    msgs, system = _build_messages(req, mctx)

    provider = req.provider
    if provider == "auto":
        provider = "openai" if _OPENAI_KEY else ("anthropic" if _ANTHROPIC_KEY else "rule_based")

    content = ""
    used    = provider

    try:
        if provider == "openai" and _OPENAI_KEY:
            openai_msgs = [{"role": "system", "content": system}] + msgs
            async for c in _openai(openai_msgs):
                content = c
        elif provider == "anthropic" and _ANTHROPIC_KEY:
            async for c in _anthropic(system, msgs):
                content = c
        else:
            content = _rule_based(req.message, mctx)
            used    = "rule_based"
    except Exception as e:
        # Cascade fallback
        if provider != "rule_based":
            content = _rule_based(req.message, mctx)
            used    = "rule_based_fallback"

    return {
        "role":     "assistant",
        "content":  content,
        "provider": used,
        "ticker":   req.ticker,
        "ts":       datetime.utcnow().isoformat(),
    }


@router.get("/stream")
async def stream_chat(
    message:  str = Query(..., min_length=1),
    ticker:   Optional[str] = Query(None),
    provider: str = Query("auto"),
    loader:   DataLoader = Depends(get_loader),
):
    """Streaming SSE — typewriter effect."""
    mctx  = _market_context(ticker, loader) if ticker else ""
    req   = ChatRequest(message=message, ticker=ticker, provider=provider)  # type: ignore
    msgs, system = _build_messages(req, mctx)

    prov = provider
    if prov == "auto":
        prov = "openai" if _OPENAI_KEY else ("anthropic" if _ANTHROPIC_KEY else "rule_based")

    try:
        if prov == "openai" and _OPENAI_KEY:
            openai_msgs = [{"role": "system", "content": system}] + msgs
            return StreamingResponse(
                _sse(_openai(openai_msgs, stream=True)),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        elif prov == "anthropic" and _ANTHROPIC_KEY:
            return StreamingResponse(
                _sse(_anthropic(system, msgs, stream=True)),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
    except Exception:
        pass

    # rule_based fallback
    text = _rule_based(message, mctx)
    return StreamingResponse(
        _sse_text(text),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/benchmark")
async def benchmark(req: BenchmarkRequest, loader: DataLoader = Depends(get_loader)):
    """
    ส่งคำถามเดียว → ทดสอบทั้ง 3 providers พร้อมกัน
    เปรียบเทียบคำตอบ, latency, token usage
    """
    import time
    mctx = _market_context(req.ticker, loader) if req.ticker else ""
    cr   = ChatRequest(message=req.message, ticker=req.ticker, provider="auto")
    msgs, system = _build_messages(cr, mctx)

    async def run_openai():
        if not _OPENAI_KEY:
            return {"provider": "openai", "available": False, "content": None, "latency_ms": 0, "error": "No API key"}
        t0 = time.monotonic()
        try:
            openai_msgs = [{"role": "system", "content": system}] + msgs
            content = ""
            async for c in _openai(openai_msgs):
                content = c
            return {
                "provider":   "openai",
                "model":      OPENAI_MODEL,
                "available":  True,
                "content":    content,
                "latency_ms": round((time.monotonic() - t0) * 1000),
                "error":      None,
                "char_count": len(content),
            }
        except Exception as e:
            return {"provider": "openai", "available": False, "content": None,
                    "latency_ms": round((time.monotonic() - t0) * 1000), "error": str(e)}

    async def run_anthropic():
        if not _ANTHROPIC_KEY:
            return {"provider": "anthropic", "available": False, "content": None, "latency_ms": 0, "error": "No API key"}
        t0 = time.monotonic()
        try:
            content = ""
            async for c in _anthropic(system, msgs):
                content = c
            return {
                "provider":   "anthropic",
                "model":      ANTHROPIC_MODEL,
                "available":  True,
                "content":    content,
                "latency_ms": round((time.monotonic() - t0) * 1000),
                "error":      None,
                "char_count": len(content),
            }
        except Exception as e:
            return {"provider": "anthropic", "available": False, "content": None,
                    "latency_ms": round((time.monotonic() - t0) * 1000), "error": str(e)}

    async def run_rule_based():
        t0 = time.monotonic()
        content = _rule_based(req.message, mctx)
        return {
            "provider":   "rule_based",
            "model":      "built-in",
            "available":  True,
            "content":    content,
            "latency_ms": round((time.monotonic() - t0) * 1000),
            "error":      None,
            "char_count": len(content),
        }

    # Run all 3 in parallel
    results = await asyncio.gather(
        run_openai(),
        run_anthropic(),
        run_rule_based(),
        return_exceptions=False,
    )

    return {
        "question":   req.message,
        "ticker":     req.ticker,
        "market_ctx": mctx,
        "results":    results,
        "ts":         datetime.utcnow().isoformat(),
    }


@router.get("/suggestions")
async def suggestions(
    ticker:  Optional[str] = Query(None),
    context: Optional[str] = Query(None),
):
    base = [
        "RSI คืออะไร อ่านค่าอย่างไร?",
        "วิธีกำหนด Stop Loss ที่ดีที่สุด",
        "Kelly Criterion คืออะไร ใช้อย่างไร?",
        "Mean Reversion vs Trend Following",
        "Position Sizing คำนวณอย่างไร?",
        "Bollinger Bands Squeeze บอกอะไร?",
        "Backtest ที่ดีต้องดูอะไรบ้าง?",
        "จิตวิทยาการเทรดสำคัญอย่างไร?",
    ]
    if ticker:
        base = [
            f"วิเคราะห์ {ticker.upper()} ตอนนี้",
            f"RSI ของ {ticker.upper()} บอกอะไร?",
            f"ควร Trade {ticker.upper()} ด้วย Strategy ไหน?",
            f"Risk ของ {ticker.upper()} คือเท่าไหร่?",
            f"แนวรับแนวต้าน {ticker.upper()} อยู่ที่ไหน?",
            "Kelly Criterion คืออะไร?",
            "VaR กับ CVaR ต่างกันอย่างไร?",
        ]
    return {"suggestions": base[:8]}


@router.get("/context/{ticker}")
async def market_context(ticker: str, loader: DataLoader = Depends(get_loader)):
    ctx = _market_context(ticker, loader)
    return {"ticker": ticker.upper(), "context": ctx}
