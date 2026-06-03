import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ChartSpec } from "../types";

type Props = {
  columns: string[];
  rows: (string | number | null)[][];
  spec: ChartSpec;
};

const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f97316",
];

export function ChartView({ columns, rows, spec }: Props) {
  if (spec.type === "none" || rows.length === 0) {
    return <div className="empty">No chart for this result.</div>;
  }

  const x = spec.x && columns.includes(spec.x) ? spec.x : columns[0];
  const y = spec.y && columns.includes(spec.y) ? spec.y : columns[1];
  if (!x || !y) {
    return <div className="empty">Not enough columns to chart.</div>;
  }

  const data = rows.map((r) => {
    const obj: Record<string, unknown> = {};
    columns.forEach((c, i) => {
      obj[c] = r[i];
    });
    return obj;
  });

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={300}>
        {renderChart(spec.type, data, x, y)}
      </ResponsiveContainer>
    </div>
  );
}

function renderChart(
  type: ChartSpec["type"],
  data: Record<string, unknown>[],
  x: string,
  y: string,
) {
  switch (type) {
    case "bar":
      return (
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey={x} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey={y} fill={COLORS[0]} radius={[4, 4, 0, 0]} />
        </BarChart>
      );
    case "line":
      return (
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey={x} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey={y}
            stroke={COLORS[0]}
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      );
    case "pie":
      return (
        <PieChart>
          <Tooltip />
          <Legend />
          <Pie data={data} dataKey={y} nameKey={x} outerRadius={100} label>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      );
    default:
      return <></>;
  }
}
