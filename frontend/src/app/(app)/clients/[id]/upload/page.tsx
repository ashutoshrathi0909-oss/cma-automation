"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { DocumentUploader } from "@/components/documents/DocumentUploader";
import { DocumentList } from "@/components/documents/DocumentList";
import { apiClient } from "@/lib/api";
import type { Client, Document } from "@/types";

export default function UploadPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [client, setClient] = useState<Client | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      apiClient<Client>(`/api/clients/${id}`),
      apiClient<Document[]>(`/api/documents/?client_id=${id}`),
    ])
      .then(([c, docs]) => {
        setClient(c);
        setDocuments(docs);
      })
      .catch(() => router.replace("/clients"))
      .finally(() => setLoading(false));
  }, [id, router]);

  function handleUploaded(doc: Document) {
    setDocuments((prev) => [doc, ...prev]);
  }

  function handleDeleted(docId: string) {
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-7 w-40 animate-pulse rounded bg-muted" />
        <div className="h-48 animate-pulse rounded-xl bg-muted" />
      </div>
    );
  }

  if (!client) return null;

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href={`/clients/${id}`}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to {client.name}
      </Link>

      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Upload Documents</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Upload financial documents for <span className="font-medium">{client.name}</span>
        </p>
      </div>

      {/* Uploader */}
      <div className="rounded-xl border bg-card p-6">
        <h2 className="mb-4 text-sm font-medium">Add New Document</h2>
        <DocumentUploader clientId={id} onUploaded={handleUploaded} />
      </div>

      {/* Document list */}
      <div>
        <h2 className="mb-3 text-lg font-medium">
          Uploaded Documents
          {documents.length > 0 && (
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({documents.length})
            </span>
          )}
        </h2>
        <DocumentList documents={documents} onDeleted={handleDeleted} />
      </div>
    </div>
  );
}
