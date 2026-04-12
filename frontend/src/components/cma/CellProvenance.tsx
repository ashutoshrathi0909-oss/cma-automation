"use client";

import { useEffect, useState } from "react";
import { Info, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";

interface ProvenanceRecord {
  id: string;
  cma_row: number;
  cma_column: string;
  financial_year: number | null;
  source_text: string | null;
  raw_amount: number | null;
  converted_amount: number | null;
  document_id: string | null;
}

interface CellProvenanceProps {
  reportId: string;
  cmaRow: number;
  cmaColumn: string;
}

export function CellProvenance({ reportId, cmaRow, cmaColumn }: CellProvenanceProps) {
  const [open, setOpen] = useState(false);
  const [records, setRecords] = useState<ProvenanceRecord[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    apiClient<ProvenanceRecord[]>(
      `/api/cma-reports/${reportId}/provenance?row=${cmaRow}&column=${cmaColumn}`
    )
      .then(setRecords)
      .catch(() => setRecords([]))
      .finally(() => setLoading(false));
  }, [open, reportId, cmaRow, cmaColumn]);

  const formatAmount = (amt: number | null) =>
    amt != null ? amt.toLocaleString("en-IN", { maximumFractionDigits: 2 }) : "-";

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" className="h-6 w-6">
          <Info className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            Cell Provenance — Row {cmaRow}, Column {cmaColumn}
          </DialogTitle>
        </DialogHeader>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : records.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            No source items found for this cell.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Source Text</TableHead>
                <TableHead className="text-right">Raw Amount</TableHead>
                <TableHead className="text-right">Converted</TableHead>
                <TableHead>Year</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="max-w-[200px] truncate">
                    {r.source_text || "-"}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatAmount(r.raw_amount)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatAmount(r.converted_amount)}
                  </TableCell>
                  <TableCell>{r.financial_year || "-"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </DialogContent>
    </Dialog>
  );
}
