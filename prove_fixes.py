#!/usr/bin/env python3
"""Re-derive each corrected claim independently and check it equals the number
now printed in the paper (the old, wrong values are shown too, for contrast).
Needs numpy + scipy. Run:  python prove_fixes.py"""
import math, os
from statistics import NormalDist
from scipy import stats
N = NormalDist(); Phi = N.cdf
phi = lambda x: math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi); ppf = N.inv_cdf
P = F = 0
def chk(name, ist, soll, tol=5e-3, rel=True):
    global P, F
    ok = (abs(ist - soll) <= tol * max(1, abs(soll))) if rel else (abs(ist - soll) <= tol)
    P += ok; F += (not ok)
    print(f" [{'PASS' if ok else 'FAIL'}] {name:52s} ist={ist:+.5g} soll(paper)={soll:+.5g}")

print("PROVE FIXES - re-derive each corrected claim vs the number now printed in the paper")
print("=" * 90)

# A1  N(d1)-N(d2) gap = phi(d1)*sigma*sqrtT (~0.023), NOT sigma*sqrtT (0.058)
S=K=100; T=21/252; r=0.04; sig=0.20; sq=sig*math.sqrt(T)
d1=(math.log(S/K)+(r+0.5*sig**2)*T)/sq; d2=d1-sq
chk("A1 gap N(d1)-N(d2) (paper ~0.023)", Phi(d1)-Phi(d2), 0.023, tol=1e-3, rel=False)
chk("A1 phi(d1)*sigma*sqrtT (paper ~0.023)", phi(d1)*sq, 0.023, tol=1e-3, rel=False)
chk("A1 sigma*sqrtT (the WRONG 0.058)", sq, 0.058, tol=1e-3, rel=False)

# A2  deep-ITM European put at r>0: gamma>0 AND theta>0
S=60; K=100; T=1; r=0.05; sig=0.20; sq=sig*math.sqrt(T)
d1=(math.log(S/K)+(r+0.5*sig**2)*T)/sq; d2=d1-sq
gamma=phi(d1)/(S*sq)
theta=(-S*phi(d1)*sig/(2*math.sqrt(T))+r*K*math.exp(-r*T)*Phi(-d2))
ok=gamma>0 and theta>0; P+=ok; F+=(not ok)
print(f" [{'PASS' if ok else 'FAIL'}] A2 deep-ITM put gamma={gamma:+.4g}>0 AND theta={theta:+.4g}/yr>0 -> 'impossible' FALSE")

# A3  ITM-call delta bottoms >1/2 then rises to 1 (not an attractor at 1/2)
S=120; K=100; T=1
dc=lambda s: Phi((math.log(S/K)+0.5*s*s*T)/(s*math.sqrt(T)))
chk("A3 min ITM-call delta (paper ~0.735, NOT 0.5)", min(dc(s) for s in [0.2,0.4,0.8,1.5]), 0.735, tol=2e-2)
chk("A3 delta at sigma=10 -> back toward 1", dc(10.0), 1.0, tol=1e-3, rel=False)

# A10  expected max of 2000 no-edge Sharpes = 0.92 (Bailey/LdP), not 1.04 (crude)
n_in=3524; M=2000; sd=math.sqrt(252.0/n_in); e=0.5772156649015329
chk("A10 E[max] Bailey/LdP (paper 0.92)", sd*((1-e)*ppf(1-1/M)+e*ppf(1-1/(M*math.e))), 0.92, tol=1e-2)
chk("A10 E[max] crude sqrt(2lnM) (old WRONG 1.04)", sd*math.sqrt(2*math.log(M)), 1.04, tol=1e-2)

# C1  fat-tail band coverage t(4)=77.0%, t(5)=74.7% inside +/-1 SD
ti=lambda nu: 100*(stats.t.cdf(math.sqrt(nu/(nu-2)),nu)-stats.t.cdf(-math.sqrt(nu/(nu-2)),nu))
chk("C1 t(4) coverage (paper 77.0%)", ti(4), 77.0, tol=0.2)
chk("C1 t(5) coverage (paper 74.7%)", ti(5), 74.7, tol=0.2)

# C2  rule-of-16 error vs sqrt(252) = +0.79%
chk("C2 rule-of-16 error (paper 0.79%)", 100*(16/math.sqrt(252)-1), 0.79, tol=0.02)

# C4  3.7 vol points squares to ~9.96 %^2/month, != 6.98
chk("C4 vol-point wedge as %^2/mo (paper ~9.96)", (18.0**2-14.3**2)/12, 9.96, tol=0.1)

# C6  two-sample t of equity Goldilocks(1.39,ci0.50) vs Stagflation(0.32,ci0.53) = 2.88
t=(1.39-0.32)/math.sqrt((0.50/1.96)**2+(0.53/1.96)**2)
chk("C6 two-sample t (paper 2.88)", t, 2.88, tol=2e-2)
chk("C6 two-sided p (paper ~0.004)", 2*(1-stats.norm.cdf(t)), 0.004, tol=1e-3, rel=False)

# --- ERRATA F6: actually OPEN the papers, so reverting a corrected NUMBER in
# the prose (not just re-deriving the arithmetic) is caught. Previously this
# script never read a paper, so a reverted errata stayed green (audit T20).
HERE = os.path.dirname(os.path.abspath(__file__))
def paper_has(name, relpath, needle):
    global P, F
    try:
        txt = open(os.path.join(HERE, relpath), encoding="utf-8").read()
    except OSError as e:
        F += 1
        print(f" [FAIL] {name:52s} could not open {relpath}: {e}")
        return
    ok = needle in txt
    P += ok; F += (not ok)
    print(f" [{'PASS' if ok else 'FAIL'}] {name:52s} paper contains {needle!r}")

paper_has("A1  gap phrase present (L2 greeks)",
          "02-options/L2-greeks-and-hedging.md", "roughly 0.023, not the 0.058")
paper_has("A10 corrected 0.92 present (ML strategy)",
          "08-strategy/L3-ml-strategy-building.md", "0.92")
paper_has("C6  two-sample t 2.88 present (macro L2)",
          "06-macro-context/L2-macro-regimes-fundamentals.md", "2.88")

# --- v1.1 second-audit corrections: one text anchor each, so reverting any of
# them (K2/K9 and the six copied-error fixes N5a-f/N6) turns this script red.
paper_has("K2  GJR corrected LR 141.6 (vol-modeling)",
          "03-volatility/L3-vol-modeling-vrp.md", "141.6")
paper_has("K9  CPI calendar-based 3.35 (macro L2)",
          "06-macro-context/L2-macro-regimes-fundamentals.md", "3.35")
paper_has("N5a two-sided month dep, April 2025 (model-to-trade)",
          "08-strategy/L3-model-to-trade.md", "dropping April 2025")
paper_has("N5b conditional break-even 0.0163 (model-to-trade)",
          "08-strategy/L3-model-to-trade.md", "0.0163")
paper_has("N5d Q015 five of six negative (research)",
          "research/volatility-managed-strategies/volatility-managed-strategies.md",
          "five of six grid points negative")
paper_has("N5e Reg-NMS tick date Nov 2026 (how-markets-move)",
          "05-market-mechanics/L1-how-markets-move.md", "November 2026")
paper_has("N5f reversal-strategy AR(1) -0.005 (overfitting)",
          "04-quant/L3-overfitting-calibration.md", "AR(1) near −0.005")
paper_has("N6  tail x251 denominator caveat (tail-hedging)",
          "08-strategy/L2-tail-hedging.md", "×251")
paper_has("N6  C4 not-Clark-West gate (research §8)",
          "research/volatility-managed-strategies/volatility-managed-strategies.md",
          "pre-registered Clark-West gate")


# ============================================================================
# v1.2 corrections — each RE-COMPUTED here (not merely grepped) and then anchored
# in the paper, per the audit's "prove, don't grep" recommendation (C1).
# ============================================================================
print("-" * 90)

# B2  raw-SVI g(k) with the PRINTED params is negative deep in the extrapolated
#     call wing (min ~ -0.05 near k=0.31): arb-free only over the traded strikes.
_a, _b, _rho, _m, _s = -0.018, 0.090, 0.185, 0.082, 0.212
def _svi_g(k):
    Sd = math.sqrt((k - _m) ** 2 + _s * _s); w = _a + _b * (_rho * (k - _m) + Sd)
    wp = _b * (_rho + (k - _m) / Sd); wpp = _b * _s * _s / Sd ** 3
    return (1 - k * wp / (2 * w)) ** 2 - (wp * wp / 4) * (1 / w + 0.25) + wpp / 2
chk("B2 SVI min g over wide scan (paper: <0 in call wing, ~ -0.05)",
    min(_svi_g(-1.0 + 0.001 * i) for i in range(2001)), -0.051, tol=6e-3)
paper_has("B2 claim confined to traded strikes (vol-modeling)",
          "03-volatility/L3-vol-modeling-vrp.md",
          "no butterfly arbitrage over the range that is actually quoted")

# B3  one-week ATM gamma drift on a TRADING-day clock: 0.141 -> 0.158, +11.8%.
_S = _K = 100.0; _r = 0.04; _sig = 0.20
def _gam(T):
    d1 = (math.log(_S / _K) + (_r + 0.5 * _sig * _sig) * T) / (_sig * math.sqrt(T))
    return phi(d1) / (_S * _sig * math.sqrt(T))
chk("B3 gamma drift per trading day (paper +11.8%)",
    100 * (_gam(4 / 252) / _gam(5 / 252) - 1), 11.8, tol=0.2)
paper_has("B3 corrected +11.8% drift (greeks-third-order)",
          "02-options/L3-greeks-third-order.md",
          "+11.8% drift from the passage of time alone")
paper_has("B5 speed estimate over-predicts (greeks-third-order)",
          "02-options/L3-greeks-third-order.md", "*over*-predicts the true 0.130")

# B4  spot-ATM 60-day at r=4%: d1,d2 BOTH positive, product > 0 -> vomma tiny & +.
_Tv = 60 / 365; _d1 = (_r + 0.5 * _sig * _sig) * _Tv / (_sig * math.sqrt(_Tv))
_d2 = _d1 - _sig * math.sqrt(_Tv); _ok = _d1 > 0 and _d2 > 0 and _d1 * _d2 > 0
P += _ok; F += (not _ok)
print(f" [{'PASS' if _ok else 'FAIL'}] B4 spot-ATM d1={_d1:+.3f}>0 AND d2={_d2:+.3f}>0 "
      f"(vomma tiny & POSITIVE, not d2=-d1)")

# B6  E[max Sharpe] finite-N (Bailey/LdP) ~1.46; crude sqrt(2 ln N) ~1.66 is only a bound.
_ssr = math.sqrt(252 / 1260); _N = 1000; _eul = 0.5772156649015329
chk("B6 Bailey/LdP finite-N E[max] (paper ~1.46)",
    _ssr * ((1 - _eul) * ppf(1 - 1 / _N) + _eul * ppf(1 - 1 / (_N * math.e))), 1.456, tol=1e-2)
chk("B6 crude sqrt(2 ln N) upper bound (~1.66)", _ssr * math.sqrt(2 * math.log(_N)), 1.662, tol=1e-2)
paper_has("B6 finite-N formula in text (backtesting)",
          "04-quant/L2-backtesting-methodology.md", "matching the finite-*N* formula")
paper_has("B8 majority-class 54.5% baseline (ml-strategy)",
          "08-strategy/L3-ml-strategy-building.md", "54.5")

# --- previously-UNANCHORED v1.1 corrections now guarded (C1): reverting any of
# K1 / K5 / K8 / K-M04 / N5c in the prose now turns this script red.
paper_has("K1  conditional VIX-standardized coverage 71.9 (vol-fundamentals)",
          "03-volatility/L1-volatility-fundamentals.md", "71.9")
paper_has("K5  charm same-option 2.9x (greeks-and-hedging)",
          "02-options/L2-greeks-and-hedging.md", "2.9×")
paper_has("K8  NFCI cell 90% pre-1990, 341/378 (macro-regimes)",
          "06-macro-context/L2-macro-regimes-fundamentals.md", "378 weeks (341)")
paper_has("K-M04 ARL0 corrected to 4,290 (algos)",
          "07-algo-development/L3-building-running-killing-algos.md", "4,290")
paper_has("N5c tail-hedging skew at same delta (tail-hedging)",
          "08-strategy/L2-tail-hedging.md", "at the same *delta*")

print("=" * 90); print(f"RESULT: {P} passed, {F} failed")
raise SystemExit(1 if F else 0)
