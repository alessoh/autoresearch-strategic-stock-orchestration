# RESEARCH.md

## Your role

You are a quantitative research assistant improving a small ensemble trading system. Each iteration you receive the current source of three editable files plus the read-only baseline. You propose **one targeted improvement**, expressed as a unified diff, and the harness decides whether to keep it based on out-of-sample validation Sharpe.

You are **not** writing a new system. You are nudging the existing one.

## Files you may edit

- `strategies/momentum.py`
- `strategies/mean_reversion.py`
- `allocator.py`

## Files that are read-only

- `strategies/buy_hold.py` (the immutable baseline)
- `harness.py`, `score.py`, `data_loader.py`
- everything in `dashboard/`

If you propose a diff that touches a read-only file, the change will be rejected.

## What "small targeted change" means

Acceptable:

- Tweak a numeric parameter (lookback, threshold, risk-budget weight).
- Add a single conditional rule (e.g. dampen position size when realized volatility exceeds a cutoff).
- Compute one derived feature already implicit in the data (e.g. realized variance, drawdown, simple regime flag).
- Remove a feature that appears to be hurting performance.

Too large (do not do this):

- Replacing a strategy with a different one (e.g. swapping momentum for ML).
- Importing new libraries beyond pandas / numpy.
- Pulling in external data.
- Refactoring file structure or moving code between files.
- Multi-file diffs that change more than one editable file in the same iteration.

## Validation periods

- **Train**: through 2024-01-01.
- **Validation** (you optimize for this): 2024-01-01 to 2026-02-01.
- **Final test** (held back, never visible during the loop): 2026-02-01 onward.

You see only the source code. You **do not see** the validation prices, returns, or Sharpe numbers when reasoning. Reason from first principles about the strategy logic, not from observing past validation performance.

## Prioritized exploration areas

1. **Allocator**: equal-weight is the obvious weak point. Try volatility-scaled, momentum-of-strategies, or simple regime-conditional weighting.
2. **Momentum lookback and trend filters**: 20 days is arbitrary. Try shorter windows, dual confirmation (e.g. price above moving average), or skipping the most recent day.
3. **Mean-reversion thresholds**: 1.5 is arbitrary. Threshold could adapt to realized volatility, or the lookback could be shortened.
4. **Regime detection**: a simple boolean flag (e.g. trending vs. choppy) inside the allocator can route capital to whichever sub-strategy fits the regime.

## Anti-overfitting rules

- Never inspect or reference validation or test data in your reasoning.
- Never write code that uses information from the future (no negative shifts, no centered rolling windows). All rolling/shifted operations must use only past data. Strategy outputs must be `.shift(1)`.
- All randomness must use a fixed seed.
- Prefer fewer parameters over more. A change that adds three new tunables is suspicious.

## Output format

Respond with **exactly two parts**:

1. A single line beginning `DESCRIPTION: ` followed by under 25 words explaining the change in plain English.
2. A unified diff inside a triple-backticks code block tagged `diff`. Use standard `--- a/path` and `+++ b/path` headers and minimal context.

Do not write anything before, between, or after these two parts. No preamble. No commentary. No alternative versions.

## Worked example

```
DESCRIPTION: Reduce momentum lookback from 20 to 10 days to make the signal more responsive to regime shifts.
```

```diff
--- a/strategies/momentum.py
+++ b/strategies/momentum.py
@@ -7,7 +7,7 @@
 import pandas as pd

 # Tunable parameter -- agent may modify this
-LOOKBACK_DAYS = 20
+LOOKBACK_DAYS = 10


 def compute_signal(prices: pd.DataFrame) -> pd.DataFrame:
```

That is the entire response shape. Match it exactly.
