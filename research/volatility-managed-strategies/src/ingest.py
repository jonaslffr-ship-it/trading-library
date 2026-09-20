"""Ingest MarketTick 1-minute candlestick CSVs -> clean close-price series.

MarketTick candlestick format (semicolon-separated, NO header), timestamps in UTC:

    timestamp(YYYYMMDDhhmmss) ; type ; open ; high ; low ; close ; volume

``type``: 0=Bid, 1=Ask, 2=Last(Trade). Index candles use type=2 and volume=0.
One file per trading day: ``YYYYMMDD.csv`` (already regular trading hours only,
~390 one-minute bars/day). See ``data/raw/data_structure.txt`` (provider doc).
"""
from __future__ import annotations

import glob
import os

import pandas as pd

COLS = ["ts", "type", "open", "high", "low", "close", "volume"]
TYPE_LAST = 2


def load_day(path: str) -> pd.Series:
    """Read one MarketTick daily candlestick CSV -> UTC-indexed close series."""
    df = pd.read_csv(path, sep=";", header=None, names=COLS)
    df = df[df["type"] == TYPE_LAST]                       # keep Last-trade candles
    ts = pd.to_datetime(df["ts"], format="%Y%m%d%H%M%S", utc=True)
    close = pd.Series(df["close"].to_numpy(dtype="float64"), index=ts, name="close")
    return close[close > 0].sort_index()


def load_days(raw_dir: str = "data/raw", pattern: str = "*.csv") -> pd.Series:
    """Concatenate all daily candlestick CSVs (``YYYYMMDD.csv``) into one series."""
    files = sorted(glob.glob(os.path.join(raw_dir, pattern)))
    parts = [load_day(f) for f in files if os.path.basename(f)[:8].isdigit()]
    if not parts:
        raise FileNotFoundError(f"no daily YYYYMMDD.csv files in {raw_dir!r}")
    return pd.concat(parts).sort_index()
