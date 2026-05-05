"""Meta-allocator that combines the three strategies into one ensemble.

The agent will refine this -- equal-weight is a deliberately weak baseline.
"""

from __future__ import annotations

import pandas as pd
import numpy as np



def allocate(
    momentum_returns: pd.Series,
    mean_reversion_returns: pd.Series,
    buy_hold_returns: pd.Series,
) -> pd.DataFrame:
    """Return a DataFrame of per-day weights for the three strategies.

    Each row sums to 1.0. The columns are ``momentum``,
    ``mean_reversion``, and ``buy_hold``. The baseline implementation
    is a constant equal weight across all dates.
    """
    # Compute rolling 20-day realized volatility for each strategy
    vol_lookback = 20
    mom_vol = momentum_returns.rolling(window=vol_lookback, min_periods=vol_lookback).std()
    mr_vol = mean_reversion_returns.rolling(window=vol_lookback, min_periods=vol_lookback).std()
    bh_vol = buy_hold_returns.rolling(window=vol_lookback, min_periods=vol_lookback).std()

    # Inverse volatility weights
    inv_vol = pd.DataFrame({'momentum': 1.0 / mom_vol, 'mean_reversion': 1.0 / mr_vol, 'buy_hold': 1.0 / bh_vol})
    inv_vol = inv_vol.fillna(0).replace([np.inf, -np.inf], 0)

    # Normalize to sum to 1
    row_sums = inv_vol.sum(axis=1)
    weights = inv_vol.div(row_sums, axis=0)

    # Fall back to equal weight when normalization fails
    weights = weights.fillna(1.0 / 3.0)

    index = momentum_returns.index
    return weights
