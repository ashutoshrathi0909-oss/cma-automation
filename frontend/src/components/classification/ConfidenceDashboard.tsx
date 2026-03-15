"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { ConfidenceSummary } from "@/types";

interface ConfidenceDashboardProps {
  summary: ConfidenceSummary;
}

const SEGMENTS = [
  { key: "high_confidence", label: "High Confidence", color: "#22c55e" },
  { key: "medium_confidence", label: "Medium", color: "#f59e0b" },
  { key: "needs_review", label: "Needs Review", color: "#ef4444" },
] as const;

export function ConfidenceDashboard({ summary }: ConfidenceDashboardProps) {
  const data = SEGMENTS.map((s) => ({
    name: s.label,
    value: summary[s.key],
    color: s.color,
  })).filter((d) => d.value > 0);

  const approvedPct =
    summary.total > 0
      ? Math.round(((summary.approved + summary.corrected) / summary.total) * 100)
      : 0;

  return (
    <div className="space-y-4">
      {/* Donut chart */}
      {summary.total > 0 ? (
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={85}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend iconType="circle" iconSize={10} />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex h-[220px] items-center justify-center text-sm text-muted-foreground">
          No classifications yet
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
        {[
          { label: "Total", value: summary.total, color: "text-foreground" },
          { label: "High", value: summary.high_confidence, color: "text-green-600" },
          { label: "Medium", value: summary.medium_confidence, color: "text-amber-600" },
          { label: "Doubts", value: summary.needs_review, color: "text-red-600" },
          { label: "Approved", value: summary.approved, color: "text-blue-600" },
          { label: "Corrected", value: summary.corrected, color: "text-purple-600" },
        ].map(({ label, value, color }) => (
          <div key={label} className="rounded-lg border bg-card p-3 text-center">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{label}</p>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Review progress</span>
          <span>{approvedPct}% reviewed</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${approvedPct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
