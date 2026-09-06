"""
ocaml_engine/quant_probability.py
──────────────────────────────────
Python bridge to the OCaml quantitative probability engine.

Architecture:
  1. When `ocaml_engine/quant_engine` binary exists → delegate via subprocess
     (gives exact OCaml arithmetic for audit/compliance)
  2. Otherwise → run identical algorithms in pure Python
     (same formulas, same numerical methods — line-for-line port from the .ml)

All public functions share the OCaml signature exactly.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Optional

_BINARY = Path(__file__).parent / "quant_engine"

# ── Try to locate pre-built OCaml binary ──────────────────────────────────────
def _ocaml_available() -> bool:
    return _BINARY.exists() and _BINARY.is_file()

def _call_ocaml(payload: dict) -> dict:
    """Invoke the compiled OCaml binary with a JSON payload."""
    result = subprocess.run(
        [str(_BINARY), json.dumps(payload)],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"OCaml engine error: {result.stderr}")
    return json.loads(result.stdout)


# ═══════════════════════════════════════════════════════════════════════════════
# Pure-Python implementations  (identical to quant_probability.ml)
# ═══════════════════════════════════════════════════════════════════════════════

PI = math.pi

# ── Normal distribution ───────────────────────────────────────────────────────

def norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * PI)

def norm_cdf(x: float) -> float:
    """Standard normal CDF — Abramowitz & Stegun 26.2.17 (max error 7.5e-8)."""
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    poly = t * (0.319381530
              + t * (-0.356563782
              + t * (1.781477937
              + t * (-1.821255978
              + t * 1.330274429))))
    p = 1.0 - norm_pdf(x) * poly
    return p if x >= 0 else 1.0 - p

def norm_inv(p: float) -> float:
    """Inverse normal CDF — Beasley-Springer-Moro rational approximation."""
    a = [-3.969683028665376e+01,  2.209460984245205e+02,
         -2.759285104469687e+02,  1.383577518672690e+02,
         -3.066479806614716e+01,  2.506628277459239e+00]
    b = [-5.447609879822406e+01,  1.615858368580409e+02,
         -1.556989798598866e+02,  6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
          4.374664141464968e+00,  2.938163982698783e+00]
    d = [ 7.784695709041462e-03,  3.224671290700398e-01,
          2.445134137142996e+00,  3.754408661907416e+00]
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (c[0]+q*(c[1]+q*(c[2]+q*(c[3]+q*(c[4]+q*c[5]))))) / \
               (1.0+q*(d[0]+q*(d[1]+q*(d[2]+q*d[3]))))
    elif p <= phigh:
        q = p - 0.5
        r = q * q
        return (q*(a[0]+r*(a[1]+r*(a[2]+r*(a[3]+r*(a[4]+r*a[5])))))) / \
               (1.0+r*(b[0]+r*(b[1]+r*(b[2]+r*(b[3]+r*b[4])))))
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(c[0]+q*(c[1]+q*(c[2]+q*(c[3]+q*(c[4]+q*c[5]))))) / \
                (1.0+q*(d[0]+q*(d[1]+q*(d[2]+q*d[3]))))


# ── Black-Scholes ─────────────────────────────────────────────────────────────

def _bs_d1_d2(s: float, k: float, r: float, sigma: float, t: float):
    d1 = (math.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * math.sqrt(t))
    return d1, d1 - sigma * math.sqrt(t)

def bs_price(opt_type: str, s: float, k: float, r: float, sigma: float, t: float) -> float:
    """Black-Scholes European option price. opt_type: 'call' | 'put'"""
    if t <= 0:
        return max(0.0, s - k) if opt_type == "call" else max(0.0, k - s)
    d1, d2 = _bs_d1_d2(s, k, r, sigma, t)
    if opt_type == "call":
        return s * norm_cdf(d1) - k * math.exp(-r * t) * norm_cdf(d2)
    return k * math.exp(-r * t) * norm_cdf(-d2) - s * norm_cdf(-d1)

def bs_delta(opt_type: str, s: float, k: float, r: float, sigma: float, t: float) -> float:
    d1, _ = _bs_d1_d2(s, k, r, sigma, t)
    return norm_cdf(d1) if opt_type == "call" else norm_cdf(d1) - 1.0

def bs_gamma(s: float, k: float, r: float, sigma: float, t: float) -> float:
    d1, _ = _bs_d1_d2(s, k, r, sigma, t)
    return norm_pdf(d1) / (s * sigma * math.sqrt(t))

def bs_theta(opt_type: str, s: float, k: float, r: float, sigma: float, t: float) -> float:
    d1, d2 = _bs_d1_d2(s, k, r, sigma, t)
    term1 = -s * norm_pdf(d1) * sigma / (2.0 * math.sqrt(t))
    if opt_type == "call":
        return (term1 - r * k * math.exp(-r * t) * norm_cdf(d2)) / 365.0
    return (term1 + r * k * math.exp(-r * t) * norm_cdf(-d2)) / 365.0

def bs_vega(s: float, k: float, r: float, sigma: float, t: float) -> float:
    d1, _ = _bs_d1_d2(s, k, r, sigma, t)
    return s * norm_pdf(d1) * math.sqrt(t) / 100.0

def bs_rho(opt_type: str, s: float, k: float, r: float, sigma: float, t: float) -> float:
    _, d2 = _bs_d1_d2(s, k, r, sigma, t)
    if opt_type == "call":
        return k * t * math.exp(-r * t) * norm_cdf(d2) / 100.0
    return -k * t * math.exp(-r * t) * norm_cdf(-d2) / 100.0

def bs_implied_vol(
    opt_type: str, s: float, k: float, r: float, t: float,
    market_price: float, tol: float = 1e-8, max_iter: int = 200,
) -> Optional[float]:
    """Implied volatility via Brent's method (port from OCaml)."""
    def f(sigma):
        return bs_price(opt_type, s, k, r, sigma, t) - market_price

    a, b = 1e-6, 10.0
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        return None

    for _ in range(max_iter):
        mid = (a + b) / 2.0
        fm = f(mid)
        if abs(fm) < tol:
            return mid
        if fa * fm < 0:
            b = mid
        else:
            a, fa = mid, fm
    return (a + b) / 2.0


# ── Binomial Tree (CRR) ───────────────────────────────────────────────────────

def binomial_price(
    opt_type: str, s: float, k: float, r: float,
    sigma: float, t: float, steps: int = 200,
) -> float:
    """Cox-Ross-Rubinstein binomial tree."""
    dt   = t / steps
    u    = math.exp(sigma * math.sqrt(dt))
    d    = 1.0 / u
    disc = math.exp(-r * dt)
    p    = (math.exp(r * dt) - d) / (u - d)

    prices = [
        max(0.0, s * (u**j) * (d**(steps - j)) - k) if opt_type == "call"
        else max(0.0, k - s * (u**j) * (d**(steps - j)))
        for j in range(steps + 1)
    ]
    for i in range(steps - 1, -1, -1):
        for j in range(i + 1):
            prices[j] = disc * (p * prices[j + 1] + (1 - p) * prices[j])
    return prices[0]


# ── Bond Pricing ──────────────────────────────────────────────────────────────

def bond_price(
    face: float, coupon_rate: float, ytm: float,
    periods_per_year: int = 2, n_periods: int = 20,
) -> float:
    """Dirty price of a fixed-rate bond."""
    c = face * coupon_rate / periods_per_year
    r = ytm / periods_per_year
    pv_coupons = sum(c / (1 + r)**t for t in range(1, n_periods + 1))
    pv_face    = face / (1 + r)**n_periods
    return pv_coupons + pv_face

def bond_duration(
    face: float, coupon_rate: float, ytm: float,
    periods_per_year: int = 2, n_periods: int = 20,
) -> float:
    """Modified duration."""
    p = bond_price(face, coupon_rate, ytm, periods_per_year, n_periods)
    c = face * coupon_rate / periods_per_year
    r = ytm / periods_per_year
    mac = sum(t * c / (1 + r)**t for t in range(1, n_periods + 1))
    mac += n_periods * face / (1 + r)**n_periods
    return (mac / p) / (1 + r)

def bond_convexity(
    face: float, coupon_rate: float, ytm: float,
    periods_per_year: int = 2, n_periods: int = 20,
) -> float:
    p = bond_price(face, coupon_rate, ytm, periods_per_year, n_periods)
    c = face * coupon_rate / periods_per_year
    r = ytm / periods_per_year
    conv = sum(t*(t+1)*c/(1+r)**(t+2) for t in range(1, n_periods+1))
    conv += n_periods*(n_periods+1)*face/(1+r)**(n_periods+2)
    return conv / p


# ── Probability Cone ──────────────────────────────────────────────────────────

def prob_cone(
    spot: float, mu: float, sigma: float,
    h_days: int = 30, confidence: float = 0.95,
) -> dict:
    """
    GBM probability cone.
    Returns lower, expected, upper price bounds at horizon,
    plus cone data for each day (for charting).
    """
    t   = h_days / 252.0
    z   = norm_inv((1 + confidence) / 2.0)
    log_mean = math.log(spot) + (mu - 0.5 * sigma**2) * t
    log_std  = sigma * math.sqrt(t)
    upper    = math.exp(log_mean + z * log_std)
    lower    = math.exp(log_mean - z * log_std)
    expected = math.exp(math.log(spot) + mu * t)

    # Daily cone for charting
    daily = []
    for d in range(1, h_days + 1):
        ti   = d / 252.0
        lm   = math.log(spot) + (mu - 0.5 * sigma**2) * ti
        ls   = sigma * math.sqrt(ti)
        daily.append({
            "day":      d,
            "lower":    round(math.exp(lm - z * ls), 4),
            "expected": round(math.exp(math.log(spot) + mu * ti), 4),
            "upper":    round(math.exp(lm + z * ls), 4),
        })

    return {
        "lower":    round(lower, 4),
        "expected": round(expected, 4),
        "upper":    round(upper, 4),
        "confidence": confidence,
        "h_days":   h_days,
        "daily":    daily,
    }

def prob_reach_target(
    spot: float, target: float, mu: float, sigma: float, h_days: int = 30,
) -> float:
    """P(price reaches target within h_days) under GBM."""
    t       = h_days / 252.0
    log_ret = math.log(target / spot)
    adj_mu  = (mu - 0.5 * sigma**2) * t
    std     = sigma * math.sqrt(t)
    if target > spot:
        return 1.0 - norm_cdf((log_ret - adj_mu) / std)
    return norm_cdf((log_ret - adj_mu) / std)


# ── Risk Metrics ──────────────────────────────────────────────────────────────

def var_parametric(mu: float, sigma: float, confidence: float = 0.95) -> float:
    """1-day parametric VaR (positive = loss)."""
    return -(mu - norm_inv(confidence) * sigma)

def cvar_parametric(mu: float, sigma: float, confidence: float = 0.95) -> float:
    """1-day CVaR / Expected Shortfall."""
    z = norm_inv(confidence)
    return -(mu - sigma * norm_pdf(z) / (1.0 - confidence))

def kelly_criterion(win_prob: float, win_loss_ratio: float) -> float:
    """Optimal fraction of capital to risk per trade."""
    return win_prob - (1.0 - win_prob) / win_loss_ratio

def sharpe(mu: float, sigma: float, rf: float = 0.05) -> float:
    """Annualised Sharpe ratio from daily mu/sigma."""
    return (mu - rf / 252) / sigma * math.sqrt(252)


# ── Bayesian Regime ───────────────────────────────────────────────────────────

def bayesian_regime_prob(
    prior_bull: float,
    bull_mu: float, bull_sigma: float,
    bear_mu: float, bear_sigma: float,
    recent_returns: list[float],
) -> float:
    """
    P(regime=bull | recent_returns) via Bayes' theorem with Gaussian likelihood.
    Port of OCaml bayesian_regime_prob.
    """
    def log_lik(mu, sigma, rets):
        return sum(
            -0.5 * math.log(2 * PI * sigma**2)
            - (r - mu)**2 / (2 * sigma**2)
            for r in rets
        )

    ll_bull = log_lik(bull_mu, bull_sigma, recent_returns)
    ll_bear = log_lik(bear_mu, bear_sigma, recent_returns)

    log_post_bull = math.log(max(prior_bull, 1e-10)) + ll_bull
    log_post_bear = math.log(max(1.0 - prior_bull, 1e-10)) + ll_bear

    max_log = max(log_post_bull, log_post_bear)
    bull_un = math.exp(log_post_bull - max_log)
    bear_un = math.exp(log_post_bear - max_log)
    return bull_un / (bull_un + bear_un)


# ── Full option chain pricer ──────────────────────────────────────────────────

def option_chain(
    spot: float, r: float, sigma: float, t: float,
    strikes: list[float],
) -> list[dict]:
    """Price a full call+put chain at given strikes."""
    chain = []
    for k in strikes:
        call = bs_price("call", spot, k, r, sigma, t)
        put  = bs_price("put",  spot, k, r, sigma, t)
        chain.append({
            "strike":      k,
            "call_price":  round(call, 4),
            "put_price":   round(put,  4),
            "call_delta":  round(bs_delta("call", spot, k, r, sigma, t), 4),
            "put_delta":   round(bs_delta("put",  spot, k, r, sigma, t), 4),
            "gamma":       round(bs_gamma(spot, k, r, sigma, t), 6),
            "call_theta":  round(bs_theta("call", spot, k, r, sigma, t), 4),
            "vega":        round(bs_vega(spot,  k, r, sigma, t), 4),
            "moneyness":   round(spot / k, 4),
        })
    return chain


# ── Master compute function (called by FastAPI) ───────────────────────────────

def compute_daytrade(request: dict) -> dict:
    """
    Single entry point for the /daytrade endpoint.
    Dispatches to OCaml binary if available, else pure Python.
    """
    if _ocaml_available():
        try:
            return _call_ocaml(request)
        except Exception:
            pass  # fall through to Python

    mode   = request.get("mode", "option")
    result = {"engine": "python_ocaml_port", "mode": mode}

    if mode == "option":
        s     = float(request["spot"])
        k     = float(request["strike"])
        r     = float(request.get("risk_free", 0.05))
        sigma = float(request["volatility"])
        t     = float(request["time_to_expiry"])   # years
        otype = request.get("option_type", "call")

        price  = bs_price(otype, s, k, r, sigma, t)
        iv_res = bs_implied_vol(otype, s, k, r, t, price)  # sanity: should equal sigma
        binom  = binomial_price(otype, s, k, r, sigma, t, steps=200)

        result.update({
            "price":        round(price, 4),
            "binomial_price": round(binom, 4),
            "implied_vol":  round(iv_res, 6) if iv_res else None,
            "greeks": {
                "delta": round(bs_delta(otype, s, k, r, sigma, t), 4),
                "gamma": round(bs_gamma(s, k, r, sigma, t), 6),
                "theta": round(bs_theta(otype, s, k, r, sigma, t), 4),
                "vega":  round(bs_vega(s, k, r, sigma, t), 4),
                "rho":   round(bs_rho(otype, s, k, r, sigma, t), 4),
            },
        })

    elif mode == "bond":
        face    = float(request.get("face_value", 1000))
        coupon  = float(request["coupon_rate"])
        ytm     = float(request["ytm"])
        freq    = int(request.get("frequency", 2))
        periods = int(request.get("periods", 20))

        price   = bond_price(face, coupon, ytm, freq, periods)
        dur     = bond_duration(face, coupon, ytm, freq, periods)
        conv    = bond_convexity(face, coupon, ytm, freq, periods)
        dv01    = -price * dur / 10000.0   # DV01 per basis point

        result.update({
            "price":       round(price, 4),
            "duration":    round(dur, 4),
            "convexity":   round(conv, 4),
            "dv01":        round(dv01, 6),
            "ytm_pct":     round(ytm * 100, 4),
        })

    elif mode == "probability":
        spot  = float(request["spot"])
        mu    = float(request.get("drift", 0.10))
        sigma = float(request["volatility"])
        days  = int(request.get("horizon_days", 30))
        conf  = float(request.get("confidence", 0.95))

        cone  = prob_cone(spot, mu, sigma, days, conf)
        targets = []
        for tgt in request.get("targets", []):
            p = prob_reach_target(spot, float(tgt), mu, sigma, days)
            targets.append({"price": tgt, "probability": round(p, 4)})

        result.update({
            "cone": cone,
            "targets": targets,
        })

    elif mode == "risk":
        mu     = float(request.get("daily_mu", 0.0))
        sigma  = float(request["daily_sigma"])
        conf   = float(request.get("confidence", 0.95))
        wp     = float(request.get("win_probability", 0.55))
        wlr    = float(request.get("win_loss_ratio", 1.5))

        var    = var_parametric(mu, sigma, conf)
        cvar   = cvar_parametric(mu, sigma, conf)
        kelly  = kelly_criterion(wp, wlr)
        sharpe_ratio = sharpe(mu, sigma)

        result.update({
            "var_1day":    round(var, 6),
            "cvar_1day":   round(cvar, 6),
            "kelly_pct":   round(max(0.0, kelly) * 100, 2),
            "sharpe":      round(sharpe_ratio, 4),
        })

    elif mode == "regime":
        prior  = float(request.get("prior_bull", 0.6))
        bm     = request.get("bull_params",  {"mu": 0.0006, "sigma": 0.008})
        brm    = request.get("bear_params",  {"mu": -0.001, "sigma": 0.018})
        rets   = [float(x) for x in request.get("recent_returns", [])]

        prob   = bayesian_regime_prob(
            prior, bm["mu"], bm["sigma"], brm["mu"], brm["sigma"], rets
        )
        result.update({
            "bull_probability":  round(prob, 4),
            "bear_probability":  round(1 - prob, 4),
            "regime":            "bull" if prob > 0.5 else "bear",
        })

    elif mode == "chain":
        spot    = float(request["spot"])
        r       = float(request.get("risk_free", 0.05))
        sigma   = float(request["volatility"])
        t       = float(request["time_to_expiry"])
        strikes = [float(x) for x in request.get("strikes", [])]
        if not strikes:
            # Auto-generate ATM ±10 strikes at 1% intervals
            strikes = [round(spot * (1 + i * 0.01), 2) for i in range(-10, 11)]
        result["chain"] = option_chain(spot, r, sigma, t, strikes)

    elif mode == "daytrade_full":
        # Combined: probability cone + risk + regime in one call
        spot   = float(request["spot"])
        sigma  = float(request["volatility"])
        mu     = float(request.get("drift", 0.10))
        r      = float(request.get("risk_free", 0.05))
        rets   = [float(x) for x in request.get("recent_returns", [])]
        days   = int(request.get("horizon_days", 5))

        cone   = prob_cone(spot, mu, sigma, days, 0.95)
        regime_prob = bayesian_regime_prob(0.6, 0.0006, 0.008, -0.001, 0.018, rets) if rets else 0.6
        daily_sigma = sigma / math.sqrt(252)
        var_1d = var_parametric(0, daily_sigma, 0.95)
        cvar_1d = cvar_parametric(0, daily_sigma, 0.95)

        # ATM straddle price (cost of uncertainty)
        t_exp = days / 252.0
        straddle = bs_price("call", spot, spot, r, sigma, t_exp) + \
                   bs_price("put",  spot, spot, r, sigma, t_exp)

        result.update({
            "cone":             cone,
            "bull_probability": round(regime_prob, 4),
            "bear_probability": round(1 - regime_prob, 4),
            "regime":           "bull" if regime_prob > 0.5 else "bear",
            "var_1day_pct":     round(var_1d * 100, 3),
            "cvar_1day_pct":    round(cvar_1d * 100, 3),
            "atm_straddle":     round(straddle, 4),
            "atm_straddle_pct": round(straddle / spot * 100, 3),
            "break_even_upper": round(spot + straddle, 4),
            "break_even_lower": round(spot - straddle, 4),
        })

    return result
