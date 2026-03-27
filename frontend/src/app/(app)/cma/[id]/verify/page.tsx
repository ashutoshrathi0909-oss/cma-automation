"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, AlertCircle, CheckCircle2, FileSpreadsheet, FileText, Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api";
import { ProgressTracker } from "@/components/common/ProgressTracker";
import { ExtractionVerifier } from "@/components/extraction/ExtractionVerifier";
import type { Document, ExtractionTriggerResponse, SheetInfo, SheetsPreviewResponse } from "@/types";

interface PageCountResponse {
  document_id: string;
  page_count: number;
}

interface FilterPagesResponse {
  document_id: string;
  original_page_count: number;
  removed_pages: number[];
  filtered_page_count: number;
}

type PageState =
  | { phase: "loading" }
  | { phase: "sheet_selection"; sheets: SheetInfo[] }
  | { phase: "page_filter"; pageCount: number }
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
  const [selectedSheets, setSelectedSheets] = useState<Set<string>>(new Set());

  // Page filter state
  const [pageRangeInput, setPageRangeInput] = useState("");
  const [filterApplied, setFilterApplied] = useState(false);
  const [filterResult, setFilterResult] = useState<FilterPagesResponse | null>(null);
  const [isFiltering, setIsFiltering] = useState(false);

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
        if (d.file_type === "xlsx" || d.file_type === "xls") {
          loadSheetPreview(d.id);
        } else {
          // PDF: show page filter step before extraction
          loadPageCount(d.id);
        }
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
        if (d.file_type === "xlsx" || d.file_type === "xls") {
          loadSheetPreview(d.id);
        } else {
          // PDF failed: show page filter so user can re-filter and retry
          loadPageCount(d.id);
        }
        break;
    }
  }

  async function loadPageCount(docId: string) {
    try {
      const result = await apiClient<PageCountResponse>(
        `/api/documents/${docId}/page-count`
      );
      setPageState({ phase: "page_filter", pageCount: result.page_count });

      // If pages were previously filtered, pre-populate state so user sees current filter
      setFilterApplied(false);
      setFilterResult(null);
      setPageRangeInput("");
    } catch {
      // If page-count endpoint fails, fall through to extraction directly
      triggerExtraction(docId);
    }
  }

  async function loadSheetPreview(docId: string) {
    try {
      const preview = await apiClient<SheetsPreviewResponse>(
        `/api/documents/${docId}/sheets`
      );
      const autoSelected = new Set(
        preview.sheets.filter((s) => s.auto_included).map((s) => s.name)
      );
      setSelectedSheets(autoSelected);
      setPageState({ phase: "sheet_selection", sheets: preview.sheets });
    } catch {
      // If sheet preview fails, fall back to auto-detection
      triggerExtraction(docId);
    }
  }

  function toggleSheet(name: string) {
    setSelectedSheets((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  }

  function selectAll(sheets: SheetInfo[]) {
    setSelectedSheets(new Set(sheets.map((s) => s.name)));
  }

  function deselectAll() {
    setSelectedSheets(new Set());
  }

  async function handleApplyFilter() {
    if (!doc || !pageRangeInput.trim()) return;
    setIsFiltering(true);
    try {
      const result = await apiClient<FilterPagesResponse>(
        `/api/documents/${doc.id}/filter-pages`,
        {
          method: "POST",
          body: JSON.stringify({ pages_to_remove: pageRangeInput.trim() }),
        }
      );
      setFilterResult(result);
      setFilterApplied(true);
      toast.success(
        `Removed ${result.removed_pages.length} page(s). Keeping ${result.filtered_page_count} of ${result.original_page_count} pages.`
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to apply page filter");
    } finally {
      setIsFiltering(false);
    }
  }

  function handleReFilter() {
    setFilterApplied(false);
    setFilterResult(null);
    setPageRangeInput("");
  }

  async function triggerExtraction(docId: string, sheets?: string[]) {
    setPageState({ phase: "triggering" });
    try {
      const body = sheets ? { selected_sheets: sheets } : undefined;
      const result = await apiClient<ExtractionTriggerResponse>(
        `/api/documents/${docId}/extract`,
        {
          method: "POST",
          body: body ? JSON.stringify(body) : undefined,
        }
      );
      setPageState({ phase: "tracking", taskId: result.task_id });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to start extraction");
      setPageState({ phase: "failed" });
    }
  }

  function handleStartExtraction() {
    if (!doc) return;
    const sheets = selectedSheets.size > 0 ? Array.from(selectedSheets) : undefined;
    triggerExtraction(doc.id, sheets);
  }

  function handleStartPdfExtraction() {
    if (!doc) return;
    void triggerExtraction(doc.id);
  }

  function handleExtractionComplete() {
    setPageState({ phase: "verifier" });
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
    if (doc.file_type === "xlsx" || doc.file_type === "xls") {
      loadSheetPreview(doc.id);
    } else {
      loadPageCount(doc.id);
    }
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

        {pageState.phase === "sheet_selection" && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-medium">Select Sheets to Extract</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              Choose which sheets contain financial data. Sheets are auto-detected, but you can
              adjust the selection below.
            </p>

            {/* Select all / Deselect all */}
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => selectAll(pageState.sheets)}
              >
                Select all
              </Button>
              <Button variant="ghost" size="sm" onClick={deselectAll}>
                Deselect all
              </Button>
              <span className="ml-auto text-xs text-muted-foreground">
                {selectedSheets.size} of {pageState.sheets.length} selected
              </span>
            </div>

            {/* Sheet list */}
            <div className="divide-y rounded-lg border">
              {pageState.sheets.map((sheet) => {
                const isSelected = selectedSheets.has(sheet.name);
                return (
                  <label
                    key={sheet.name}
                    className={`flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-muted/50 transition-colors ${
                      isSelected ? "bg-primary/5" : ""
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleSheet(sheet.name)}
                      className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-medium">{sheet.name}</span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({sheet.rows} rows)
                      </span>
                    </div>
                    {sheet.auto_included && (
                      <Badge variant="secondary" className="text-xs">
                        Auto-detected
                      </Badge>
                    )}
                  </label>
                );
              })}
            </div>

            {/* Action buttons */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(backHref)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleStartExtraction}
                disabled={selectedSheets.size === 0}
              >
                Extract Selected Sheets
              </Button>
            </div>
          </div>
        )}

        {pageState.phase === "page_filter" && (
          <div className="space-y-5">
            {/* Header */}
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-medium">Prepare PDF for Extraction</h2>
            </div>

            <p className="text-sm text-muted-foreground">
              PDF has <span className="font-medium text-foreground">{pageState.pageCount} pages</span>.
              Optionally remove unnecessary pages before extraction to save processing time.
            </p>

            {/* Show existing filter if already applied */}
            {doc?.removed_pages && doc.removed_pages.length > 0 && !filterApplied && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm">
                <p className="font-medium text-amber-800">Previously filtered</p>
                <p className="mt-0.5 text-amber-700">
                  Pages {doc.removed_pages.join(", ")} were removed in a previous session.
                  You can apply a new filter below or proceed to extraction.
                </p>
              </div>
            )}

            {/* Filter result success message */}
            {filterApplied && filterResult && (
              <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                  <p className="font-medium text-green-800">Filter applied</p>
                </div>
                <p className="mt-0.5 text-green-700">
                  Removed pages {filterResult.removed_pages.join(", ")}. Keeping{" "}
                  <span className="font-medium">{filterResult.filtered_page_count}</span> of{" "}
                  {filterResult.original_page_count} pages.
                </p>
                <button
                  onClick={handleReFilter}
                  className="mt-1.5 text-xs text-green-600 underline hover:text-green-800"
                >
                  Change filter
                </button>
              </div>
            )}

            {/* Filter input — hidden once filter is applied */}
            {!filterApplied && (
              <div className="rounded-lg border bg-muted/30 px-4 py-4 space-y-3">
                <div className="space-y-1.5">
                  <Label htmlFor="page-range" className="text-sm font-medium">
                    Pages to remove
                  </Label>
                  <Input
                    id="page-range"
                    placeholder="e.g. 1-2, 7, 10-15"
                    value={pageRangeInput}
                    onChange={(e) => setPageRangeInput(e.target.value)}
                    className="max-w-sm"
                  />
                  <p className="text-xs text-muted-foreground">
                    Remove cover pages, auditor reports, or blank pages to save processing time.
                    Leave blank to process all pages.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleApplyFilter}
                  disabled={isFiltering || !pageRangeInput.trim()}
                >
                  {isFiltering && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  Apply Filter
                </Button>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(backHref)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleStartPdfExtraction}
              >
                Start Extraction
              </Button>
            </div>
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
