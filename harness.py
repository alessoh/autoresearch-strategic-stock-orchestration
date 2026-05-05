"""Backtest engine. Computes per-strategy returns, ensemble returns, and Sharpe ratios."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict

import numpy as np
import pandas as pd

from allocator import allocate
from strategies import buy_hold_signal, mean_reversion_signal, momentum_signal


@dataclass
class BacktestResult:
    """Container for the outputs of a single backtest run."""

    train_sharpe: float
    val_sharpe: float
    final_test_sharpe: float
    train_returns: pd.Series
    val_returns: pd.Series
    val_strategy_returns: pd.DataFrame
    val_weights: pd.DataFrame
    val_cumulative: pd.DataFrame

    def to_dict(self) -> Dict[str, float]:
        """Return just the three Sharpe numbers, rounded to 4 decimals."""
        return {
            "train_sharpe": round(float(self.train_sharpe), 4),
            "val_sharpe": round(float(self.val_sharpe), 4),
            "final_test_sharpe": round(float(self.final_test_sharpe), 4),
        }


def sharpe_ratio(returns: pd.Series) -> float:
    """Return the annualized Sharpe ratio of a return series.

    Assumes a zero risk-free rate and 252 trading days per year. Returns
    0.0 when the input is too short or has zero standard deviation.
    """
    r = pd.Series(returns).dropna()
    if len(r) < 2:
        return 0.0
    std = r.std()
    if std == 0 or np.isnan(std):
        return 0.0
    return float(np.sqrt(252) * r.mean() / std)


def compute_strategy_returns(
    prices: pd.DataFrame,
    signal_fn: Callable[[pd.DataFrame], pd.DataFrame],
) -> pd.Series:
    """Apply ``signal_fn`` to ``prices`` and return equal-weighted daily portfolio returns."""
    signals = signal_fn(prices)
    asset_returns = prices.pct_change().fillna(0.0)
    aligned_signals = signals.reindex_like(asset_returns).fillna(0.0)
    position_returns = aligned_signals * asset_returns
    portfolio = position_returns.mean(axis=1)
    return portfolio.fillna(0.0)


def run_backtest(
    prices: pd.DataFrame,
    train_end: str = "2024-01-01",
    val_end: str = "2026-02-01",
) -> BacktestResult:
    """Run all three strategies, the allocator, and return a populated :class:`BacktestResult`."""
    np.random.seed(42)

    momentum_r = compute_strategy_returns(prices, momentum_signal)
    mean_rev_r = compute_strategy_returns(prices, mean_reversion_signal)
    buy_hold_r = compute_strategy_returns(prices, buy_hold_signal)

    weights = allocate(momentum_r, mean_rev_r, buy_hold_r)
    weights = weights.reindex(momentum_r.index).ffill().fillna(1.0 / 3.0)

    ensemble_r = (
        weights["momentum"] * momentum_r
        + weights["mean_reversion"] * mean_rev_r
        + weights["buy_hold"] * buy_hold_r
    )

    train_end_ts = pd.Timestamp(train_end)
    val_end_ts = pd.Timestamp(val_end)
    train_mask = ensemble_r.index < train_end_ts
    val_mask = (ensemble_r.index >= train_end_ts) & (ensemble_r.index < val_end_ts)
    test_mask = ensemble_r.index >= val_end_ts

    train_returns = ensemble_r[train_mask]
    val_returns = ensemble_r[val_mask]
    test_returns = ensemble_r[test_mask]

    val_strategy_returns = pd.DataFrame(
        {
            "momentum": momentum_r[val_mask],
            "mean_reversion": mean_rev_r[val_mask],
            "buy_hold": buy_hold_r[val_mask],
            "ensemble": ensemble_r[val_mask],
        }
    )

    val_cumulative = (1.0 + val_strategy_returns).cumprod() - 1.0
    val_weights = weights[val_mask].copy()

    return BacktestResult(
        train_sharpe=sharpe_ratio(train_returns),
        val_sharpe=sharpe_ratio(val_returns),
        final_test_sharpe=sharpe_ratio(test_returns),
        train_returns=train_returns,
        val_returns=val_returns,
        val_strategy_returns=val_strategy_returns,
        val_weights=val_weights,
        val_cumulative=val_cumulative,
    )
