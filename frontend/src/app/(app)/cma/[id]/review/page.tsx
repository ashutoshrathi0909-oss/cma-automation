"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Check, Eye, EyeOff, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { ClassificationReview } from "@/components/classification/ClassificationReview";
import { Skeleton } from "@/components/ui/skeleton";
import type { Classification } from "@/types";

type FilterMode = "needs_review" | "all";

export default function ReviewPage() {
  const { id: reportId } = useParams<{ id: string }>();
  const router = useRouter();

  const [classifications, setClassifications] = useState<Classification[]>([]);
  const [loading, setLoading] = useState(true);
  const [bulkApproving, setBulkApproving] = useState(false);
  const [filter, setFilter] = useState<FilterMode>("needs_review");

  useEffect(() => {
    if (!reportId) return;
    apiClient<Classification[]>(`/api/cma-reports/${reportId}/classifications`)
      .then(setClassifications)
      .catch(() => router.replace(`/cma/${reportId}`))
      .finally(() => setLoading(false));
  }, [reportId, router]);

  function handleApproved(id: string) {
    setClassifications((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: "approved" } : c))
    );
  }

  function handleCorrected(updated: Classification) {
    setClassifications((prev) =>
      prev.map((c) => (c.id === updated.id ? updated : c))
    );
  }

  async function handleBulkApprove() {
    const targets = filtered.filter(
      (c) =>
        !c.is_doubt &&
        (c.confidence_score ?? 0) >= 0.85 &&
        c.status === "auto_classified"
    );

    if (targets.length === 0) {
      toast.info("No high-confidence items left to approve.");
      return;
    }

    setBulkApproving(true);
    try {
      await Promise.all(
        targets.map((c) =>
          apiClient(`/api/classifications/${c.id}/approve`, {
            method: "POST",
            body: JSON.stringify({}),
          })
        )
      );
      toast.success(`Approved ${targets.length} high-confidence items`);
      setClassifications((prev) =>
        prev.map((c) =>
          targets.some((h) => h.id === c.id) ? { ...c, status: "approved" } : c
        )
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Bulk approve failed");
    } finally {
      setBulkApproving(false);
    }
  }

  // Filter logic: "needs_review" shows only items needing CA attention
  const filtered =
    filter === "needs_review"
      ? classifications.filter(
          (c) =>
            c.status === "needs_review" ||
            c.status === "auto_classified" ||
            c.is_doubt
        )
      : classifications;

  const needsReviewCount = classifications.filter(
    (c) => c.status === "needs_review" || c.status === "auto_classified" || c.is_doubt
  ).length;

  const highConfCount = filtered.filter(
    (c) => !c.is_doubt && (c.confidence_score ?? 0) >= 0.85 && c.status === "auto_classified"
  ).length;

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-5 w-32" />
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-56" />
            <Skeleton className="h-4 w-44" />
          </div>
          <Skeleton className="h-8 w-48" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        href={`/cma/${reportId}`}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to report
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Review Classifications</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {filter === "needs_review" ? (
              <>
                Showing <span className="font-medium text-foreground">{filtered.length}</span> items
                needing review ({classifications.length} total,{" "}
                {classifications.length - needsReviewCount} auto-approved)
              </>
            ) : (
              <>
                Showing all <span className="font-medium text-foreground">{classifications.length}</span> classifications
              </>
            )}
          </p>
        </div>

        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFilter(filter === "needs_review" ? "all" : "needs_review")}
          >
            {filter === "needs_review" ? (
              <>
                <Eye className="mr-1.5 h-4 w-4" />
                Show All ({classifications.length})
              </>
            ) : (
              <>
                <EyeOff className="mr-1.5 h-4 w-4" />
                Needs Review Only ({needsReviewCount})
              </>
            )}
          </Button>

          {highConfCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              disabled={bulkApproving}
              onClick={handleBulkApprove}
            >
              {bulkApproving ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <Check className="mr-1.5 h-4 w-4 text-green-600" />
              )}
              Approve All High Confidence ({highConfCount})
            </Button>
          )}
        </div>
      </div>

      <ClassificationReview
        classifications={filtered}
        onApproved={handleApproved}
        onCorrected={handleCorrected}
      />
    </div>
  );
}
