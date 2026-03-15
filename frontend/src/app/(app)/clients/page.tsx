"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ClientCard } from "@/components/clients/ClientCard";
import { ClientSearch } from "@/components/clients/ClientSearch";
import { apiClient } from "@/lib/api";
import type { Client, IndustryType } from "@/types";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchClients = useCallback(
    async (search = "", industry: IndustryType | "" = "") => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (search) params.set("search", search);
        if (industry) params.set("industry", industry);
        const qs = params.toString() ? `?${params.toString()}` : "";
        const data = await apiClient<Client[]>(`/api/clients/${qs}`);
        setClients(data);
      } catch {
        setClients([]);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Clients</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Manage client accounts and CMA reports
          </p>
        </div>
        <Link href="/clients/new">
          <Button>
            <Plus className="mr-1.5 h-4 w-4" />
            New Client
          </Button>
        </Link>
      </div>

      {/* Search + filter */}
      <ClientSearch onSearch={fetchClients} />

      {/* Client grid */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-36 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : clients.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Users className="mb-3 h-12 w-12 text-muted-foreground/30" />
          <p className="font-medium text-muted-foreground">No clients found</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Create your first client to start generating CMA reports
          </p>
          <Link href="/clients/new" className="mt-5">
            <Button size="sm">
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              New Client
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {clients.map((client) => (
            <ClientCard key={client.id} client={client} />
          ))}
        </div>
      )}
    </div>
  );
}
