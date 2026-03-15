"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { DoubtReport } from "@/components/classification/DoubtReport";
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

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Resolve Doubts</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {doubts.length > 0
            ? `${doubts.length} item${doubts.length !== 1 ? "s" : ""} need manual classification.`
            : "All items have been classified."}
        </p>
      </div>

      <DoubtReport doubts={doubts} onResolved={handleResolved} />
    </div>
  );
}
