"""CLI scoring entry point.

Runs a full backtest, prints the Sharpe summary as JSON, and optionally
writes the dashboard data files. The AutoResearch loop reads
``latest_score.json`` after every iteration to decide whether to keep or
roll back the proposed change.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from data_loader import load_prices
from harness import BacktestResult, run_backtest

DASHBOARD_DATA_DIR = Path("dashboard/public/data")
LATEST_SCORE_PATH = Path("latest_score.json")


def _records(df: pd.DataFrame) -> list:
    """Convert a DataFrame indexed by date into a list of JSON-friendly records."""
    out = df.copy()
    out.insert(0, "date", out.index.strftime("%Y-%m-%d"))
    return out.reset_index(drop=True).to_dict(orient="records")


def _write_dashboard(result: BacktestResult) -> None:
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    race = _records(result.val_cumulative.round(6))
    weights = _records(result.val_weights.round(6))
    summary = {
        **result.to_dict(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    (DASHBOARD_DATA_DIR / "race.json").write_text(json.dumps(race))
    (DASHBOARD_DATA_DIR / "weights.json").write_text(json.dumps(weights))
    (DASHBOARD_DATA_DIR / "summary.json").write_text(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ensemble backtest and write scoring output.")
    parser.add_argument(
        "--write-dashboard",
        action="store_true",
        help="Also write race.json, weights.json, summary.json into dashboard/public/data/",
    )
    args = parser.parse_args()

    prices = load_prices()
    result = run_backtest(prices)
    summary = result.to_dict()

    LATEST_SCORE_PATH.write_text(json.dumps(summary))
    if args.write_dashboard:
        _write_dashboard(result)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
