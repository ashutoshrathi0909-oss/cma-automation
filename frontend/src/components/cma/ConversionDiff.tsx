"use client";

import { useState } from "react";
import type { ConversionDiffItem, ConversionDiffResponse, ConversionDiffItemV2, ConversionPreviewResponseV2, DiffCategory } from "@/types";
import { CheckCircle, ArrowUpDown, AlertTriangle, Plus, Minus } from "lucide-react";

// ── V2: 5-category color-coded diff ─────────────────────────────────────

const diffStyles: Record<DiffCategory, { bg: string; border: string; label: string; badgeBg: string; icon: typeof CheckCircle }> = {
  unchanged:      { bg: "bg-green-50",  border: "border-l-4 border-green-500",  label: "Unchanged",           badgeBg: "bg-green-100 text-green-800",  icon: CheckCircle },
  amount_changed: { bg: "bg-yellow-50", border: "border-l-4 border-yellow-500", label: "Amount Updated",      badgeBg: "bg-yellow-100 text-yellow-800", icon: ArrowUpDown },
  desc_changed:   { bg: "bg-red-50",    border: "border-l-4 border-red-500",    label: "Description Changed", badgeBg: "bg-red-100 text-red-800",      icon: AlertTriangle },
  added:          { bg: "bg-blue-50",   border: "border-l-4 border-blue-500",   label: "New Item",            badgeBg: "bg-blue-100 text-blue-800",    icon: Plus },
  removed:        { bg: "bg-gray-100",  border: "border-l-4 border-gray-400",   label: "Removed",             badgeBg: "bg-gray-200 text-gray-700",    icon: Minus },
};

const categories: DiffCategory[] = ["unchanged", "amount_changed", "desc_changed", "added", "removed"];

function fmt(amount: number | null): string {
  if (amount === null || amount === undefined) return "\u2014";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function AmountDiff({ provisional, audited }: { provisional: number | null; audited: number | null }) {
  if (provisional === audited || (provisional === null && audited === null)) {
    return <span className="font-medium">{fmt(audited ?? provisional)}</span>;
  }

  const delta = provisional != null && audited != null && provisional !== 0
    ? ((audited - provisional) / Math.abs(provisional) * 100).toFixed(1)
    : null;

  return (
    <div className="flex flex-col items-end gap-0.5">
      {provisional != null && (
        <span className="text-xs text-muted-foreground line-through">{fmt(provisional)}</span>
      )}
      <span className="font-semibold">{fmt(audited)}</span>
      {delta && (
        <span className={`text-xs ${Number(delta) > 0 ? "text-red-600" : "text-green-600"}`}>
          {Number(delta) > 0 ? "+" : ""}{delta}%
        </span>
      )}
    </div>
  );
}

function DiffRow({ item }: { item: ConversionDiffItemV2 }) {
  const style = diffStyles[item.category];
  const Icon = style.icon;

  return (
    <tr className={`${style.bg} ${style.border}`}>
      <td className="px-4 py-2">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 shrink-0 opacity-60" />
          <div>
            <div className="text-sm font-medium text-gray-900">
              {item.provisional_desc || item.audited_desc}
            </div>
            {item.category === "desc_changed" && item.audited_desc && item.provisional_desc && (
              <div className="text-xs text-gray-500 mt-0.5">
                was: <span className="italic">{item.provisional_desc}</span>
              </div>
            )}
          </div>
        </div>
      </td>
      <td className="px-4 py-2 text-right">
        <AmountDiff provisional={item.provisional_amount} audited={item.audited_amount} />
      </td>
      <td className="px-4 py-2 text-center">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${style.badgeBg}`}>
          {style.label}
        </span>
      </td>
      <td className="px-4 py-2 text-center text-xs text-gray-500">
        {item.match_score > 0 ? `${item.match_score.toFixed(0)}%` : "\u2014"}
      </td>
    </tr>
  );
}

interface SummaryBarProps {
  summary: Record<DiffCategory, number>;
  activeFilter: DiffCategory | "all";
  onFilter: (cat: DiffCategory | "all") => void;
}

function SummaryBar({ summary, activeFilter, onFilter }: SummaryBarProps) {
  const total = Object.values(summary).reduce((a, b) => a + b, 0);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        onClick={() => onFilter("all")}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
          activeFilter === "all"
            ? "bg-gray-900 text-white"
            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`}
      >
        All ({total})
      </button>
      {categories.map((cat) => {
        if (summary[cat] === 0) return null;
        const style = diffStyles[cat];
        return (
          <button
            key={cat}
            onClick={() => onFilter(cat)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeFilter === cat
                ? "ring-2 ring-offset-1 ring-gray-400 " + style.badgeBg
                : style.badgeBg + " hover:opacity-80"
            }`}
          >
            {style.label} ({summary[cat]})
          </button>
        );
      })}
    </div>
  );
}

interface ConversionDiffV2Props {
  diff: ConversionPreviewResponseV2;
  onAcceptAllAmountChanges?: () => void;
}

export function ConversionDiffV2({ diff, onAcceptAllAmountChanges }: ConversionDiffV2Props) {
  const [activeFilter, setActiveFilter] = useState<DiffCategory | "all">("all");

  // By default, hide unchanged items unless filter is "all" or "unchanged"
  const [showUnchanged, setShowUnchanged] = useState(false);

  const allItems: ConversionDiffItemV2[] = [
    ...diff.amount_changed,
    ...diff.desc_changed,
    ...diff.added,
    ...diff.removed,
    ...(showUnchanged || activeFilter === "unchanged" ? diff.unchanged : []),
  ];

  const filteredItems = activeFilter === "all"
    ? allItems
    : allItems.filter((item) => item.category === activeFilter);

  const hasChanges = diff.amount_changed.length + diff.desc_changed.length + diff.added.length + diff.removed.length > 0;

  if (!hasChanges && diff.unchanged.length > 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-green-50 p-6 text-center">
        <CheckCircle className="mx-auto h-8 w-8 text-green-500 mb-2" />
        <p className="text-sm font-medium text-green-700">
          No differences found — all {diff.unchanged.length} items match between provisional and audited.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <SummaryBar
        summary={diff.summary}
        activeFilter={activeFilter}
        onFilter={setActiveFilter}
      />

      {/* Bulk actions */}
      <div className="flex items-center gap-3">
        {diff.amount_changed.length > 0 && onAcceptAllAmountChanges && (
          <button
            onClick={onAcceptAllAmountChanges}
            className="px-4 py-2 bg-yellow-500 text-white text-sm font-medium rounded-md hover:bg-yellow-600 transition-colors"
          >
            Accept All Amount Changes ({diff.amount_changed.length})
          </button>
        )}
        {!showUnchanged && diff.unchanged.length > 0 && activeFilter !== "unchanged" && (
          <button
            onClick={() => setShowUnchanged(true)}
            className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 border border-gray-300 rounded-md"
          >
            Show {diff.unchanged.length} unchanged items
          </button>
        )}
        {showUnchanged && (
          <button
            onClick={() => setShowUnchanged(false)}
            className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 border border-gray-300 rounded-md"
          >
            Hide unchanged items
          </button>
        )}
      </div>

      {/* Diff table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Line Item
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                Amount
              </th>
              <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                Match
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredItems.map((item, idx) => (
              <DiffRow key={`${item.provisional_item_id || item.audited_item_id}-${idx}`} item={item} />
            ))}
          </tbody>
        </table>
      </div>

      {filteredItems.length === 0 && (
        <div className="text-center text-sm text-gray-500 py-4">
          No items in this category.
        </div>
      )}
    </div>
  );
}

// ── V1: Legacy component (backward compatibility) ───────────────────────

interface ConversionDiffProps {
  diff: ConversionDiffResponse;
}

function fmtV1(amount: number | null): string {
  if (amount === null) return "\u2014";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function DiffRowV1({ item }: { item: ConversionDiffItem }) {
  const rowClass =
    item.change_type === "changed"
      ? "bg-yellow-50"
      : item.change_type === "added"
        ? "bg-green-50"
        : "bg-red-50";

  const badge =
    item.change_type === "changed"
      ? "bg-yellow-100 text-yellow-800"
      : item.change_type === "added"
        ? "bg-green-100 text-green-800"
        : "bg-red-100 text-red-800";

  return (
    <tr className={rowClass}>
      <td className="px-4 py-2 text-sm font-medium text-gray-900">
        {item.description}
      </td>
      <td className="px-4 py-2 text-sm text-right text-gray-600">
        {fmtV1(item.provisional_amount)}
      </td>
      <td className="px-4 py-2 text-sm text-right text-gray-900 font-medium">
        {fmtV1(item.audited_amount)}
      </td>
      <td className="px-4 py-2 text-center">
        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${badge}`}>
          {item.change_type}
        </span>
      </td>
    </tr>
  );
}

export function ConversionDiff({ diff }: ConversionDiffProps) {
  const allItems: ConversionDiffItem[] = [
    ...diff.changed,
    ...diff.added,
    ...diff.removed,
  ];

  const totalChanges = allItems.length;

  if (totalChanges === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-green-50 p-6 text-center">
        <p className="text-sm font-medium text-green-700">
          No differences found — provisional and audited figures match exactly.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4 text-sm">
        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">
          {diff.changed.length} changed
        </span>
        <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
          {diff.added.length} added
        </span>
        <span className="px-2 py-1 bg-red-100 text-red-800 rounded">
          {diff.removed.length} removed
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Line Item
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                Provisional
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                Audited
              </th>
              <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                Change
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {allItems.map((item, idx) => (
              <DiffRowV1 key={idx} item={item} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
