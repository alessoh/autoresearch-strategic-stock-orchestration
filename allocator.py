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

    # Regime detection: high volatility across strategies suggests choppy markets
    avg_vol = (mom_vol + mr_vol + bh_vol) / 3.0
    vol_threshold = avg_vol.rolling(window=120, min_periods=120).quantile(0.75)
    high_vol_regime = avg_vol > vol_threshold

    # In high-vol regimes, tilt toward buy-hold to reduce turnover
    regime_tilt = pd.DataFrame({'momentum': 1.0, 'mean_reversion': 1.0, 'buy_hold': 1.0}, index=momentum_returns.index)
    regime_tilt.loc[high_vol_regime, 'buy_hold'] = 2.0
    regime_tilt.loc[high_vol_regime, 'momentum'] = 0.5
    regime_tilt.loc[high_vol_regime, 'mean_reversion'] = 0.5

    # Compute rolling 60-day cumulative returns (momentum of strategies)
    mom_perf = momentum_returns.ewm(span=vol_lookback, min_periods=vol_lookback).mean() * vol_lookback
    mr_perf = mean_reversion_returns.ewm(span=vol_lookback, min_periods=vol_lookback).mean() * vol_lookback
    bh_perf = buy_hold_returns.ewm(span=vol_lookback, min_periods=vol_lookback).mean() * vol_lookback

    # Combine inverse volatility with performance: (cumulative return / volatility)
    mom_score = mom_perf / mom_vol
    mr_score = mr_perf / mr_vol
    bh_score = bh_perf / bh_vol

    # Use positive scores only, zero out negative
    scores = pd.DataFrame({'momentum': mom_score, 'mean_reversion': mr_score, 'buy_hold': bh_score})

    # Apply regime tilt
    scores = scores * regime_tilt
    scores = scores.clip(lower=0)
    scores = scores.replace([np.inf, -np.inf], 0).fillna(0)

    # Normalize to sum to 1
    row_sums = scores.sum(axis=1)
    weights = scores.div(row_sums, axis=0)

    # Fall back to equal weight when normalization fails
    weights = weights.fillna(1.0 / 3.0)

    index = momentum_returns.index
    return weights
