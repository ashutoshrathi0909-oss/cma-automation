"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Building2, Edit2, FileText, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import type { Client } from "@/types";

const INDUSTRY_STYLES: Record<string, string> = {
  manufacturing: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  service: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  trading:
    "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  other: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useCurrentUser();

  const [client, setClient] = useState<Client | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!id) return;
    apiClient<Client>(`/api/clients/${id}`)
      .then(setClient)
      .catch(() => router.replace("/clients"))
      .finally(() => setLoading(false));
  }, [id, router]);

  async function handleDelete() {
    if (!client) return;
    if (!window.confirm(`Delete "${client.name}"? This cannot be undone.`)) return;

    setDeleting(true);
    try {
      await apiClient(`/api/clients/${client.id}`, { method: "DELETE" });
      toast.success(`"${client.name}" deleted`);
      router.replace("/clients");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete client");
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-7 w-32 animate-pulse rounded bg-muted" />
        <div className="h-40 animate-pulse rounded-xl bg-muted" />
      </div>
    );
  }

  if (!client) return null;

  const industryStyle =
    INDUSTRY_STYLES[client.industry_type] ?? INDUSTRY_STYLES.other;

  return (
    <div className="space-y-6">
      {/* Top bar: back + admin actions */}
      <div className="flex items-center justify-between">
        <Link
          href="/clients"
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          All Clients
        </Link>

        {user?.role === "admin" && (
          <div className="flex gap-2">
            <Link href={`/clients/${client.id}/edit`}>
              <Button variant="outline" size="sm">
                <Edit2 className="mr-1.5 h-3.5 w-3.5" />
                Edit
              </Button>
            </Link>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDelete}
              disabled={deleting}
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              {deleting ? "Deleting…" : "Delete"}
            </Button>
          </div>
        )}
      </div>

      {/* Client info card */}
      <Card>
        <CardHeader>
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Building2 className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>{client.name}</CardTitle>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${industryStyle}`}
                >
                  {client.industry_type}
                </span>
              </div>
              <CardDescription className="mt-0.5">
                FY ending {client.financial_year_ending} &middot; {client.currency}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        {client.notes && (
          <CardContent>
            <p className="text-sm text-muted-foreground">{client.notes}</p>
          </CardContent>
        )}
      </Card>

      {/* CMA Reports section — Phase 3+ */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">CMA Reports</h2>
          <Button size="sm" disabled title="Available after Phase 3">
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            New Report
          </Button>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <FileText className="mb-3 h-10 w-10 text-muted-foreground/30" />
            <p className="text-sm font-medium text-muted-foreground">
              No CMA reports yet
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Upload financial documents to start a new CMA report
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
