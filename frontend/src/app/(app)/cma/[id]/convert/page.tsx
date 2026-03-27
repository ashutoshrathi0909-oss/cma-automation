"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ConversionDiffV2 } from "@/components/cma/ConversionDiff";
import type { ConversionPreviewResponseV2, ConversionConfirmResponseV2, Document } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const steps = [
  { label: "Select Provisional", description: "Choose the provisional document to replace" },
  { label: "Select Audited", description: "Choose the audited document" },
  { label: "Review Diff", description: "Review the differences between documents" },
  { label: "Confirm", description: "Apply changes" },
];

export default function ConvertPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;

  const [currentStep, setCurrentStep] = useState(0);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedProvisional, setSelectedProvisional] = useState<string | null>(null);
  const [selectedAudited, setSelectedAudited] = useState<string | null>(null);
  const [diffPreview, setDiffPreview] = useState<ConversionPreviewResponseV2 | null>(null);
  const [confirmResult, setConfirmResult] = useState<ConversionConfirmResponseV2 | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch documents for this report
  useEffect(() => {
    async function fetchDocs() {
      try {
        const res = await fetch(`${API_BASE}/api/cma-reports/${reportId}`, { credentials: "include" });
        if (!res.ok) throw new Error("Failed to load report");
        const report = await res.json();
        const docIds: string[] = report.document_ids || [];

        const docPromises = docIds.map((id: string) =>
          fetch(`${API_BASE}/api/documents/${id}`, { credentials: "include" }).then((r) => r.json())
        );
        const docs = await Promise.all(docPromises);
        setDocuments(docs);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load documents");
      }
    }
    fetchDocs();
  }, [reportId]);

  const provisionalDocs = documents.filter((d) => d.nature === "provisional");
  const auditedDocs = documents.filter((d) => d.nature === "audited");

  const handlePreview = useCallback(async () => {
    if (!selectedProvisional || !selectedAudited) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/conversion/v2/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          provisional_doc_id: selectedProvisional,
          audited_doc_id: selectedAudited,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Preview failed");
      }
      const data: ConversionPreviewResponseV2 = await res.json();
      setDiffPreview(data);
      setCurrentStep(2);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setLoading(false);
    }
  }, [selectedProvisional, selectedAudited]);

  const handleConfirm = useCallback(async () => {
    if (!selectedProvisional || !selectedAudited) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/conversion/v2/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          provisional_doc_id: selectedProvisional,
          audited_doc_id: selectedAudited,
          cma_report_id: reportId,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Confirm failed");
      }
      const data: ConversionConfirmResponseV2 = await res.json();
      setConfirmResult(data);
      setCurrentStep(3);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Conversion failed");
    } finally {
      setLoading(false);
    }
  }, [selectedProvisional, selectedAudited, reportId]);

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Provisional &rarr; Audited Conversion
      </h1>
      <p className="text-sm text-gray-500 mb-8">
        Replace provisional figures with audited data. Only changed items will be updated.
      </p>

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-8">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
              idx < currentStep
                ? "bg-green-500 text-white"
                : idx === currentStep
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-500"
            }`}>
              {idx < currentStep ? "\u2713" : idx + 1}
            </div>
            <span className={`text-sm ${idx === currentStep ? "font-medium text-gray-900" : "text-gray-500"}`}>
              {step.label}
            </span>
            {idx < steps.length - 1 && <div className="w-8 h-px bg-gray-300" />}
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Step 1: Select provisional */}
      {currentStep === 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Select Provisional Document</h2>
          <p className="text-sm text-gray-500">Choose the provisional document you want to replace with audited data.</p>
          {provisionalDocs.length === 0 ? (
            <p className="text-sm text-gray-400">No provisional documents found for this report.</p>
          ) : (
            <div className="grid gap-3">
              {provisionalDocs.map((doc) => (
                <button
                  key={doc.id}
                  onClick={() => { setSelectedProvisional(doc.id); setCurrentStep(1); }}
                  className={`text-left p-4 rounded-lg border-2 transition-colors ${
                    selectedProvisional === doc.id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="font-medium text-gray-900">{doc.file_name}</div>
                  <div className="text-sm text-gray-500 mt-1">
                    FY {doc.financial_year} &middot; {doc.document_type?.replace(/_/g, " ")} &middot; {doc.nature}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step 2: Select audited */}
      {currentStep === 1 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Select Audited Document</h2>
          <p className="text-sm text-gray-500">Choose the audited document that will replace the provisional figures.</p>
          {auditedDocs.length === 0 ? (
            <p className="text-sm text-gray-400">No audited documents found. Upload one first.</p>
          ) : (
            <div className="grid gap-3">
              {auditedDocs.map((doc) => (
                <button
                  key={doc.id}
                  onClick={() => { setSelectedAudited(doc.id); handlePreview(); }}
                  className={`text-left p-4 rounded-lg border-2 transition-colors ${
                    selectedAudited === doc.id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="font-medium text-gray-900">{doc.file_name}</div>
                  <div className="text-sm text-gray-500 mt-1">
                    FY {doc.financial_year} &middot; {doc.document_type?.replace(/_/g, " ")} &middot; {doc.nature}
                  </div>
                </button>
              ))}
            </div>
          )}
          <button
            onClick={() => setCurrentStep(0)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            &larr; Back
          </button>
        </div>
      )}

      {/* Step 3: Diff preview */}
      {currentStep === 2 && diffPreview && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Review Differences</h2>
          <ConversionDiffV2
            diff={diffPreview}
            onAcceptAllAmountChanges={() => {/* handled on confirm */}}
          />
          <div className="flex gap-3 pt-4">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              &larr; Back
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Applying..." : "Confirm Conversion"}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Confirm result */}
      {currentStep === 3 && confirmResult && (
        <div className="space-y-6">
          <div className="rounded-lg border border-green-200 bg-green-50 p-6">
            <h2 className="text-lg font-semibold text-green-800 mb-2">Conversion Complete</h2>
            <p className="text-sm text-green-700 mb-4">{confirmResult.message}</p>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { label: "Unchanged", value: confirmResult.unchanged, color: "text-green-700" },
                { label: "Amounts Updated", value: confirmResult.amount_updated, color: "text-yellow-700" },
                { label: "Reclassified", value: confirmResult.reclassified, color: "text-red-700" },
                { label: "Added", value: confirmResult.added, color: "text-blue-700" },
                { label: "Removed", value: confirmResult.removed, color: "text-gray-700" },
              ].map(({ label, value, color }) => (
                <div key={label} className="text-center">
                  <div className={`text-2xl font-bold ${color}`}>{value}</div>
                  <div className="text-xs text-gray-500">{label}</div>
                </div>
              ))}
            </div>
          </div>
          <button
            onClick={() => router.push(`/cma/${reportId}/review`)}
            className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Go to Review Page &rarr;
          </button>
        </div>
      )}

      {loading && currentStep < 2 && (
        <div className="flex items-center gap-2 text-sm text-gray-500 mt-4">
          <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-blue-600 rounded-full" />
          Computing diff...
        </div>
      )}
    </div>
  );
}
