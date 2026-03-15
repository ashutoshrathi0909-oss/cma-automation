"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, AlertCircle, CheckCircle2, Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import { ProgressTracker } from "@/components/common/ProgressTracker";
import { ExtractionVerifier } from "@/components/extraction/ExtractionVerifier";
import type { Document, ExtractionTriggerResponse } from "@/types";

type PageState =
  | { phase: "loading" }
  | { phase: "triggering" }
  | { phase: "tracking"; taskId: string }
  | { phase: "processing_unknown" }
  | { phase: "verifier" }
  | { phase: "already_verified" }
  | { phase: "failed" }
  | { phase: "error"; message: string };

export default function VerifyPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [doc, setDoc] = useState<Document | null>(null);
  const [pageState, setPageState] = useState<PageState>({ phase: "loading" });

  useEffect(() => {
    if (!id) return;
    apiClient<Document>(`/api/documents/${id}`)
      .then((d) => {
        setDoc(d);
        resolveInitialState(d);
      })
      .catch(() => {
        setPageState({ phase: "error", message: "Document not found." });
      });
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  function resolveInitialState(d: Document) {
    switch (d.extraction_status) {
      case "pending":
        triggerExtraction(d.id);
        break;
      case "processing":
        setPageState({ phase: "processing_unknown" });
        break;
      case "extracted":
        setPageState({ phase: "verifier" });
        break;
      case "verified":
        setPageState({ phase: "already_verified" });
        break;
      case "failed":
        setPageState({ phase: "failed" });
        break;
    }
  }

  async function triggerExtraction(docId: string) {
    setPageState({ phase: "triggering" });
    try {
      const result = await apiClient<ExtractionTriggerResponse>(
        `/api/documents/${docId}/extract`,
        { method: "POST" }
      );
      setPageState({ phase: "tracking", taskId: result.task_id });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to start extraction");
      setPageState({ phase: "failed" });
    }
  }

  function handleExtractionComplete() {
    setPageState({ phase: "verifier" });
    // Refresh document state
    if (id) {
      apiClient<Document>(`/api/documents/${id}`)
        .then(setDoc)
        .catch(() => null);
    }
  }

  function handleExtractionFailed(error: string) {
    toast.error(error);
    setPageState({ phase: "failed" });
  }

  function handleVerified() {
    setPageState({ phase: "already_verified" });
    if (id) {
      apiClient<Document>(`/api/documents/${id}`)
        .then(setDoc)
        .catch(() => null);
    }
  }

  function handleRetry() {
    if (!doc) return;
    void triggerExtraction(doc.id);
  }

  const backHref = doc ? `/clients/${doc.client_id}` : "/clients";

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href={backHref}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to client
      </Link>

      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Verify Extracted Data</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Review and confirm the extracted financial line items
        </p>
        {doc && (
          <p className="mt-1 text-xs text-muted-foreground">
            {doc.file_name}
          </p>
        )}
      </div>

      {/* Content area */}
      <div className="rounded-xl border bg-card p-6">
        {pageState.phase === "loading" && (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {pageState.phase === "triggering" && (
          <div className="flex flex-col items-center justify-center gap-3 py-10">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Starting extraction…</p>
          </div>
        )}

        {pageState.phase === "tracking" && (
          <ProgressTracker
            taskId={pageState.taskId}
            onComplete={handleExtractionComplete}
            onFailed={handleExtractionFailed}
          />
        )}

        {pageState.phase === "processing_unknown" && (
          <div className="flex flex-col items-center justify-center gap-3 py-10">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="text-sm font-medium">Extraction in progress…</p>
            <p className="text-xs text-muted-foreground">
              The document is being processed. Please refresh in a moment.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (!id) return;
                setPageState({ phase: "loading" });
                apiClient<Document>(`/api/documents/${id}`)
                  .then((d) => { setDoc(d); resolveInitialState(d); })
                  .catch(() => setPageState({ phase: "error", message: "Document not found." }));
              }}
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </Button>
          </div>
        )}

        {pageState.phase === "verifier" && (
          <ExtractionVerifier documentId={id} onVerified={handleVerified} />
        )}

        {pageState.phase === "already_verified" && (
          <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
            <CheckCircle2 className="h-10 w-10 text-green-500" />
            <div>
              <p className="font-medium">Already Verified</p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                This document has been verified and is ready for classification.
              </p>
            </div>
            <Badge variant="default" className="bg-green-100 text-green-800">
              Verified
            </Badge>
            <Button variant="outline" size="sm" onClick={() => router.push(backHref)}>
              Back to client
            </Button>
          </div>
        )}

        {pageState.phase === "failed" && (
          <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
            <AlertCircle className="h-10 w-10 text-destructive" />
            <div>
              <p className="font-medium">Extraction Failed</p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                Something went wrong while extracting data from this document.
              </p>
            </div>
            <Button onClick={handleRetry} size="sm">
              <RefreshCw className="h-3.5 w-3.5" />
              Retry Extraction
            </Button>
          </div>
        )}

        {pageState.phase === "error" && (
          <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
            <AlertCircle className="h-10 w-10 text-destructive" />
            <p className="text-sm text-muted-foreground">{pageState.message}</p>
            <Button variant="outline" size="sm" onClick={() => router.push("/clients")}>
              Go to Clients
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
