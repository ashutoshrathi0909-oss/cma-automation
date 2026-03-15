import Link from "next/link";
import { Calendar, IndianRupee, Building2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Client } from "@/types";

const INDUSTRY_STYLES: Record<string, string> = {
  manufacturing: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  service: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  trading: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  other: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

interface ClientCardProps {
  client: Client;
}

export function ClientCard({ client }: ClientCardProps) {
  const industryStyle = INDUSTRY_STYLES[client.industry_type] ?? INDUSTRY_STYLES.other;

  return (
    <Link href={`/clients/${client.id}`}>
      <Card className="cursor-pointer hover:ring-primary/50 hover:shadow-sm transition-all h-full">
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10">
                <Building2 className="h-4 w-4 text-primary" />
              </div>
              <CardTitle className="truncate text-sm">{client.name}</CardTitle>
            </div>
            <span
              className={`shrink-0 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${industryStyle}`}
            >
              {client.industry_type}
            </span>
          </div>
        </CardHeader>

        <CardContent>
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5 shrink-0" />
              FY ends {client.financial_year_ending}
            </span>
            <span className="flex items-center gap-1">
              <IndianRupee className="h-3.5 w-3.5 shrink-0" />
              {client.currency}
            </span>
          </div>
          {client.notes && (
            <p className="mt-2 text-xs text-muted-foreground line-clamp-2">
              {client.notes}
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
