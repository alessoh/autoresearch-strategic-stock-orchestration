import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Row = {
  date: string;
  momentum: number;
  mean_reversion: number;
  buy_hold: number;
  ensemble: number;
};

type Props = { data: Row[] };

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

export default function RaceChart({ data }: Props) {
  if (!data || data.length === 0) {
    return <div className="flex h-96 items-center justify-center text-sm text-gray-500">Loading…</div>;
  }

  return (
    <div className="h-96 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="#E5E7EB" strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#6B7280" }} minTickGap={40} />
          <YAxis tick={{ fontSize: 11, fill: "#6B7280" }} tickFormatter={pct} />
          <Tooltip
            formatter={(v: number) => pct(v)}
            labelFormatter={(label: string) => label}
            contentStyle={{ fontSize: 12 }}
          />
          <Line type="monotone" dataKey="momentum" stroke="#F0997B" strokeWidth={1} dot={false} />
          <Line type="monotone" dataKey="mean_reversion" stroke="#5DCAA5" strokeWidth={1} dot={false} />
          <Line type="monotone" dataKey="buy_hold" stroke="#9CA3AF" strokeWidth={1} dot={false} />
          <Line type="monotone" dataKey="ensemble" stroke="#534AB7" strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
