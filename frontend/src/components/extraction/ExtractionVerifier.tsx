"use client";

import { Fragment, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { LineItemEditor } from "./LineItemEditor";
import type { LineItemResponse, Document } from "@/types";

function pageTypeBadge(pageType: string | null | undefined) {
  if (!pageType || pageType === "unknown") return null;
  if (pageType === "notes") {
    return (
      <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
        Notes
      </span>
    );
  }
  if (pageType === "face") {
    return (
      <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-slate-100 text-slate-600 dark:bg-slate-800/50 dark:text-slate-400">
        Face
      </span>
    );
  }
  return null;
}

interface ExtractionVerifierProps {
  documentId: string;
  onVerified: () => void;
}

export function ExtractionVerifier({ documentId, onVerified }: ExtractionVerifierProps) {
  const [items, setItems] = useState<LineItemResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiClient<LineItemResponse[]>(`/api/documents/${documentId}/items`)
      .then(setItems)
      .catch(() => toast.error("Failed to load extracted items"))
      .finally(() => setLoading(false));
  }, [documentId]);

  function handleSaved(updated: LineItemResponse) {
    setItems((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
  }

  async function handleVerifyAll() {
    setVerifying(true);
    try {
      await apiClient<Document>(`/api/documents/${documentId}/verify`, { method: "POST" });
      toast.success("All items verified successfully");
      onVerified();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to verify document");
    } finally {
      setVerifying(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-10">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <p className="text-sm text-muted-foreground">No items extracted yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{items.length}</span> items extracted
        </p>
        <Button
          onClick={() => void handleVerifyAll()}
          disabled={verifying}
          size="sm"
        >
          {verifying ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Verifying…
            </>
          ) : (
            <>
              <CheckCircle2 className="h-3.5 w-3.5" />
              Verify All
            </>
          )}
        </Button>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">
                Section
              </th>
              <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">
                Description
              </th>
              <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">
                Amount (₹)
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.map((item) => (
              <Fragment key={item.id}>
                <tr className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-2.5 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <span>{item.section ?? "—"}</span>
                      {pageTypeBadge(item.page_type)}
                    </div>
                  </td>
                  <td className="max-w-xs px-4 py-2.5">
                    <span className="line-clamp-2">{item.description}</span>
                    {item.raw_text && item.raw_text !== item.description && (
                      <span className="mt-0.5 block truncate text-xs text-muted-foreground">
                        {item.raw_text}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <LineItemEditor item={item} onSaved={handleSaved} />
                  </td>
                </tr>
                {item.ambiguity_question && (
                  <tr key={`${item.id}-ambiguity`} className="bg-amber-50 dark:bg-amber-950/20 border-b border-amber-100">
                    <td colSpan={3} className="px-4 py-2">
                      <div className="flex items-start gap-2 text-xs">
                        <AlertTriangle className="h-3.5 w-3.5 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                          <span className="font-semibold text-amber-700 dark:text-amber-400">
                            Needs clarification:{" "}
                          </span>
                          <span className="text-amber-600 dark:text-amber-300">
                            {item.ambiguity_question}
                          </span>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
