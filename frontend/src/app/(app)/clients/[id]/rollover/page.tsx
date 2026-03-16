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
import { RolloverWizard } from "@/components/cma/RolloverWizard";
import type { Client, Document } from "@/types";

export default function RolloverPage() {
  const { id: clientId } = useParams<{ id: string }>();

  const [client, setClient] = useState<Client | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!clientId) return;
    Promise.all([
      apiClient<Client>(`/api/clients/${clientId}`),
      apiClient<Document[]>(`/api/documents?client_id=${clientId}`).catch(
        () => [] as Document[]
      ),
    ])
      .then(([c, docs]) => {
        setClient(c);
        setDocuments(docs);
      })
      .catch(() => setError("Failed to load client data"))
      .finally(() => setLoading(false));
  }, [clientId]);

  // Suggest from_year as the latest year in existing documents
  const suggestedFromYear =
    documents.length > 0
      ? Math.max(...documents.map((d) => d.financial_year))
      : undefined;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Link href={`/clients/${clientId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Annual Rollover</h1>
          {client && (
            <p className="text-sm text-gray-500">{client.name}</p>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">New Financial Year Rollover</CardTitle>
          <CardDescription>
            Carry forward balance sheet closing balances from the previous year
            as opening balances for the new financial year. P&amp;L items are
            not carried over.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {clientId && (
            <RolloverWizard
              clientId={clientId}
              suggestedFromYear={suggestedFromYear}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
