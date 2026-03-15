"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Check, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { ClassificationReview } from "@/components/classification/ClassificationReview";
import type { Classification } from "@/types";

export default function ReviewPage() {
  const { id: reportId } = useParams<{ id: string }>();
  const router = useRouter();

  const [classifications, setClassifications] = useState<Classification[]>([]);
  const [loading, setLoading] = useState(true);
  const [bulkApproving, setBulkApproving] = useState(false);

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
    // Collect high-confidence, non-doubt, non-reviewed IDs
    const highConf = classifications.filter(
      (c) =>
        !c.is_doubt &&
        (c.confidence_score ?? 0) >= 0.85 &&
        c.status === "auto_classified"
    );

    if (highConf.length === 0) {
      toast.info("No high-confidence items left to approve.");
      return;
    }

    setBulkApproving(true);
    try {
      // The bulk-approve endpoint is document-scoped; call per document
      const docIds = [...new Set(classifications.map((c) => c.line_item_id))];
      // Use the report-level classifications we already have
      await Promise.all(
        highConf.map((c) =>
          apiClient(`/api/classifications/${c.id}/approve`, {
            method: "POST",
            body: JSON.stringify({}),
          })
        )
      );
      toast.success(`Approved ${highConf.length} high-confidence items`);
      setClassifications((prev) =>
        prev.map((c) =>
          highConf.some((h) => h.id === c.id) ? { ...c, status: "approved" } : c
        )
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Bulk approve failed");
    } finally {
      setBulkApproving(false);
    }
  }

  const highConfCount = classifications.filter(
    (c) => !c.is_doubt && (c.confidence_score ?? 0) >= 0.85 && c.status === "auto_classified"
  ).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
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
            {classifications.length} items total — approve or correct each classification.
          </p>
        </div>

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

      <ClassificationReview
        classifications={classifications}
        onApproved={handleApproved}
        onCorrected={handleCorrected}
      />
    </div>
  );
}
