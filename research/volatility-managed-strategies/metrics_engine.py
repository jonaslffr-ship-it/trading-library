#!/usr/bin/env python3
"""Full performance/metric suite for the strategy campaign (QR006).

Everything the campaign reports comes from here, so every sleeve/combination is
measured identically:

  - daily-return metrics: CAGR, Vol, Sharpe, Sortino, MaxDD, Calmar, ProfitFactor,
    daily WinRate, NetProfit / EndBalance from EUR 100k.
  - trade-episode metrics: #Trades, trade WinRate, avg win / avg loss (EUR on 100k),
    CRV (avg_win/|avg_loss|), expectancy EUR/trade.  An episode is a maximal run of
    constant-sign nonzero weight (magnitude may vary).  Continuous sleeves (always
    invested) are flagged and additionally report implied round-trips from turnover.
  - Monte-Carlo (stationary fixed-block bootstrap, block=21, seed 42): end-capital
    P5/P50/P95, MaxDD median/P95, P(end<start), P(MaxDD < -20%).
  - PSR/DSR/PBO/bootstrap-CI re-exported from validation.py (single implementation).

Pre-registered in vault note QR006 before any campaign backtest was run.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from validation import psr, deflated_sharpe, pbo_cscv, block_bootstrap_sharpe_ci, _sr  # noqa: F401

PPY = 252
CAPITAL = 100_000.0


# ---------------------------------------------------------------- daily metrics
def perf_daily(ret: pd.Series, capital: float = CAPITAL) -> dict:
    """Metric suite on net daily simple returns."""
    r = ret.dropna()
    n = len(r)
    if n == 0:
        return {}
    eq = (1.0 + r).cumprod()
    end_balance = capital * eq.iloc[-1]
    cagr = eq.iloc[-1] ** (PPY / n) - 1.0
    sd = r.std()
    vol = sd * np.sqrt(PPY)
    sharpe = r.mean() / sd * np.sqrt(PPY) if sd > 0 else np.nan
    dn = r[r < 0].std()
    sortino = r.mean() / dn * np.sqrt(PPY) if dn and dn > 0 else np.nan
    dd = (eq / eq.cummax() - 1.0).min()
    calmar = cagr / abs(dd) if dd < 0 else np.nan
    neg = r[r < 0].sum()
    pf = r[r > 0].sum() / abs(neg) if neg != 0 else np.nan
    win = (r > 0).mean()
    return {
        "CAGR": cagr, "Vol": vol, "Sharpe": sharpe, "Sortino": sortino,
        "MaxDD": dd, "Calmar": calmar, "ProfitFactor": pf, "WinRate_d": win,
        "N_days": n, "NetProfit_EUR": end_balance - capital, "EndBalance_EUR": end_balance,
    }


# ---------------------------------------------------------------- trade episodes
def trade_stats(strat_ret: pd.Series, weights: pd.Series,
                capital: float = CAPITAL) -> dict:
    """Episode-level trade statistics.

    Episode = maximal run of nonzero same-sign weight.  Each episode's PnL is
    computed as if entered with `capital` (standard per-trade statistics, avoids
    path dependence).  Flat periods contribute nothing.
    """
    df = pd.DataFrame({"r": strat_ret, "w": weights}).dropna()
    sign = np.sign(df["w"]).replace(0, np.nan)
    # episode id increments whenever sign changes or becomes nan (flat)
    grp = (sign != sign.shift()).cumsum()[sign.notna()]
    pnl = []
    for _, seg in df.loc[grp.index].groupby(grp):
        pnl.append(capital * ((1.0 + seg["r"]).prod() - 1.0))
    pnl = np.array(pnl)
    n = len(pnl)
    if n == 0:
        return {"Trades": 0}
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    avg_win = wins.mean() if len(wins) else np.nan
    avg_loss = losses.mean() if len(losses) else np.nan
    crv = avg_win / abs(avg_loss) if len(wins) and len(losses) else np.nan
    # implied round-trips from turnover (for continuous sleeves)
    dw = df["w"].diff().abs()
    rt_py = dw.mean() * PPY / 2.0
    always_in = bool((sign.notna()).mean() > 0.95 and n <= 3)
    return {
        "Trades": n,
        "WinRate_t": float((pnl > 0).mean()),
        "AvgWin_EUR": avg_win, "AvgLoss_EUR": avg_loss, "CRV": crv,
        "Expectancy_EUR": float(pnl.mean()),
        "RoundTrips_pa": float(rt_py),
        "ContinuousSleeve": always_in,
    }


# ---------------------------------------------------------------- Monte-Carlo
def monte_carlo(ret: pd.Series, n_paths: int = 5000, block: int = 21,
                capital: float = CAPITAL, seed: int = 42) -> dict:
    """Fixed-block bootstrap of the daily net return series (same style as
    validation.block_bootstrap_sharpe_ci) -> distribution of end capital and MaxDD
    over the SAME horizon length as the observed series."""
    r = ret.dropna().to_numpy(float)
    T = len(r)
    if T < 2 * block:
        return {}
    rng = np.random.RandomState(seed)
    nb = int(np.ceil(T / block))
    end_cap = np.empty(n_paths)
    maxdd = np.empty(n_paths)
    for b in range(n_paths):
        starts = rng.randint(0, T - block + 1, nb)
        samp = np.concatenate([r[s:s + block] for s in starts])[:T]
        eq = np.cumprod(1.0 + samp)
        end_cap[b] = capital * eq[-1]
        maxdd[b] = (eq / np.maximum.accumulate(eq) - 1.0).min()
    yrs = T / PPY
    cagr = (end_cap / capital) ** (1.0 / yrs) - 1.0
    return {
        "MC_End_P5": float(np.percentile(end_cap, 5)),
        "MC_End_P50": float(np.percentile(end_cap, 50)),
        "MC_End_P95": float(np.percentile(end_cap, 95)),
        "MC_CAGR_P5": float(np.percentile(cagr, 5)),
        "MC_CAGR_P50": float(np.percentile(cagr, 50)),
        "MC_MaxDD_P50": float(np.percentile(maxdd, 50)),
        "MC_MaxDD_P95": float(np.percentile(maxdd, 5)),   # 5th pct = worst tail
        "MC_P_Loss": float((end_cap < capital).mean()),
        "MC_P_DD20": float((maxdd < -0.20).mean()),
    }


def full_report(strat_ret: pd.Series, weights: pd.Series | None = None,
                mc: bool = False, capital: float = CAPITAL) -> dict:
    out = perf_daily(strat_ret, capital)
    if weights is not None:
        out.update(trade_stats(strat_ret, weights, capital))
    if mc:
        out.update(monte_carlo(strat_ret, capital=capital))
    return out
