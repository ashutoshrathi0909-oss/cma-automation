"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { createClient } from "@/lib/supabase/client";
import type { Document } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.ms-excel": [".xls"],
};

const DOCUMENT_TYPES = [
  { value: "profit_and_loss", label: "Profit & Loss" },
  { value: "balance_sheet", label: "Balance Sheet" },
  { value: "notes_to_accounts", label: "Notes to Accounts" },
  { value: "schedules", label: "Schedules" },
  { value: "loan_repayment_schedule", label: "Loan Repayment Schedule" },
  { value: "combined_financial_statement", label: "Combined Financial Statement" },
];

interface DocumentUploaderProps {
  clientId: string;
  onUploaded: (doc: Document) => void;
}

type UploadState = "idle" | "uploading" | "success" | "error";

export function DocumentUploader({ clientId, onUploaded }: DocumentUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState("profit_and_loss");
  const [financialYear, setFinancialYear] = useState(new Date().getFullYear().toString());
  const [nature, setNature] = useState("audited");
  const [uploadState, setUploadState] = useState<UploadState>("idle");

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50 MB
    onDropRejected: (rejections) => {
      const reason = rejections[0]?.errors[0]?.message ?? "Invalid file";
      toast.error(reason);
    },
  });

  async function handleUpload() {
    if (!file) return;
    setUploadState("uploading");

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      const formData = new FormData();
      formData.append("file", file);
      formData.append("client_id", clientId);
      formData.append("document_type", documentType);
      formData.append("financial_year", financialYear);
      formData.append("nature", nature);

      const res = await fetch(`${API_URL}/api/documents/`, {
        method: "POST",
        headers: session?.access_token
          ? { Authorization: `Bearer ${session.access_token}` }
          : {},
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? "Upload failed");
      }

      const doc: Document = await res.json();
      setUploadState("success");
      toast.success(`"${file.name}" uploaded successfully`);
      onUploaded(doc);

      // Reset form after short delay
      setTimeout(() => {
        setFile(null);
        setUploadState("idle");
      }, 1500);
    } catch (err) {
      setUploadState("error");
      toast.error(err instanceof Error ? err.message : "Upload failed");
    }
  }

  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i);

  return (
    <div className="space-y-5">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors ${
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30"
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <div className="flex items-center gap-3 text-sm">
            <FileText className="h-8 w-8 text-primary" />
            <div>
              <p className="font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {(file.size / 1024).toFixed(0)} KB
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
                setUploadState("idle");
              }}
              className="ml-2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <Upload className="mb-3 h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm font-medium">
              {isDragActive ? "Drop the file here" : "Drag & drop or click to select"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              PDF, XLSX, XLS — up to 50 MB
            </p>
          </>
        )}
      </div>

      {/* Form fields (shown when file selected) */}
      {file && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="doc_type">Document Type</Label>
            <Select
              id="doc_type"
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
            >
              {DOCUMENT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="fin_year">Financial Year</Label>
            <Select
              id="fin_year"
              value={financialYear}
              onChange={(e) => setFinancialYear(e.target.value)}
            >
              {yearOptions.map((y) => (
                <option key={y} value={y}>
                  FY {y - 1}–{y}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="nature">Nature</Label>
            <Select
              id="nature"
              value={nature}
              onChange={(e) => setNature(e.target.value)}
            >
              <option value="audited">Audited</option>
              <option value="provisional">Provisional</option>
            </Select>
          </div>
        </div>
      )}

      {/* Upload button */}
      {file && (
        <Button
          onClick={handleUpload}
          disabled={uploadState === "uploading" || uploadState === "success"}
          className="w-full sm:w-auto"
        >
          {uploadState === "uploading" && "Uploading…"}
          {uploadState === "success" && (
            <span className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4" /> Uploaded
            </span>
          )}
          {uploadState === "error" && (
            <span className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" /> Retry Upload
            </span>
          )}
          {uploadState === "idle" && (
            <span className="flex items-center gap-2">
              <Upload className="h-4 w-4" /> Upload Document
            </span>
          )}
        </Button>
      )}
    </div>
  );
}
