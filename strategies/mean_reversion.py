"""Mean-reversion signal: fade extreme z-scored deviations from a rolling mean."""

from __future__ import annotations

import pandas as pd

# Tunable parameters -- agent may modify these
LOOKBACK_DAYS = 10
ZSCORE_THRESHOLD = 1.5


def compute_signal(prices: pd.DataFrame) -> pd.DataFrame:
    """Return +1 / 0 / -1 mean-reversion signals for each (date, ticker).

    The z-score of price relative to its trailing rolling window is the
    decision variable. When price sits below ``-ZSCORE_THRESHOLD`` the
    asset is considered oversold and we go long; above
    ``+ZSCORE_THRESHOLD`` it is overbought and we go short. Signals are
    shifted forward by one day to prevent lookahead bias.
    """
    rolling_mean = prices.rolling(window=LOOKBACK_DAYS, min_periods=LOOKBACK_DAYS).mean()
    rolling_std = prices.rolling(window=LOOKBACK_DAYS, min_periods=LOOKBACK_DAYS).std()
    zscore = (prices - rolling_mean) / rolling_std

    signal = zscore.copy()
    signal[:] = 0
    signal[zscore < -ZSCORE_THRESHOLD] = 1
    signal[zscore > ZSCORE_THRESHOLD] = -1
    signal = signal.fillna(0)

    return signal.shift(1).fillna(0)
