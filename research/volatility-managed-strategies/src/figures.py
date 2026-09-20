"""Figures: RV series, ACF (long memory), OOS forecast vs. realized, loss bars,
signature plot (optional). One consistent style; save to figures/.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def rv_series(feat: pd.DataFrame, out="figures/rv_series.png") -> None:
    ax = (feat["rv"] ** 0.5 * (252 ** 0.5)).plot(lw=0.7)
    ax.set_title("Annualized realized volatility")
    ax.figure.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(ax.figure)


def oos_forecast(res: pd.DataFrame, out="figures/oos_forecast.png") -> None:
    ax = res[["actual", "pred"]].plot(lw=0.7)
    ax.set_title("OOS forecast vs. realized")
    ax.figure.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(ax.figure)


def make_all(feat, res) -> None:
    rv_series(feat)
    oos_forecast(res)
