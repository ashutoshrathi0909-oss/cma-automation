"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, Trash2, Clock, CheckCircle2, AlertCircle, Loader2, Zap } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import type { Document, ExtractionStatus } from "@/types";

const STATUS_CONFIG: Record<
  ExtractionStatus,
  { label: string; icon: React.ReactNode; className: string }
> = {
  pending: {
    label: "Pending",
    icon: <Clock className="h-3 w-3" />,
    className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
  },
  processing: {
    label: "Processing",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
    className: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  },
  extracted: {
    label: "Extracted",
    icon: <CheckCircle2 className="h-3 w-3" />,
    className: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  },
  verified: {
    label: "Verified",
    icon: <CheckCircle2 className="h-3 w-3" />,
    className: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  },
  failed: {
    label: "Failed",
    icon: <AlertCircle className="h-3 w-3" />,
    className: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  },
};

const FILE_TYPE_ICONS: Record<string, string> = {
  pdf: "PDF",
  xlsx: "XLS",
  xls: "XLS",
};

const DOC_TYPE_LABELS: Record<string, string> = {
  profit_and_loss: "P&L",
  balance_sheet: "Balance Sheet",
  notes_to_accounts: "Notes",
  schedules: "Schedules",
  loan_repayment_schedule: "Loan Schedule",
  combined_financial_statement: "Combined",
};

interface DocumentListProps {
  documents: Document[];
  onDeleted: (id: string) => void;
}

export function DocumentList({ documents, onDeleted }: DocumentListProps) {
  const router = useRouter();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleDelete(doc: Document) {
    if (!window.confirm(`Delete "${doc.file_name}"? This cannot be undone.`)) return;
    setDeletingId(doc.id);
    try {
      await apiClient(`/api/documents/${doc.id}`, { method: "DELETE" });
      toast.success(`"${doc.file_name}" deleted`);
      onDeleted(doc.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete document");
    } finally {
      setDeletingId(null);
    }
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <FileText className="mb-2 h-8 w-8 text-muted-foreground/30" />
        <p className="text-sm text-muted-foreground">No documents uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="divide-y rounded-xl border">
      {documents.map((doc) => {
        const status = STATUS_CONFIG[doc.extraction_status] ?? STATUS_CONFIG.pending;
        const isDeleting = deletingId === doc.id;

        return (
          <div key={doc.id} className="flex items-center gap-3 px-4 py-3">
            {/* File type pill */}
            <span className="flex h-8 w-10 shrink-0 items-center justify-center rounded-md bg-muted text-xs font-bold text-muted-foreground">
              {FILE_TYPE_ICONS[doc.file_type] ?? doc.file_type.toUpperCase()}
            </span>

            {/* File info */}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{doc.file_name}</p>
              <p className="text-xs text-muted-foreground">
                {DOC_TYPE_LABELS[doc.document_type] ?? doc.document_type} ·{" "}
                FY {doc.financial_year - 1}–{doc.financial_year} ·{" "}
                <span className="capitalize">{doc.nature}</span>
              </p>
            </div>

            {/* Status badge */}
            <span
              className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${status.className}`}
            >
              {status.icon}
              {status.label}
            </span>

            {/* Extract & Verify button */}
            {(doc.extraction_status === "pending" || doc.extraction_status === "failed") && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(`/cma/${doc.id}/verify`)}
                className="shrink-0"
              >
                <Zap className="h-3.5 w-3.5" />
                Extract &amp; Verify
              </Button>
            )}

            {/* Delete */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDelete(doc)}
              disabled={isDeleting}
              className="shrink-0 text-muted-foreground hover:text-destructive"
            >
              {isDeleting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Trash2 className="h-3.5 w-3.5" />
              )}
            </Button>
          </div>
        );
      })}
    </div>
  );
}
