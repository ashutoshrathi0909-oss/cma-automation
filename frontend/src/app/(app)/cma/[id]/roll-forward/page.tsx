"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  FileText,
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
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import type { RollForwardPreviewResponse, RollForwardConfirmResponse } from "@/types";

type Step = "preview" | "confirm" | "done";

export default function RollForwardPage() {
  const { id: reportId } = useParams<{ id: string }>();
  const router = useRouter();

  const [step, setStep] = useState<Step>("preview");
  const [preview, setPreview] = useState<RollForwardPreviewResponse | null>(null);
  const [result, setResult] = useState<RollForwardConfirmResponse | null>(null);
  const [title, setTitle] = useState("");
  const [outputUnit, setOutputUnit] = useState<"lakhs" | "crores">("lakhs");
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch preview on mount
  useEffect(() => {
    if (!reportId) return;

    apiClient<RollForwardPreviewResponse>("/api/roll-forward/preview", {
      method: "POST",
      body: JSON.stringify({ source_report_id: reportId, client_id: "" }),
    })
      .then((data) => {
        setPreview(data);
        setTitle(`${data.source_report_title} → FY${data.add_year}`);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Preview failed"))
      .finally(() => setLoading(false));
  }, [reportId]);

  async function handleConfirm() {
    if (!preview) return;
    setConfirming(true);
    setError(null);
    try {
      const newDocIds = preview.new_year_documents.map((d) => d.id);
      const data = await apiClient<RollForwardConfirmResponse>(
        "/api/roll-forward/confirm",
        {
          method: "POST",
          body: JSON.stringify({
            source_report_id: reportId,
            client_id: preview.carried_documents[0]?.client_id || "",
            add_year: preview.add_year,
            new_document_ids: newDocIds,
            title: title || undefined,
            cma_output_unit: outputUnit,
          }),
        }
      );
      setResult(data);
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Roll forward failed");
    } finally {
      setConfirming(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading preview…</span>
      </div>
    );
  }

  if (error && !preview) {
    return (
      <div className="space-y-4">
        <Link
          href={`/cma/${reportId}`}
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Report
        </Link>
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      </div>
    );
  }

  if (!preview) return null;

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Back link */}
      <Link
        href={`/cma/${reportId}`}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Report
      </Link>

      <h1 className="text-2xl font-semibold tracking-tight">Roll Forward</h1>

      {/* Step indicator */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        {(["preview", "confirm", "done"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            {i > 0 && <ArrowRight className="h-3 w-3" />}
            <span className={step === s ? "font-medium text-gray-900" : ""}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </span>
          </div>
        ))}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Step 1: Preview */}
      {step === "preview" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Year Window Shift</CardTitle>
              <CardDescription>
                {preview.source_report_title} — {preview.source_years.map((y) => `FY${y}`).join(", ")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Dropping */}
              {preview.drop_year && (
                <div className="flex items-start gap-3 rounded-lg bg-gray-50 p-3">
                  <XCircle className="h-5 w-5 text-gray-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Dropping FY{preview.drop_year}
                    </p>
                    <p className="text-xs text-gray-500">
                      {preview.dropped_documents.length} document(s) will no longer be included
                    </p>
                  </div>
                </div>
              )}

              {/* Keeping */}
              <div className="flex items-start gap-3 rounded-lg bg-green-50 p-3">
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-green-800">
                    Keeping {preview.keep_years.map((y) => `FY${y}`).join(", ")}
                  </p>
                  <p className="text-xs text-green-600">
                    {preview.carried_documents.length} document(s), {preview.carried_classifications_count} classifications carried forward
                  </p>
                </div>
              </div>

              {/* Adding */}
              <div
                className={`flex items-start gap-3 rounded-lg p-3 ${
                  preview.new_year_docs_ready
                    ? "bg-green-50"
                    : "bg-amber-50"
                }`}
              >
                {preview.new_year_docs_ready ? (
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 shrink-0" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 shrink-0" />
                )}
                <div>
                  <p
                    className={`text-sm font-medium ${
                      preview.new_year_docs_ready ? "text-green-800" : "text-amber-800"
                    }`}
                  >
                    Adding FY{preview.add_year}
                  </p>
                  {preview.new_year_documents.length === 0 ? (
                    <p className="text-xs text-amber-600">
                      No documents uploaded yet.{" "}
                      <Link href={`/clients`} className="underline">
                        Upload documents
                      </Link>
                    </p>
                  ) : (
                    <div className="mt-1 space-y-1">
                      {preview.new_year_documents.map((doc) => (
                        <div key={doc.id} className="flex items-center gap-2 text-xs">
                          <FileText className="h-3 w-3" />
                          <span>{doc.file_name}</span>
                          <Badge
                            variant={doc.extraction_status === "verified" ? "default" : "secondary"}
                            className="text-[10px] px-1.5 py-0"
                          >
                            {doc.extraction_status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Blocking reasons */}
          {preview.blocking_reasons.length > 0 && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-sm text-amber-700">
              <p className="font-medium">Cannot proceed yet:</p>
              <ul className="mt-1 list-disc list-inside">
                {preview.blocking_reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>
          )}

          <Button
            onClick={() => setStep("confirm")}
            disabled={!preview.can_confirm}
          >
            Next
            <ArrowRight className="ml-1.5 h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Step 2: Confirm */}
      {step === "confirm" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Confirm Roll Forward</CardTitle>
              <CardDescription>
                New report: FY{preview.target_years.join(", FY")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Report Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
                  placeholder="Auto-generated if left empty"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Output Unit
                </label>
                <select
                  value={outputUnit}
                  onChange={(e) => setOutputUnit(e.target.value as "lakhs" | "crores")}
                  className="rounded border border-gray-300 px-3 py-1.5 text-sm"
                >
                  <option value="lakhs">Lakhs</option>
                  <option value="crores">Crores</option>
                </select>
              </div>

              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                This will create a new draft CMA report. Classifications for{" "}
                {preview.keep_years.map((y) => `FY${y}`).join(", ")} will be
                carried forward. FY{preview.add_year} items will need
                classification.
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setStep("preview")}>
              Back
            </Button>
            <Button onClick={handleConfirm} disabled={confirming}>
              {confirming && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Report
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Done */}
      {step === "done" && result && (
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 shrink-0" />
            <div className="text-sm text-green-800">
              <p className="font-medium">Roll forward complete!</p>
              <p className="mt-1">{result.message}</p>
            </div>
          </div>
          <Button onClick={() => router.push(`/cma/${result.new_report_id}/review`)}>
            Go to Report
            <ArrowRight className="ml-1.5 h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
