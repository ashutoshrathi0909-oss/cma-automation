"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { DoubtReport } from "@/components/classification/DoubtReport";
import { Skeleton } from "@/components/ui/skeleton";
import type { Classification } from "@/types";

export default function DoubtsPage() {
  const { id: reportId } = useParams<{ id: string }>();
  const router = useRouter();

  const [doubts, setDoubts] = useState<Classification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!reportId) return;
    apiClient<Classification[]>(`/api/cma-reports/${reportId}/classifications`)
      .then((clfs) => setDoubts(clfs.filter((c) => c.is_doubt)))
      .catch(() => router.replace(`/cma/${reportId}`))
      .finally(() => setLoading(false));
  }, [reportId, router]);

  function handleResolved(id: string) {
    setDoubts((prev) => prev.filter((c) => c.id !== id));
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-5 w-32" />
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-lg" />
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

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Resolve Doubts</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {doubts.length > 0
            ? `${doubts.length} item${doubts.length !== 1 ? "s" : ""} need manual classification.`
            : "All items have been classified."}
        </p>
      </div>

      {doubts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <CheckCircle2 className="mb-3 h-12 w-12 text-green-500/60" />
          <p className="font-medium text-muted-foreground">No doubt items</p>
          <p className="mt-1 text-sm text-muted-foreground">
            All classifications resolved
          </p>
        </div>
      ) : (
        <DoubtReport doubts={doubts} onResolved={handleResolved} />
      )}
    </div>
  );
}
