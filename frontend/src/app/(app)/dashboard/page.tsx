"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2,
  FileText,
  Plus,
  ArrowRight,
  Users,
  BarChart3,
} from "lucide-react";
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
import type { Client } from "@/types";

const INDUSTRY_COLORS: Record<string, string> = {
  manufacturing: "bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400",
  service: "bg-green-50 dark:bg-green-950/30 text-green-600 dark:text-green-400",
  trading: "bg-orange-50 dark:bg-orange-950/30 text-orange-600 dark:text-orange-400",
  other: "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400",
};

export default function DashboardPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient<Client[]>("/api/clients/")
      .then(setClients)
      .catch(() => toast.error("Could not load dashboard data"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-7 w-48 animate-pulse rounded bg-muted" />
          <div className="mt-1 h-4 w-64 animate-pulse rounded bg-muted" />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
        <div className="h-64 animate-pulse rounded-xl bg-muted" />
      </div>
    );
  }

  // Industry breakdown
  const industryCounts = clients.reduce<Record<string, number>>((acc, c) => {
    acc[c.industry_type] = (acc[c.industry_type] ?? 0) + 1;
    return acc;
  }, {});

  const statCards = [
    {
      label: "Total Clients",
      value: clients.length,
      icon: Users,
      color: "text-blue-500",
      bg: "bg-blue-50 dark:bg-blue-950/30",
      href: "/clients",
    },
    {
      label: "Manufacturing",
      value: industryCounts["manufacturing"] ?? 0,
      icon: BarChart3,
      color: "text-purple-500",
      bg: "bg-purple-50 dark:bg-purple-950/30",
      href: "/clients?industry=manufacturing",
    },
    {
      label: "Service / Trading",
      value: (industryCounts["service"] ?? 0) + (industryCounts["trading"] ?? 0),
      icon: FileText,
      color: "text-green-500",
      bg: "bg-green-50 dark:bg-green-950/30",
      href: "/clients?industry=service",
    },
  ];

  const recentClients = clients.slice(0, 8);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Overview of your CMA automation workspace
          </p>
        </div>
        <Link href="/clients/new">
          <Button>
            <Plus className="mr-1.5 h-4 w-4" />
            New Client
          </Button>
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {statCards.map(({ label, value, icon: Icon, color, bg, href }) => (
          <Link key={label} href={href}>
            <Card className="cursor-pointer transition-colors hover:bg-muted/30">
              <CardContent className="flex items-center gap-4 p-5">
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${bg}`}
                >
                  <Icon className={`h-5 w-5 ${color}`} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{value}</p>
                  <p className="text-xs text-muted-foreground">{label}</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Recent clients */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="text-base">Clients</CardTitle>
            <CardDescription>
              {clients.length === 0
                ? "No clients yet"
                : `${clients.length} client${clients.length !== 1 ? "s" : ""} total`}
            </CardDescription>
          </div>
          <Link href="/clients">
            <Button variant="ghost" size="sm" className="gap-1 text-xs">
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {clients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <Building2 className="mb-3 h-10 w-10 text-muted-foreground/30" />
              <p className="font-medium text-muted-foreground">No clients yet</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Add your first client to start generating CMA reports
              </p>
              <Link href="/clients/new" className="mt-4">
                <Button size="sm">
                  <Plus className="mr-1.5 h-3.5 w-3.5" />
                  Add Client
                </Button>
              </Link>
            </div>
          ) : (
            <div className="divide-y">
              {recentClients.map((client) => {
                const colorClass =
                  INDUSTRY_COLORS[client.industry_type] ?? INDUSTRY_COLORS.other;
                return (
                  <Link key={client.id} href={`/clients/${client.id}`}>
                    <div className="flex items-center gap-3 py-2.5 transition-colors hover:bg-muted/30 rounded-lg px-2 -mx-2">
                      <div
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${colorClass}`}
                      >
                        <Building2 className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">
                          {client.name}
                        </p>
                        <p className="text-xs capitalize text-muted-foreground">
                          {client.industry_type} · FY ending{" "}
                          {client.financial_year_ending}
                        </p>
                      </div>
                      <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground/40" />
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
