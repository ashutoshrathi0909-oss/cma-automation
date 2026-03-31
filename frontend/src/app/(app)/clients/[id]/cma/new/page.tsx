"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import type { CMAReport, Client, Document } from "@/types";

export default function NewCMAReportPage() {
  const { id: clientId } = useParams<{ id: string }>();
  const router = useRouter();

  const [client, setClient] = useState<Client | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [title, setTitle] = useState("");
  const [cmaOutputUnit, setCmaOutputUnit] = useState("lakhs");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!clientId) return;
    Promise.all([
      apiClient<Client>(`/api/clients/${clientId}`),
      apiClient<Document[]>(`/api/documents/?client_id=${clientId}`),
    ])
      .then(([c, docs]) => {
        setClient(c);
        const verified = docs.filter((d) => d.extraction_status === "verified");
        setDocuments(verified);
        setTitle(`CMA Report — ${c.name}`);
      })
      .catch(() => router.replace(`/clients/${clientId}`))
      .finally(() => setLoading(false));
  }, [clientId, router]);

  function toggleDoc(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function handleCreate() {
    if (selectedIds.size === 0 || !title.trim()) return;
    setSubmitting(true);
    try {
      const report = await apiClient<CMAReport>(
        `/api/clients/${clientId}/cma-reports`,
        {
          method: "POST",
          body: JSON.stringify({
            title: title.trim(),
            document_ids: Array.from(selectedIds),
            cma_output_unit: cmaOutputUnit,
          }),
        }
      );
      toast.success("CMA report created");
      router.push(`/cma/${report.id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create report");
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        href={`/clients/${clientId}`}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to {client?.name ?? "client"}
      </Link>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New CMA Report</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Select verified documents to include in this report.
        </p>
      </div>

      {/* Report title */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Report Title</CardTitle>
        </CardHeader>
        <CardContent>
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. FY2024 CMA Report"
            className="mt-1"
          />

          <div className="mt-4">
            <Label htmlFor="cma_output_unit">CMA Output Unit</Label>
            <Select
              id="cma_output_unit"
              value={cmaOutputUnit}
              onChange={(e) => setCmaOutputUnit(e.target.value)}
              className="mt-1"
            >
              <option value="lakhs">Lakhs</option>
              <option value="crores">Crores</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Document picker */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Select Documents</CardTitle>
          <CardDescription>
            Only verified documents are shown. Select at least one.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {documents.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-8 text-center">
              <FileText className="h-8 w-8 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">
                No verified documents found. Verify documents before creating a
                CMA report.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => {
                const selected = selectedIds.has(doc.id);
                return (
                  <button
                    key={doc.id}
                    type="button"
                    onClick={() => toggleDoc(doc.id)}
                    className={`w-full rounded-lg border p-3 text-left transition-colors ${
                      selected
                        ? "border-primary bg-primary/5"
                        : "border-border hover:bg-muted/40"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">
                          {doc.file_name}
                        </p>
                        <p className="mt-0.5 text-xs text-muted-foreground capitalize">
                          {doc.document_type.replace(/_/g, " ")} · FY{doc.financial_year} ·{" "}
                          {doc.nature}
                        </p>
                      </div>
                      <Badge
                        className={
                          selected
                            ? "bg-primary/10 text-primary"
                            : "bg-muted text-muted-foreground"
                        }
                      >
                        {selected ? "Selected" : "Select"}
                      </Badge>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {selectedIds.size} document{selectedIds.size !== 1 ? "s" : ""} selected
        </p>
        <Button
          onClick={handleCreate}
          disabled={selectedIds.size === 0 || !title.trim() || submitting}
        >
          {submitting ? (
            <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
          ) : (
            <Plus className="mr-1.5 h-4 w-4" />
          )}
          Create Report
        </Button>
      </div>
    </div>
  );
}
