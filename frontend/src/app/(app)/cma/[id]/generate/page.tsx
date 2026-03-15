"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle,
  Download,
  FileBarChart,
  Loader2,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import type { CMAReport, DownloadUrlResponse, GenerateTriggerResponse } from "@/types";

type GenerateState = "idle" | "starting" | "generating" | "complete" | "failed";

export default function GeneratePage() {
  const { id: reportId } = useParams<{ id: string }>();

  const [state, setState] = useState<GenerateState>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!reportId) return;
    startGeneration();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportId]);

  async function startGeneration() {
    setState("starting");
    try {
      await apiClient<GenerateTriggerResponse>(
        `/api/cma-reports/${reportId}/generate`,
        { method: "POST" }
      );
      setState("generating");
      startPolling();
    } catch (err) {
      setState("failed");
      setErrorMsg(err instanceof Error ? err.message : "Failed to start generation");
    }
  }

  function startPolling() {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const report = await apiClient<CMAReport>(`/api/cma-reports/${reportId}`);
        if (report.status === "complete") {
          clearInterval(pollRef.current!);
          setState("complete");
        } else if (report.status === "failed") {
          clearInterval(pollRef.current!);
          setState("failed");
          setErrorMsg("Excel generation failed. Please try again.");
        }
      } catch {
        // ignore transient errors — keep polling
      }
    }, 2000);
  }

  async function handleDownload() {
    try {
      const { signed_url } = await apiClient<DownloadUrlResponse>(
        `/api/cma-reports/${reportId}/download`
      );
      window.open(signed_url, "_blank");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Download failed");
    }
  }

  async function handleRetry() {
    setErrorMsg(null);
    await startGeneration();
  }

  return (
    <div className="space-y-6 max-w-lg mx-auto">
      <Link
        href={`/cma/${reportId}`}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Report
      </Link>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileBarChart className="h-5 w-5" />
            Generate CMA Excel
          </CardTitle>
          <CardDescription>
            Filling the CMA template with classified financial data.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {(state === "starting" || state === "generating") && (
            <div className="flex flex-col items-center gap-3 py-6" role="status">
              <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" aria-hidden="true" />
              <p className="text-sm text-muted-foreground">
                {state === "starting"
                  ? "Starting generation…"
                  : "Generating Excel file — this may take a few seconds…"}
              </p>
            </div>
          )}

          {state === "complete" && (
            <div className="flex flex-col items-center gap-4 py-6">
              <CheckCircle className="h-10 w-10 text-green-500" />
              <p className="text-sm font-medium">CMA Excel is ready!</p>
              <Button onClick={handleDownload} size="sm">
                <Download className="mr-1.5 h-4 w-4" />
                Download .xlsm
              </Button>
              <p className="text-xs text-muted-foreground">
                The download link expires in 60 seconds. Click again to get a new link.
              </p>
            </div>
          )}

          {state === "failed" && (
            <div className="flex flex-col items-center gap-4 py-6">
              <XCircle className="h-10 w-10 text-destructive" />
              <p className="text-sm font-medium text-destructive">
                {errorMsg ?? "Generation failed."}
              </p>
              <Button variant="outline" size="sm" onClick={handleRetry}>
                Retry
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
