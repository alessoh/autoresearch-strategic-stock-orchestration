import { useState } from "react";

type Experiment = {
  experiment: number;
  description?: string;
  diff?: string;
  val_sharpe_before?: number;
  val_sharpe_after?: number;
  delta?: number;
  kept?: boolean;
};

type Props = { experiments: Experiment[] };

export default function ChangeLog({ experiments }: Props) {
  const accepted = experiments.filter((e) => e.kept === true).slice().reverse();
  const [expanded, setExpanded] = useState<number | null>(null);

  if (accepted.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 text-sm text-gray-500 shadow-sm">
        No accepted improvements yet. The agent is still proposing.
      </div>
    );
  }

  const fmt = (n: number | undefined) =>
    n === undefined || n === null || Number.isNaN(n) ? "--" : n.toFixed(4);

  return (
    <div className="space-y-3">
      {accepted.map((exp) => {
        const isOpen = expanded === exp.experiment;
        const delta = exp.delta ?? 0;
        return (
          <div key={exp.experiment} className="rounded-xl border border-gray-200 bg-white shadow-sm">
            <div className="flex items-start justify-between gap-4 p-4">
              <div className="min-w-0 flex-1">
                <div className="text-xs text-gray-500">exp {exp.experiment}</div>
                <div className="mt-1 text-sm text-gray-800">{exp.description ?? "(no description)"}</div>
              </div>
              <div className="shrink-0 text-right">
                <div className="text-2xl font-bold text-ensemble">
                  {delta >= 0 ? "+" : ""}
                  {delta.toFixed(3)}
                </div>
                <div className="text-xs text-gray-500">
                  {fmt(exp.val_sharpe_before)} → {fmt(exp.val_sharpe_after)}
                </div>
              </div>
            </div>
            <div className="border-t border-gray-100 px-4 py-2">
              <button
                className="text-xs font-medium text-ensemble hover:underline"
                onClick={() => setExpanded(isOpen ? null : exp.experiment)}
              >
                {isOpen ? "Hide diff" : "Show diff"}
              </button>
              {isOpen && (
                <pre className="mt-2 overflow-x-auto rounded bg-gray-900 p-3 font-mono text-xs leading-snug text-gray-100">
                  {exp.diff ?? "(no diff captured)"}
                </pre>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
