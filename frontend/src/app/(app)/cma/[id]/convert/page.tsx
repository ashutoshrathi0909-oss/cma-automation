"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import { ConversionDiff } from "@/components/cma/ConversionDiff";
import type {
  CMAReport,
  ConversionConfirmResponse,
  ConversionDiffResponse,
  Document,
} from "@/types";

export default function ConvertPage() {
  const { id: reportId } = useParams<{ id: string }>();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [provisionalDocId, setProvisionalDocId] = useState("");
  const [auditedDocId, setAuditedDocId] = useState("");
  const [diff, setDiff] = useState<ConversionDiffResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [confirmResult, setConfirmResult] = useState<ConversionConfirmResponse | null>(null);

  useEffect(() => {
    if (!reportId) return;
    apiClient<CMAReport>(`/api/cma-reports/${reportId}`)
      .then((r) => {
        if (r.document_ids.length > 0) {
          return Promise.all(
            r.document_ids.map((id) =>
              apiClient<Document>(`/api/documents/${id}`).catch(() => null)
            )
          );
        }
        return [];
      })
      .then((docs) => {
        const valid = (docs as (Document | null)[]).filter(Boolean) as Document[];
        setDocuments(valid);
        const prov = valid.find((d) => d.nature === "provisional");
        const aud = valid.find((d) => d.nature === "audited");
        if (prov) setProvisionalDocId(prov.id);
        if (aud) setAuditedDocId(aud.id);
      })
      .catch(() => setError("Failed to load report"))
      .finally(() => setLoading(false));
  }, [reportId]);

  async function handlePreview() {
    if (!provisionalDocId || !auditedDocId) return;
    setPreviewLoading(true);
    setError(null);
    try {
      const data = await apiClient<ConversionDiffResponse>("/api/conversion/preview", {
        method: "POST",
        body: JSON.stringify({
          provisional_doc_id: provisionalDocId,
          audited_doc_id: auditedDocId,
        }),
      });
      setDiff(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleConfirm() {
    if (!diff || !reportId) return;
    setConfirmLoading(true);
    setError(null);
    try {
      const data = await apiClient<ConversionConfirmResponse>("/api/conversion/confirm", {
        method: "POST",
        body: JSON.stringify({
          provisional_doc_id: provisionalDocId,
          audited_doc_id: auditedDocId,
          cma_report_id: reportId,
        }),
      });
      setConfirmResult(data);
      setConfirmed(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Conversion failed");
    } finally {
      setConfirmLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  const provisionalDocs = documents.filter((d) => d.nature === "provisional");
  const auditedDocs = documents.filter((d) => d.nature === "audited");

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-3">
        <Link href={`/cma/${reportId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        </Link>
        <h1 className="text-xl font-semibold text-gray-900">
          Provisional → Audited Conversion
        </h1>
      </div>

      {confirmed && confirmResult ? (
        <Card>
          <CardContent className="pt-6">
            <div className="rounded-lg bg-green-50 border border-green-200 p-4 text-sm text-green-800">
              <p className="font-medium">Conversion complete.</p>
              <p>
                {confirmResult.updated_count} line item(s) updated.{" "}
                {confirmResult.flagged_for_review} classification(s) flagged for
                re-review.
              </p>
            </div>
            <div className="mt-4">
              <Link href={`/cma/${reportId}/doubts`}>
                <Button>Review Flagged Items</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Select Documents</CardTitle>
              <CardDescription>
                Choose the provisional and audited versions to compare.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Provisional Document
                  </label>
                  <select
                    value={provisionalDocId}
                    onChange={(e) => setProvisionalDocId(e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
                  >
                    <option value="">— Select —</option>
                    {provisionalDocs.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.file_name} (FY {d.financial_year})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Audited Document
                  </label>
                  <select
                    value={auditedDocId}
                    onChange={(e) => setAuditedDocId(e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
                  >
                    <option value="">— Select —</option>
                    {auditedDocs.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.file_name} (FY {d.financial_year})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {error && (
                <p className="text-sm text-red-600">{error}</p>
              )}

              <Button
                onClick={handlePreview}
                disabled={previewLoading || !provisionalDocId || !auditedDocId}
              >
                {previewLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Preview Differences
              </Button>
            </CardContent>
          </Card>

          {diff && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Differences Found</CardTitle>
                <CardDescription>
                  Review all changes before confirming the conversion.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ConversionDiff diff={diff} />

                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                  Confirming will update provisional amounts to audited values and
                  flag affected classifications for re-review.
                </div>

                <Button onClick={handleConfirm} disabled={confirmLoading}>
                  {confirmLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Confirm Conversion
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
