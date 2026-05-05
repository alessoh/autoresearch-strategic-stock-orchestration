import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Experiment = {
  experiment: number;
  status: string;
  kept?: boolean;
  val_sharpe_after?: number;
};

type Props = { experiments: Experiment[] };

export default function StaircaseChart({ experiments }: Props) {
  const usable = experiments.filter(
    (e) => e.status === "ok" && typeof e.val_sharpe_after === "number"
  );

  if (usable.length === 0) {
    return <div className="flex h-72 items-center justify-center text-sm text-gray-500">No experiments yet…</div>;
  }

  let bestSoFar = -Infinity;
  const series = usable.map((e) => {
    if (e.kept && (e.val_sharpe_after as number) > bestSoFar) {
      bestSoFar = e.val_sharpe_after as number;
    }
    return {
      experiment: e.experiment,
      best: bestSoFar === -Infinity ? null : Number(bestSoFar.toFixed(4)),
    };
  });

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={series} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="#E5E7EB" strokeDasharray="3 3" />
          <XAxis
            dataKey="experiment"
            label={{ value: "Experiment #", position: "insideBottom", offset: -2, fontSize: 11, fill: "#6B7280" }}
            tick={{ fontSize: 11, fill: "#6B7280" }}
          />
          <YAxis tick={{ fontSize: 11, fill: "#6B7280" }} />
          <Tooltip contentStyle={{ fontSize: 12 }} />
          <Area
            type="stepAfter"
            dataKey="best"
            stroke="#534AB7"
            strokeWidth={2}
            fill="#534AB7"
            fillOpacity={0.2}
            connectNulls
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
