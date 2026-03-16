"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import type { RolloverConfirmResponse, RolloverItem, RolloverPreviewResponse } from "@/types";

interface RolloverWizardProps {
  clientId: string;
  suggestedFromYear?: number;
}

type Step = "select" | "preview" | "confirm" | "done";

export function RolloverWizard({ clientId, suggestedFromYear }: RolloverWizardProps) {
  const router = useRouter();
  const currentYear = new Date().getFullYear();

  const [step, setStep] = useState<Step>("select");
  const [fromYear, setFromYear] = useState<number>(
    suggestedFromYear ?? currentYear - 1
  );
  const [toYear, setToYear] = useState<number>(
    suggestedFromYear ? suggestedFromYear + 1 : currentYear
  );
  const [preview, setPreview] = useState<RolloverPreviewResponse | null>(null);
  const [result, setResult] = useState<RolloverConfirmResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handlePreview() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient<RolloverPreviewResponse>("/api/rollover/preview", {
        method: "POST",
        body: JSON.stringify({ client_id: clientId, from_year: fromYear, to_year: toYear }),
      });
      setPreview(data);
      setStep("preview");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient<RolloverConfirmResponse>("/api/rollover/confirm", {
        method: "POST",
        body: JSON.stringify({ client_id: clientId, from_year: fromYear, to_year: toYear }),
      });
      setResult(data);
      setStep("done");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Rollover failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        {(["select", "preview", "confirm", "done"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            {i > 0 && <ArrowRight className="h-3 w-3" />}
            <span className={step === s ? "font-medium text-gray-900" : ""}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </span>
          </div>
        ))}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Step 1: Select years */}
      {step === "select" && (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Select the financial years to roll over. Balance sheet closing balances
            from <strong>FY {fromYear}</strong> will become opening balances for{" "}
            <strong>FY {toYear}</strong>.
          </p>
          <div className="flex gap-4 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                From Year
              </label>
              <input
                type="number"
                value={fromYear}
                onChange={(e) => {
                  const v = Number(e.target.value);
                  setFromYear(v);
                  setToYear(v + 1);
                }}
                className="w-28 rounded border border-gray-300 px-3 py-1.5 text-sm"
              />
            </div>
            <ArrowRight className="h-4 w-4 text-gray-400 mb-2" />
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                To Year
              </label>
              <input
                type="number"
                value={toYear}
                onChange={(e) => setToYear(Number(e.target.value))}
                className="w-28 rounded border border-gray-300 px-3 py-1.5 text-sm"
              />
            </div>
          </div>
          <Button onClick={handlePreview} disabled={loading || toYear <= fromYear}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Preview Rollover
          </Button>
        </div>
      )}

      {/* Step 2: Preview items */}
      {step === "preview" && preview && (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            The following{" "}
            <strong>{preview.items_to_carry_forward.length} balance sheet items</strong>{" "}
            will be carried forward from FY {fromYear} to FY {toYear}:
          </p>

          {preview.items_to_carry_forward.length === 0 ? (
            <div className="rounded-lg border bg-yellow-50 p-4 text-sm text-yellow-700">
              No classified balance sheet items found for FY {fromYear}. Run
              classification first before rolling over.
            </div>
          ) : (
            <div className="max-h-64 overflow-y-auto rounded-lg border border-gray-200">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Description
                    </th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                      Amount
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {preview.items_to_carry_forward.map((item: RolloverItem, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-gray-900">{item.description}</td>
                      <td className="px-3 py-2 text-right text-gray-700">
                        {item.amount != null
                          ? new Intl.NumberFormat("en-IN").format(item.amount)
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setStep("select")}>
              Back
            </Button>
            <Button
              onClick={() => setStep("confirm")}
              disabled={preview.items_to_carry_forward.length === 0}
            >
              Proceed to Confirm
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Confirm */}
      {step === "confirm" && preview && (
        <div className="space-y-4">
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            <strong>This action cannot be undone.</strong> It will create a new
            provisional document for FY {toYear} with{" "}
            {preview.items_to_carry_forward.length} pre-populated opening
            balance items. You will still need to upload, extract, and classify
            the remaining P&amp;L documents for FY {toYear}.
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setStep("preview")}>
              Back
            </Button>
            <Button onClick={handleConfirm} disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Confirm Rollover
            </Button>
          </div>
        </div>
      )}

      {/* Step 4: Done */}
      {step === "done" && result && (
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 shrink-0" />
            <div className="text-sm text-green-800">
              <p className="font-medium">Rollover complete!</p>
              <p>
                Created {result.document_ids.length} document(s) for FY {toYear}{" "}
                with {result.items_created} carried-forward line items.
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={() => router.push(`/clients/${clientId}`)}
          >
            Go to Client
          </Button>
        </div>
      )}
    </div>
  );
}
