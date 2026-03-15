"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { LineItemEditor } from "./LineItemEditor";
import type { LineItemResponse, Document } from "@/types";

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
              <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-2.5 text-xs text-muted-foreground">
                  {item.section ?? "—"}
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
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
