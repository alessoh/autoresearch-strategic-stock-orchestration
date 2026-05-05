"""Historical price loader with on-disk caching.

Downloads adjusted Close prices for a fixed universe of liquid ETFs from
Yahoo Finance and caches the result as a parquet file. Subsequent calls
read from the cache so the AutoResearch loop never re-hits the network
during an experiment.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

TICKERS = ["SPY", "QQQ", "IWM", "EFA", "TLT"]
START_DATE = "2015-01-01"
END_DATE = "2026-04-30"
CACHE_DIR = Path("data")
CACHE_PATH = CACHE_DIR / "prices.parquet"


def load_prices(force_refresh: bool = False) -> pd.DataFrame:
    """Return a wide DataFrame of daily Close prices indexed by date.

    Columns are tickers in :data:`TICKERS`. The first call downloads from
    Yahoo Finance; later calls read the parquet cache.
    """
    if CACHE_PATH.exists() and not force_refresh:
        prices = pd.read_parquet(CACHE_PATH)
        prices.index = pd.to_datetime(prices.index)
        return prices

    import yfinance as yf

    np.random.seed(42)
    raw = yf.download(
        TICKERS,
        start=START_DATE,
        end=END_DATE,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
    )

    if isinstance(raw.columns, pd.MultiIndex):
        closes = pd.DataFrame({t: raw[t]["Close"] for t in TICKERS if t in raw.columns.get_level_values(0)})
    else:
        closes = raw[["Close"]].rename(columns={"Close": TICKERS[0]})

    closes = closes.sort_index().ffill().dropna(how="all")
    closes = closes[[t for t in TICKERS if t in closes.columns]]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    closes.to_parquet(CACHE_PATH)
    return closes


def split_train_validation(
    prices: pd.DataFrame, split_date: str = "2024-01-01"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split a price DataFrame into train and validation halves at ``split_date``."""
    split_ts = pd.Timestamp(split_date)
    train = prices.loc[prices.index < split_ts].copy()
    val = prices.loc[prices.index >= split_ts].copy()
    return train, val


def _summary(prices: pd.DataFrame) -> str:
    train, val = split_train_validation(prices)
    return (
        f"rows={len(prices)}  tickers={list(prices.columns)}\n"
        f"date range: {prices.index.min().date()} -> {prices.index.max().date()}\n"
        f"train rows={len(train)}  val rows={len(val)}"
    )


if __name__ == "__main__":
    prices = load_prices()
    print(_summary(prices))
