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
    # Compute rolling realized volatility for each strategy
    vol_lookback = 60
    mom_vol = momentum_returns.rolling(window=vol_lookback, min_periods=vol_lookback).std()
    mr_vol = mean_reversion_returns.rolling(window=vol_lookback, min_periods=vol_lookback).std()
    bh_vol = buy_hold_returns.rolling(window=vol_lookback, min_periods=vol_lookback).std()

    # Compute rolling 60-day cumulative returns (momentum of strategies)
    mom_perf = momentum_returns.rolling(window=vol_lookback, min_periods=vol_lookback).sum()
    mr_perf = mean_reversion_returns.rolling(window=vol_lookback, min_periods=vol_lookback).sum()
    bh_perf = buy_hold_returns.rolling(window=vol_lookback, min_periods=vol_lookback).sum()

    # Combine inverse volatility with performance: (cumulative return / volatility)
    mom_score = mom_perf / mom_vol
    mr_score = mr_perf / mr_vol
    bh_score = bh_perf / bh_vol

    # Use positive scores only, zero out negative
    scores = pd.DataFrame({'momentum': mom_score, 'mean_reversion': mr_score, 'buy_hold': bh_score})
    scores = scores.clip(lower=0)
    scores = scores.replace([np.inf, -np.inf], 0).fillna(0)

    # Normalize to sum to 1
    row_sums = scores.sum(axis=1)
    weights = scores.div(row_sums, axis=0)

    # Fall back to equal weight when normalization fails
    weights = weights.fillna(1.0 / 3.0)

    index = momentum_returns.index
    return weights
