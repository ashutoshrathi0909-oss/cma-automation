"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckSquare,
  FileBarChart,
  Loader2,
  MessageSquare,
  Play,
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
import { Skeleton } from "@/components/ui/skeleton";
import type { CMAReport, Client, ConfidenceSummary } from "@/types";

export default function CMAOverviewPage() {
  const { id: reportId } = useParams<{ id: string }>();
  const router = useRouter();

  const [report, setReport] = useState<CMAReport | null>(null);
  const [client, setClient] = useState<Client | null>(null);
  const [summary, setSummary] = useState<ConfidenceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [classifying, setClassifying] = useState(false);
  const [documents, setDocuments] = useState<Record<string, { file_name: string; financial_year: number; document_type: string }>>({});

  // Live polling — updates classification summary every 5s while classifying
  useEffect(() => {
    if (!reportId || !classifying) return;

    const interval = setInterval(async () => {
      try {
        const s = await apiClient<ConfidenceSummary>(
          `/api/cma-reports/${reportId}/confidence`
        );
        setSummary(s);
        if (s.total > 0) {
          setClassifying(false);
        }
      } catch {
        // silently ignore polling errors
      }
    }, 5000);

    // Safety: stop polling after 2 minutes
    const timeout = setTimeout(() => {
      clearInterval(interval);
      setClassifying(false);
    }, 120000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [reportId, classifying]);

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
      .then((c) => {
        setClient(c);
        // Fetch document names for the linked documents card
        return apiClient<Array<{ id: string; file_name: string; financial_year: number; document_type: string }>>(
          `/api/documents/?client_id=${c.id}`
        );
      })
      .then((docs) => {
        const map: Record<string, { file_name: string; financial_year: number; document_type: string }> = {};
        for (const d of docs) map[d.id] = d;
        setDocuments(map);
      })
      .catch(() => router.replace("/clients"))
      .finally(() => setLoading(false));
  }, [reportId, router]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-5 w-32" />
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-40" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-8 w-28" />
            <Skeleton className="h-8 w-28" />
          </div>
        </div>
        <Skeleton className="h-48 w-full rounded-xl" />
      </div>
    );
  }

  if (!report || !summary) return null;

  const hasClassifications = summary.total > 0;
  const allReviewed = hasClassifications && summary.needs_review === 0;

  const handleRunClassification = async () => {
    if (!report) return;
    setClassifying(true);
    try {
      for (const docId of report.document_ids) {
        await apiClient(`/api/documents/${docId}/classify`, { method: "POST" });
      }
      toast.success(
        `Classification triggered for ${report.document_ids.length} documents`
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Classification failed");
      setClassifying(false);
    }
  };

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
          {!hasClassifications && !classifying && (
            <Button size="sm" onClick={handleRunClassification}>
              <Play className="mr-1.5 h-4 w-4" />
              Run Classification
            </Button>
          )}
          {classifying && (
            <Button size="sm" disabled>
              <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              Classifying...
            </Button>
          )}
          {allReviewed ? (
            <Link href={`/cma/${reportId}/generate`}>
              <Button size="sm">
                <FileBarChart className="mr-1.5 h-4 w-4" />
                Generate Excel
              </Button>
            </Link>
          ) : hasClassifications ? (
            <Button
              size="sm"
              disabled
              title={
                summary.needs_review > 0
                  ? `Resolve ${summary.needs_review} doubt(s) first`
                  : "Approve or correct all classifications first"
              }
            >
              <FileBarChart className="mr-1.5 h-4 w-4" />
              Generate Excel
            </Button>
          ) : null}
          {report.status === "complete" && (
            <Link href={`/cma/${reportId}/roll-forward`}>
              <Button variant="outline" size="sm">
                <ArrowRight className="mr-1.5 h-4 w-4" />
                Roll Forward
              </Button>
            </Link>
          )}
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
            <ul className="space-y-1.5">
              {report.document_ids.map((docId) => {
                const doc = documents[docId];
                return (
                  <li key={docId} className="flex items-center gap-2 text-sm">
                    <span className="font-medium truncate max-w-[30ch]" title={doc?.file_name ?? docId}>
                      {doc?.file_name ?? docId}
                    </span>
                    {doc?.financial_year && (
                      <Badge variant="outline" className="text-xs shrink-0">
                        FY {doc.financial_year - 1}-{doc.financial_year}
                      </Badge>
                    )}
                    {doc?.document_type && (
                      <span className="text-xs text-muted-foreground capitalize shrink-0">
                        {doc.document_type.replace(/_/g, " ")}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
