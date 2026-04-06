"use client";

import { useState } from "react";
import { Check, Edit3, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import { CMAFieldSelector } from "./CMAFieldSelector";
import type { Classification } from "@/types";

interface ClassificationReviewProps {
  classifications: Classification[];
  onApproved: (id: string) => void;
  onCorrected: (updated: Classification) => void;
}

function confidenceBadge(score: number | null, isDoubt: boolean) {
  if (isDoubt) return <Badge variant="destructive">Doubt</Badge>;
  if (score === null) return <Badge variant="secondary">Unknown</Badge>;
  if (score >= 0.85) return <Badge className="bg-green-100 text-green-800 dark:bg-green-900/30">High</Badge>;
  if (score >= 0.6) return <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-900/30">Medium</Badge>;
  return <Badge variant="destructive">Low</Badge>;
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    approved: "bg-green-100 text-green-800 dark:bg-green-900/30",
    corrected: "bg-blue-100 text-blue-800 dark:bg-blue-900/30",
    needs_review: "bg-red-100 text-red-800 dark:bg-red-900/30",
    auto_classified: "bg-gray-100 text-gray-700 dark:bg-gray-800",
  };
  return (
    <Badge className={map[status] ?? ""}>{status.replace(/_/g, " ")}</Badge>
  );
}

interface RowState {
  correcting: boolean;
  saving: boolean;
  newField: string | null;
}

export function ClassificationReview({
  classifications,
  onApproved,
  onCorrected,
}: ClassificationReviewProps) {
  const [rowState, setRowState] = useState<Record<string, RowState>>({});

  function getRow(id: string): RowState {
    return rowState[id] ?? { correcting: false, saving: false, newField: null };
  }

  function patchRow(id: string, patch: Partial<RowState>) {
    setRowState((prev) => ({ ...prev, [id]: { ...getRow(id), ...patch } }));
  }

  async function handleApprove(clf: Classification) {
    patchRow(clf.id, { saving: true });
    try {
      await apiClient(`/api/classifications/${clf.id}/approve`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      toast.success("Approved");
      onApproved(clf.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to approve");
    } finally {
      patchRow(clf.id, { saving: false });
    }
  }

  async function handleCorrect(clf: Classification) {
    const row = getRow(clf.id);
    if (!row.newField) return;

    patchRow(clf.id, { saving: true });
    try {
      const updated = await apiClient<Classification>(
        `/api/classifications/${clf.id}/correct`,
        {
          method: "POST",
          body: JSON.stringify({
            cma_field_name: row.newField,
            cma_row: clf.cma_row ?? 0,
            cma_sheet: clf.cma_sheet ?? "input_sheet",
            broad_classification: clf.broad_classification ?? "",
          }),
        }
      );
      toast.success("Correction saved");
      patchRow(clf.id, { correcting: false, newField: null });
      onCorrected(updated);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to correct");
    } finally {
      patchRow(clf.id, { saving: false });
    }
  }

  if (classifications.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No classifications to review.
      </p>
    );
  }

  return (
    <div className="rounded-lg border overflow-hidden">
      {/* Column headers */}
      <div className="grid grid-cols-2 divide-x bg-muted/40">
        <div className="px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Line Item
        </div>
        <div className="px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Classification
        </div>
      </div>

      {/* Rows */}
      <div className="divide-y">
        {classifications.map((clf) => {
          const row = getRow(clf.id);
          const isReviewed = clf.status === "approved" || clf.status === "corrected";

          return (
            <div key={clf.id} className="grid grid-cols-2 divide-x">
              {/* Left: line item */}
              <div className="px-4 py-3">
                <p className="text-sm font-medium leading-snug">
                  {clf.line_item_description ?? "(no description)"}
                </p>
                {clf.line_item_amount !== null && clf.line_item_amount !== undefined && (
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    ₹{clf.line_item_amount.toLocaleString("en-IN")}
                  </p>
                )}
                {/* Document context */}
                <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground/70">
                  {clf.document_name && (
                    <span className="truncate max-w-[30ch]" title={clf.document_name}>
                      {clf.document_name}
                    </span>
                  )}
                  {clf.line_item_section && (
                    <span>Section: {clf.line_item_section}</span>
                  )}
                  {clf.cma_row != null && clf.cma_row > 0 && (
                    <span>Row {clf.cma_row}</span>
                  )}
                </div>
              </div>

              {/* Right: classification + actions */}
              <div className="px-4 py-3 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium">
                    {clf.cma_field_name ?? "—"}
                  </span>
                  {confidenceBadge(clf.confidence_score, clf.is_doubt)}
                  {statusBadge(clf.status)}
                </div>

                {clf.is_doubt && clf.doubt_reason && (
                  <p className="text-xs text-destructive">{clf.doubt_reason}</p>
                )}

                {row.correcting && (
                  <div className="space-y-2">
                    <CMAFieldSelector
                      value={row.newField}
                      onChange={(f) => patchRow(clf.id, { newField: f })}
                      placeholder="Select correct CMA field…"
                    />
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        disabled={!row.newField || row.saving}
                        onClick={() => handleCorrect(clf)}
                      >
                        {row.saving ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Check className="h-3.5 w-3.5" />
                        )}
                        Save
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => patchRow(clf.id, { correcting: false, newField: null })}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {!row.correcting && !isReviewed && (
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={row.saving}
                      onClick={() => handleApprove(clf)}
                    >
                      {row.saving ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Check className="h-3.5 w-3.5 text-green-600" />
                      )}
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => patchRow(clf.id, { correcting: true })}
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                      Correct
                    </Button>
                  </div>
                )}

                {isReviewed && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-xs"
                    onClick={() => patchRow(clf.id, { correcting: true })}
                  >
                    <Edit3 className="h-3 w-3" />
                    Re-correct
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
