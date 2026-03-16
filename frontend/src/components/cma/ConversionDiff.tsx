"use client";

import type { ConversionDiffItem, ConversionDiffResponse } from "@/types";

interface ConversionDiffProps {
  diff: ConversionDiffResponse;
}

function fmt(amount: number | null): string {
  if (amount === null) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function DiffRow({ item }: { item: ConversionDiffItem }) {
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
        {fmt(item.provisional_amount)}
      </td>
      <td className="px-4 py-2 text-sm text-right text-gray-900 font-medium">
        {fmt(item.audited_amount)}
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
              <DiffRow key={idx} item={item} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
