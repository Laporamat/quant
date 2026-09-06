# OCaml Quantitative Probability Engine

Pure-OCaml implementation of quantitative finance algorithms.

## Build

```bash
# Install OCaml + opam (Windows via Diskuv or WSL recommended)
opam install ocamlfind
ocamlfind ocamlopt -package str -linkpkg quant_probability.ml -o quant_engine

# Self-test
./quant_engine
```

## Python integration

The Python bridge (`quant_probability.py`) reimplements all algorithms
in Python with identical signatures. When `quant_engine` binary is present,
the bridge calls it via subprocess for validated output. Otherwise it falls
back to the native Python implementation.

## Algorithms

| Algorithm | Function |
|-----------|---------|
| Normal CDF/PDF/InvCDF | `norm_cdf`, `norm_pdf`, `norm_inv` |
| Black-Scholes (call/put) | `bs_price` |
| Greeks (Δ,Γ,Θ,ν,ρ) | `bs_delta/gamma/theta/vega/rho` |
| Implied Volatility | `bs_implied_vol` (Brent's method) |
| Binomial Tree (CRR) | `binomial_price` |
| Bond Price/Duration/Convexity | `bond_price/duration/convexity` |
| Probability Cone (GBM) | `prob_cone` |
| Target Probability | `prob_reach_target` |
| VaR / CVaR (parametric) | `var_parametric`, `cvar_parametric` |
| Kelly Criterion | `kelly_criterion` |
| Bayesian Regime Probability | `bayesian_regime_prob` |
