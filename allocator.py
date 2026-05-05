"""Meta-allocator that combines the three strategies into one ensemble.

The agent will refine this -- equal-weight is a deliberately weak baseline.
"""

from __future__ import annotations

import pandas as pd


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
    index = momentum_returns.index
    weights = pd.DataFrame(
        {
            "momentum": 1.0 / 3.0,
            "mean_reversion": 1.0 / 3.0,
            "buy_hold": 1.0 / 3.0,
        },
        index=index,
    )
    return weights
