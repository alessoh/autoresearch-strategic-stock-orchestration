# AutoResearch Strategic Stock Orchestration

Three traders, one referee. The agent runs the competition and improves the rules overnight.

A self-improving multi-agent trading system built for the AI Agent Olympics 2026 hackathon. Three trading strategies (momentum, mean-reversion, buy-and-hold) compete for capital from a meta-allocator. An overnight AutoResearch loop calls the Anthropic API, asks for one targeted improvement per iteration, applies the proposed diff, runs a backtest, and keeps the change only if validation Sharpe improves. Every experiment is logged to JSON; a Vercel-deployed Next.js dashboard reads those logs and shows the race, allocation heatmap, learning curve, and changelog.

The methodology is inspired by Andrej Karpathy's nanochat: small codebase, fast iteration, self-improvement driven by measurable metrics, full git history of every experiment.

## Quickstart

```bash
# 1. Clone and install
git clone <your-repo-url>
cd autoresearch-strategic-stock-orchestration
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Cache the price history (one-time, ~10 seconds)
python data_loader.py

# 3. Run a baseline backtest and write dashboard data
python score.py --write-dashboard

# 4. Run the AutoResearch loop manually (small batch)
export ANTHROPIC_API_KEY=sk-ant-...
python autoresearch_loop.py --iterations 3

# 5. Run the AutoResearch loop overnight (8 hours, ~100 iterations)
python autoresearch_loop.py --iterations 100 --overnight

# 6. Build the dashboard
cd dashboard
npm install
npm run build
npm run dev   # http://localhost:3000
```

## Architecture

**Strategies.** Each of the three modules in `strategies/` exposes a single `compute_signal(prices)` function returning per-asset positions in `{-1, 0, +1}`. Every signal is shifted forward by one trading day so today's decision uses only data through yesterday. This eliminates lookahead bias at the strategy layer; the harness does not need to enforce it. `buy_hold.py` is intentionally read-only and acts as the unmoving reference baseline.

**Allocator.** `allocator.py` maps the three per-strategy return streams into per-day capital weights summing to 1.0. The baseline is a constant equal weight, which is deliberately weak so the agent has somewhere to go.

**Harness.** `harness.py` loads prices, runs every strategy, applies the allocator, builds an ensemble return series, splits it into train, validation, and held-out test windows, computes annualized Sharpe ratios for each window, and packages the result. Determinism is enforced with a fixed numpy seed.

**AutoResearch loop.** `autoresearch_loop.py` is the driver. Each iteration it sends `RESEARCH.md` plus the current source of the editable files to the Anthropic API, parses out a one-line description and a unified diff, applies the diff with `git apply`, re-runs `score.py`, compares the new validation Sharpe to the current best, commits and keeps the change if the improvement clears the threshold (0.02 by default), or runs `git reset --hard HEAD` to roll back. Every iteration is logged to `experiments.json` whether kept or rejected.

**Dashboard.** `dashboard/` is a Next.js 14 + TypeScript + Tailwind + Recharts app. On mount it fetches four JSON files from `public/data/` and renders the race chart, allocation heatmap, learning-curve staircase, and accepted-changes log. State is per-session React state; persistence is in the JSON files in the repo.

## How the loop works

The cycle each iteration:

1. Read `RESEARCH.md` and the current editable file contents.
2. Send them to Claude with a request for exactly one targeted improvement, formatted as `DESCRIPTION: ...` plus a triple-backticks `diff` block.
3. Parse the description and the diff out of the response.
4. Apply the diff with `git apply --whitespace=fix`. If it fails, log and reset.
5. Run `score.py` and read the new validation Sharpe from `latest_score.json`.
6. If the improvement is at least the threshold, `git commit` with a structured message. Otherwise `git reset --hard HEAD`. Log to `experiments.json` either way.

## Files of interest

| File | Purpose |
| --- | --- |
| `data_loader.py` | Yahoo Finance loader with parquet cache. |
| `strategies/*.py` | The three trading strategies. |
| `allocator.py` | Meta-allocator (the agent's main playground). |
| `harness.py` | Backtest engine + Sharpe computation. |
| `score.py` | CLI scoring + dashboard data writer. |
| `autoresearch_loop.py` | Overnight self-improvement driver. |
| `kraken_integration.py` | Demo shim mapping weights to Kraken xStock orders. |
| `RESEARCH.md` | Instructions Claude reads each iteration. |
| `dashboard/` | Next.js dashboard. |

## License

MIT. See `LICENSE`.
