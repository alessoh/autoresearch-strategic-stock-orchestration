# Hackathon demo shim. This module shows how the latest allocator weights
# would translate into paper-trade orders against Kraken's xStock pairs.
# Real execution requires Kraken CLI authentication (kraken.com/api). This
# file only prints the commands that would be run.
"""Map ensemble allocator weights into Kraken xStock paper-trade orders."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd

from data_loader import load_prices
from harness import run_backtest

TICKER_TO_XSTOCK: Dict[str, str] = {
    "SPY": "SPYx",
    "QQQ": "QQQx",
    "IWM": "IWMx",
    "EFA": "EFAx",
    "TLT": "TLTx",
}

NOTIONAL_USD = 10_000.0


def latest_weights() -> pd.Series:
    """Return the most recent row of the validation-period allocator weights."""
    prices = load_prices()
    result = run_backtest(prices)
    return result.val_weights.iloc[-1]


def build_orders(weights: pd.Series) -> List[Dict[str, float]]:
    """Build a list of dry-run order dicts mapping each ticker to a notional dollar size."""
    orders = []
    per_strategy_dollars = {col: NOTIONAL_USD * float(weights[col]) for col in weights.index}
    asset_share = per_strategy_dollars["buy_hold"] / len(TICKER_TO_XSTOCK)

    for ticker, xstock in TICKER_TO_XSTOCK.items():
        orders.append(
            {
                "symbol": xstock,
                "underlying": ticker,
                "side": "buy",
                "type": "market",
                "notional_usd": round(asset_share, 2),
            }
        )
    return orders


def execute_via_kraken_cli(orders: List[Dict[str, float]], dry_run: bool = True) -> None:
    """Print the kraken CLI commands. With ``dry_run=True`` nothing is sent."""
    for o in orders:
        cmd = (
            f"kraken trade place --pair {o['symbol']}/USD "
            f"--side {o['side']} --type {o['type']} "
            f"--notional {o['notional_usd']}"
        )
        prefix = "[dry-run] " if dry_run else ""
        print(prefix + cmd)


if __name__ == "__main__":
    weights = latest_weights()
    print("Latest allocator weights:")
    print(weights.round(4).to_string())
    print()

    orders = build_orders(weights)
    print("Generated orders:")
    for o in orders:
        print(f"  {o}")
    print()

    print("Kraken CLI dry-run:")
    execute_via_kraken_cli(orders, dry_run=True)
