"""Momentum signal: long when recent mean return is positive, short when negative."""

from __future__ import annotations

import pandas as pd

# Tunable parameter -- agent may modify this
LOOKBACK_DAYS = 20


def compute_signal(prices: pd.DataFrame) -> pd.DataFrame:
    """Return +1 / 0 / -1 momentum signals for each (date, ticker).

    Signals are shifted forward by one day so that the position taken on
    day ``t`` is determined only by information available through day
    ``t-1``. This eliminates lookahead bias at the strategy layer.
    """
    returns = prices.pct_change()
    rolling_mean = returns.rolling(window=LOOKBACK_DAYS, min_periods=LOOKBACK_DAYS).mean()

    # Trend filter: 50-day price moving average
    price_ma = prices.rolling(window=50, min_periods=50).mean()

    signal = rolling_mean.copy()
    signal[rolling_mean > 0] = 1
    signal[rolling_mean < 0] = -1
    signal[rolling_mean == 0] = 0
    # Only allow longs when price is above 50-day MA
    signal[(signal == 1) & (prices < price_ma)] = 0
    signal = signal.fillna(0)

    return signal.shift(1).fillna(0)
