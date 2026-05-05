import { useEffect, useState } from "react";
import RaceChart from "../components/RaceChart";
import AllocationHeatmap from "../components/AllocationHeatmap";
import StaircaseChart from "../components/StaircaseChart";
import ChangeLog from "../components/ChangeLog";

type RaceRow = {
  date: string;
  momentum: number;
  mean_reversion: number;
  buy_hold: number;
  ensemble: number;
};

type WeightRow = {
  date: string;
  momentum: number;
  mean_reversion: number;
  buy_hold: number;
};

type Experiment = {
  experiment: number;
  timestamp: string;
  description?: string;
  diff?: string;
  val_sharpe_before?: number;
  val_sharpe_after?: number;
  delta?: number;
  status: string;
  kept?: boolean;
};

type Summary = {
  train_sharpe: number;
  val_sharpe: number;
  final_test_sharpe: number;
  generated_at: string;
};

async function safeFetch<T>(url: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(url);
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

export default function Home() {
  const [race, setRace] = useState<RaceRow[]>([]);
  const [weights, setWeights] = useState<WeightRow[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    Promise.all([
      safeFetch<RaceRow[]>("/data/race.json", []),
      safeFetch<WeightRow[]>("/data/weights.json", []),
      safeFetch<Experiment[]>("/data/experiments.json", []),
      safeFetch<Summary | null>("/data/summary.json", null),
    ]).then(([r, w, e, s]) => {
      setRace(r);
      setWeights(w);
      setExperiments(e);
      setSummary(s);
    });
  }, []);

  const stat = (label: string, value: string, accent = false) => (
    <div className="flex flex-col">
      <span className="text-xs uppercase tracking-wider text-gray-500">{label}</span>
      <span className={accent ? "text-2xl font-semibold text-ensemble" : "text-2xl font-semibold text-gray-800"}>
        {value}
      </span>
    </div>
  );

  const fmt = (n: number | undefined | null) =>
    n === undefined || n === null || Number.isNaN(n) ? "--" : n.toFixed(4);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <h1 className="text-2xl font-bold text-ensemble">AutoResearch Strategic Stock Orchestration</h1>
          <p className="mt-1 text-sm text-gray-600">
            Three traders, one referee. The agent runs the competition and improves the rules overnight.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-12 px-6 py-10">
        <section className="grid grid-cols-2 gap-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm md:grid-cols-4">
          {stat("Train Sharpe", fmt(summary?.train_sharpe))}
          {stat("Validation Sharpe", fmt(summary?.val_sharpe), true)}
          {stat("Final Test Sharpe", fmt(summary?.final_test_sharpe))}
          {stat("Experiments", String(experiments.length))}
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-800">The Race</h2>
          <p className="mb-4 text-sm text-gray-600">
            Cumulative validation-period returns for each strategy and the ensemble.
          </p>
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <RaceChart data={race} />
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-800">Allocation Over Time</h2>
          <p className="mb-4 text-sm text-gray-600">
            Daily capital weights chosen by the meta-allocator. Darker means more weight.
          </p>
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <AllocationHeatmap data={weights} />
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-800">AutoResearch Loop Progress</h2>
          <p className="mb-4 text-sm text-gray-600">
            Best-so-far validation Sharpe across all kept experiments.
          </p>
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <StaircaseChart experiments={experiments} />
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-800">What the Agent Found</h2>
          <p className="mb-4 text-sm text-gray-600">
            Accepted improvements, newest first. Click any entry to inspect the diff.
          </p>
          <ChangeLog experiments={experiments} />
        </section>

        <footer className="pt-6 text-center text-xs text-gray-500">
          Built for AI Agent Olympics 2026 &middot; Inspired by Karpathy&apos;s nanochat methodology
        </footer>
      </main>
    </div>
  );
}
