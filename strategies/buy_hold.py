# DO NOT EDIT -- this file must remain a pure baseline so the agent has a reference point.
"""Buy-and-hold baseline: always long, every asset, every day."""

from __future__ import annotations

import pandas as pd


def compute_signal(prices: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of all 1s with the same shape as ``prices``."""
    signal = pd.DataFrame(1, index=prices.index, columns=prices.columns)
    return signal
