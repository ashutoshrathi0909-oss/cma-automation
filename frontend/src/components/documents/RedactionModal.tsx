"use client";

import { useEffect, useState } from "react";
import { Shield, Loader2, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import type { Document } from "@/types";

type Step = "detecting" | "previewing" | "applying" | "done";

interface RedactionModalProps {
  document: Document;
  isOpen: boolean;
  onClose: () => void;
  onRedactionComplete: (updatedDoc: Document) => void;
}

export function RedactionModal({
  document: doc,
  isOpen,
  onClose,
  onRedactionComplete,
}: RedactionModalProps) {
  const [step, setStep] = useState<Step>("detecting");
  const [detectedNames, setDetectedNames] = useState<string[]>([]);
  const [selectedNames, setSelectedNames] = useState<Set<string>>(new Set());
  const [customTerms, setCustomTerms] = useState("");
  const [termCounts, setTermCounts] = useState<Record<string, number>>({});
  const [totalInstances, setTotalInstances] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  // Auto-detect on open
  useEffect(() => {
    if (!isOpen) return;
    setStep("detecting");
    setDetectedNames([]);
    setSelectedNames(new Set());
    setCustomTerms("");
    setTermCounts({});
    setTotalInstances(0);
    setIsLoading(true);

    apiClient<{ document_id: string; detected_names: string[] }>(
      `/api/documents/${doc.id}/detect-names`,
      { method: "POST" }
    )
      .then((res) => {
        setDetectedNames(res.detected_names);
        setSelectedNames(new Set(res.detected_names));
      })
      .catch(() => {
        toast.error("Failed to detect company names");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [isOpen, doc.id]);

  function getTermsList(): string[] {
    const custom = customTerms
      .split(/[,\n]/)
      .map((t) => t.trim())
      .filter((t) => t.length > 0);
    return [...Array.from(selectedNames), ...custom];
  }

  async function handlePreview() {
    const terms = getTermsList();
    if (terms.length === 0) {
      toast.error("Select at least one term to redact");
      return;
    }
    setIsLoading(true);
    try {
      const res = await apiClient<{
        document_id: string;
        term_counts: Record<string, number>;
        total_instances: number;
      }>(`/api/documents/${doc.id}/preview-redaction`, {
        method: "POST",
        body: JSON.stringify({ terms }),
      });
      setTermCounts(res.term_counts);
      setTotalInstances(res.total_instances);
      setStep("previewing");
    } catch {
      toast.error("Failed to preview redaction");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleApply() {
    const terms = getTermsList();
    setStep("applying");
    setIsLoading(true);
    try {
      const res = await apiClient<{
        document_id: string;
        redacted_file_path: string;
        redaction_count: number;
        per_term_counts: Record<string, number>;
      }>(`/api/documents/${doc.id}/apply-redaction`, {
        method: "POST",
        body: JSON.stringify({ terms }),
      });
      setStep("done");
      toast.success(`Redacted ${res.redaction_count} instances across the document`);
      const updatedDoc: Document = {
        ...doc,
        redacted_file_path: res.redacted_file_path,
        redaction_count: res.redaction_count,
        redaction_terms: terms,
      };
      onRedactionComplete(updatedDoc);
    } catch {
      toast.error("Failed to apply redaction");
      setStep("previewing");
    } finally {
      setIsLoading(false);
    }
  }

  function toggleName(name: string) {
    setSelectedNames((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-600" />
            Redact Company Names
          </DialogTitle>
        </DialogHeader>

        {/* Step 1: Detect + Select */}
        {step === "detecting" && (
          <div className="space-y-4">
            {isLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Detecting company names...
              </div>
            ) : (
              <>
                {detectedNames.length > 0 && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Detected names</Label>
                    <div className="space-y-2">
                      {detectedNames.map((name) => (
                        <div key={name} className="flex items-center gap-2">
                          <Checkbox
                            id={`name-${name}`}
                            checked={selectedNames.has(name)}
                            onCheckedChange={() => toggleName(name)}
                          />
                          <label htmlFor={`name-${name}`} className="text-sm cursor-pointer">
                            {name}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {detectedNames.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No company names auto-detected. Add custom terms below.
                  </p>
                )}
                <div className="space-y-1">
                  <Label className="text-sm font-medium">Additional terms (comma or newline separated)</Label>
                  <Textarea
                    value={customTerms}
                    onChange={(e) => setCustomTerms(e.target.value)}
                    placeholder="e.g. ACME Corp, John Doe"
                    rows={3}
                    className="text-sm"
                  />
                </div>
                <Button
                  onClick={handlePreview}
                  disabled={isLoading || getTermsList().length === 0}
                  className="w-full"
                >
                  Preview Redaction
                </Button>
              </>
            )}
          </div>
        )}

        {/* Step 2: Preview */}
        {step === "previewing" && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Found <strong>{totalInstances}</strong> instance{totalInstances !== 1 ? "s" : ""} to redact across the document.
            </p>
            <div className="rounded-lg border divide-y">
              {Object.entries(termCounts).map(([term, count]) => (
                <div key={term} className="flex items-center justify-between px-3 py-2 text-sm">
                  <span className="truncate">{term}</span>
                  <Badge variant="secondary">{count}</Badge>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep("detecting")} className="flex-1">
                Back
              </Button>
              <Button onClick={handleApply} className="flex-1">
                Apply Redaction
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Applying */}
        {step === "applying" && (
          <div className="flex flex-col items-center gap-3 py-4">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <p className="text-sm text-muted-foreground">Applying redaction...</p>
          </div>
        )}

        {/* Step 4: Done */}
        {step === "done" && (
          <div className="flex flex-col items-center gap-3 py-4">
            <CheckCircle2 className="h-8 w-8 text-green-600" />
            <p className="text-sm font-medium">Redaction applied successfully</p>
            <Button onClick={onClose} className="w-full">
              Close
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
