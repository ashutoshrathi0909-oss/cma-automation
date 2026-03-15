"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api";
import type { Client } from "@/types";

interface ClientFormProps {
  initialData?: Client;
  onSuccess?: (client: Client) => void;
}

export function ClientForm({ initialData, onSuccess }: ClientFormProps) {
  const router = useRouter();
  const isEdit = !!initialData;

  const [form, setForm] = useState({
    name: initialData?.name ?? "",
    industry_type: initialData?.industry_type ?? "manufacturing",
    financial_year_ending: initialData?.financial_year_ending ?? "31st March",
    currency: initialData?.currency ?? "INR",
    notes: initialData?.notes ?? "",
  });
  const [loading, setLoading] = useState(false);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = { ...form, notes: form.notes || null };
      let result: Client;

      if (isEdit) {
        result = await apiClient<Client>(`/api/clients/${initialData.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        toast.success("Client updated successfully");
      } else {
        result = await apiClient<Client>("/api/clients/", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        toast.success("Client created successfully");
      }

      if (onSuccess) {
        onSuccess(result);
      } else {
        router.push(`/clients/${result.id}`);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 max-w-xl">
      {/* Client Name */}
      <div className="space-y-1.5">
        <Label htmlFor="name">
          Client Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          required
          placeholder="e.g. ABC Manufacturing Ltd"
          value={form.name}
          onChange={(e) => update("name", e.target.value)}
        />
      </div>

      {/* Industry Type */}
      <div className="space-y-1.5">
        <Label htmlFor="industry_type">
          Industry Type <span className="text-destructive">*</span>
        </Label>
        <Select
          id="industry_type"
          value={form.industry_type}
          onChange={(e) => update("industry_type", e.target.value as Client["industry_type"])}
        >
          <option value="manufacturing">Manufacturing</option>
          <option value="service">Service</option>
          <option value="trading">Trading</option>
          <option value="other">Other</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          Industry type determines classification defaults in the CMA pipeline.
        </p>
      </div>

      {/* Financial Year Ending */}
      <div className="space-y-1.5">
        <Label htmlFor="financial_year_ending">Financial Year Ending</Label>
        <Input
          id="financial_year_ending"
          value={form.financial_year_ending}
          onChange={(e) => update("financial_year_ending", e.target.value)}
          placeholder="31st March"
        />
      </div>

      {/* Currency */}
      <div className="space-y-1.5">
        <Label htmlFor="currency">Currency</Label>
        <Input
          id="currency"
          value={form.currency}
          onChange={(e) => update("currency", e.target.value)}
          placeholder="INR"
        />
      </div>

      {/* Notes */}
      <div className="space-y-1.5">
        <Label htmlFor="notes">Notes</Label>
        <Textarea
          id="notes"
          value={form.notes}
          onChange={(e) => update("notes", e.target.value)}
          placeholder="Any additional notes about this client…"
          rows={3}
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        <Button type="submit" disabled={loading}>
          {loading ? "Saving…" : isEdit ? "Update Client" : "Create Client"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
          disabled={loading}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}
