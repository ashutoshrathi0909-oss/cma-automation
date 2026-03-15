"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertCircle,
  ArrowLeft,
  CheckSquare,
  FileBarChart,
  Loader2,
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import { ConfidenceDashboard } from "@/components/classification/ConfidenceDashboard";
import type { CMAReport, Client, ConfidenceSummary } from "@/types";

export default function CMAOverviewPage() {
  const { id: reportId } = useParams<{ id: string }>();
  const router = useRouter();

  const [report, setReport] = useState<CMAReport | null>(null);
  const [client, setClient] = useState<Client | null>(null);
  const [summary, setSummary] = useState<ConfidenceSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!reportId) return;
    Promise.all([
      apiClient<CMAReport>(`/api/cma-reports/${reportId}`),
      apiClient<ConfidenceSummary>(`/api/cma-reports/${reportId}/confidence`),
    ])
      .then(([r, s]) => {
        setReport(r);
        setSummary(s);
        return apiClient<Client>(`/api/clients/${r.client_id}`);
      })
      .then(setClient)
      .catch(() => router.replace("/clients"))
      .finally(() => setLoading(false));
  }, [reportId, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!report || !summary) return null;

  const allReviewed = summary.total > 0 && summary.needs_review === 0;
  const reviewProgress =
    summary.total > 0
      ? Math.round(((summary.approved + summary.corrected) / summary.total) * 100)
      : 0;

  return (
    <div className="space-y-6">
      {/* Back */}
      <Link
        href={client ? `/clients/${client.id}` : "/clients"}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        {client?.name ?? "Client"}
      </Link>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">{report.title}</h1>
            <Badge className="capitalize">{report.status.replace(/_/g, " ")}</Badge>
          </div>
          {client && (
            <p className="mt-0.5 text-sm text-muted-foreground">{client.name}</p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2">
          <Link href={`/cma/${reportId}/review`}>
            <Button variant="outline" size="sm">
              <CheckSquare className="mr-1.5 h-4 w-4" />
              Review ({reviewProgress}%)
            </Button>
          </Link>
          {summary.needs_review > 0 && (
            <Link href={`/cma/${reportId}/doubts`}>
              <Button variant="outline" size="sm">
                <AlertCircle className="mr-1.5 h-4 w-4 text-destructive" />
                Resolve Doubts ({summary.needs_review})
              </Button>
            </Link>
          )}
          <Link href={`/cma/${reportId}/audit-trail`}>
            <Button variant="ghost" size="sm">
              <MessageSquare className="mr-1.5 h-4 w-4" />
              Audit Trail
            </Button>
          </Link>
          <Button
            size="sm"
            disabled
            title="Complete review first — available in Phase 7"
          >
            <FileBarChart className="mr-1.5 h-4 w-4" />
            Generate Excel
          </Button>
        </div>
      </div>

      {/* Confidence dashboard */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Classification Summary</CardTitle>
          <CardDescription>
            Live counts from the classifications table — updates as you review.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ConfidenceDashboard summary={summary} />
        </CardContent>
      </Card>

      {/* Linked documents */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Linked Documents ({report.document_ids.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {report.document_ids.length === 0 ? (
            <p className="text-sm text-muted-foreground">No documents linked.</p>
          ) : (
            <ul className="space-y-1">
              {report.document_ids.map((docId) => (
                <li key={docId} className="text-sm text-muted-foreground font-mono">
                  {docId}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {allReviewed && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950/20">
          <p className="text-sm font-medium text-green-800 dark:text-green-300">
            All items reviewed — ready to generate Excel (Phase 7).
          </p>
        </div>
      )}
    </div>
  );
}
