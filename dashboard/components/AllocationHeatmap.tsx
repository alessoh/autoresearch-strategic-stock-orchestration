type Row = {
  date: string;
  momentum: number;
  mean_reversion: number;
  buy_hold: number;
};

type Props = { data: Row[] };

const ROWS: { key: keyof Omit<Row, "date">; label: string; color: string }[] = [
  { key: "momentum", label: "Momentum", color: "#F0997B" },
  { key: "mean_reversion", label: "Mean-Reversion", color: "#5DCAA5" },
  { key: "buy_hold", label: "Buy & Hold", color: "#9CA3AF" },
];

const MAX_COLS = 120;

function downsample(rows: Row[], target: number): Row[] {
  if (rows.length <= target) return rows;
  const step = rows.length / target;
  const out: Row[] = [];
  for (let i = 0; i < target; i++) {
    out.push(rows[Math.floor(i * step)]);
  }
  return out;
}

function alpha(weight: number): number {
  return Math.min(1, Math.max(0.05, weight * 1.5));
}

function pctTooltip(date: string, weight: number): string {
  return `${date}  ${(weight * 100).toFixed(1)}%`;
}

export default function AllocationHeatmap({ data }: Props) {
  if (!data || data.length === 0) {
    return <div className="flex h-40 items-center justify-center text-sm text-gray-500">Loading…</div>;
  }

  const sample = downsample(data, MAX_COLS);
  const start = data[0]?.date ?? "";
  const end = data[data.length - 1]?.date ?? "";

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        {ROWS.map((row) => (
          <div key={row.key} className="flex items-center gap-3">
            <div className="w-32 shrink-0 text-xs font-medium text-gray-700">{row.label}</div>
            <div className="flex h-6 flex-1 overflow-hidden rounded">
              {sample.map((cell, idx) => (
                <div
                  key={idx}
                  title={pctTooltip(cell.date, cell[row.key])}
                  style={{
                    flex: 1,
                    backgroundColor: row.color,
                    opacity: alpha(cell[row.key]),
                  }}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between pl-32 text-xs text-gray-500">
        <span>{start}</span>
        <span>{end}</span>
      </div>
    </div>
  );
}
