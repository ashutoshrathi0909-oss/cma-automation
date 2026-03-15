"use client";

import { useState } from "react";
import { AlertCircle, Check, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import { CMAFieldSelector } from "./CMAFieldSelector";
import type { Classification } from "@/types";

interface DoubtReportProps {
  doubts: Classification[];
  onResolved: (id: string) => void;
}

interface RowState {
  selectedField: string | null;
  saving: boolean;
}

export function DoubtReport({ doubts, onResolved }: DoubtReportProps) {
  const [rowState, setRowState] = useState<Record<string, RowState>>({});

  function getRow(id: string): RowState {
    return rowState[id] ?? { selectedField: null, saving: false };
  }

  function patchRow(id: string, patch: Partial<RowState>) {
    setRowState((prev) => ({ ...prev, [id]: { ...getRow(id), ...patch } }));
  }

  async function handleResolve(clf: Classification) {
    const row = getRow(clf.id);
    if (!row.selectedField) return;

    patchRow(clf.id, { saving: true });
    try {
      await apiClient(`/api/classifications/${clf.id}/correct`, {
        method: "POST",
        body: JSON.stringify({
          cma_field_name: row.selectedField,
          cma_row: clf.cma_row ?? 0,
          cma_sheet: clf.cma_sheet ?? "input_sheet",
          broad_classification: clf.broad_classification ?? "",
        }),
      });
      toast.success("Doubt resolved");
      onResolved(clf.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to resolve");
      patchRow(clf.id, { saving: false });
    }
  }

  if (doubts.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-12 text-center">
        <Check className="h-10 w-10 text-green-500" />
        <p className="font-medium">All doubts resolved!</p>
        <p className="text-sm text-muted-foreground">
          No items require manual classification.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {doubts.map((clf) => {
        const row = getRow(clf.id);
        return (
          <div
            key={clf.id}
            className="rounded-lg border bg-card p-4 space-y-3"
          >
            {/* Header */}
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">
                  {clf.line_item_description ?? "(no description)"}
                </p>
                {clf.line_item_amount !== null && clf.line_item_amount !== undefined && (
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    ₹{clf.line_item_amount.toLocaleString("en-IN")}
                  </p>
                )}
              </div>
              <Badge variant="destructive" className="shrink-0">Doubt</Badge>
            </div>

            {/* Reason + AI guess */}
            {clf.doubt_reason && (
              <p className="text-xs text-destructive/80">
                Reason: {clf.doubt_reason}
              </p>
            )}
            {clf.ai_best_guess && (
              <p className="text-xs text-muted-foreground">
                AI best guess: <span className="font-medium">{clf.ai_best_guess}</span>
              </p>
            )}

            {/* Inline correction form */}
            <div className="flex items-end gap-2">
              <div className="flex-1">
                <p className="mb-1 text-xs font-medium text-muted-foreground">
                  Assign CMA field
                </p>
                <CMAFieldSelector
                  value={row.selectedField}
                  onChange={(f) => patchRow(clf.id, { selectedField: f })}
                  disabled={row.saving}
                />
              </div>
              <Button
                size="sm"
                disabled={!row.selectedField || row.saving}
                onClick={() => handleResolve(clf)}
              >
                {row.saving ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Check className="h-3.5 w-3.5" />
                )}
                Resolve
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
