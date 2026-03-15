"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { AuditTrail } from "@/components/common/AuditTrail";
import type { AuditEntry } from "@/types";

export default function AuditTrailPage() {
  const { id: reportId } = useParams<{ id: string }>();
  const router = useRouter();

  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!reportId) return;
    apiClient<AuditEntry[]>(`/api/cma-reports/${reportId}/audit`)
      .then(setEntries)
      .catch(() => router.replace(`/cma/${reportId}`))
      .finally(() => setLoading(false));
  }, [reportId, router]);

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
        <h1 className="text-2xl font-semibold tracking-tight">Audit Trail</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          All approve and correct actions — newest first.
        </p>
      </div>

      <AuditTrail entries={entries} />
    </div>
  );
}
