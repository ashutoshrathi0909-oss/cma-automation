"use client";

import { CheckCircle2, Edit3, ThumbsUp } from "lucide-react";
import type { AuditEntry } from "@/types";

interface AuditTrailProps {
  entries: AuditEntry[];
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function actionIcon(action: string) {
  if (action.includes("approve")) return <ThumbsUp className="h-4 w-4 text-green-600" />;
  if (action.includes("correct")) return <Edit3 className="h-4 w-4 text-blue-600" />;
  return <CheckCircle2 className="h-4 w-4 text-muted-foreground" />;
}

function actionLabel(action: string): string {
  return action
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function AuditTrail({ entries }: AuditTrailProps) {
  if (entries.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        No actions recorded yet.
      </p>
    );
  }

  return (
    <ol className="relative border-l border-border pl-4 space-y-4">
      {entries.map((entry) => (
        <li key={entry.id} className="relative">
          {/* Icon on the timeline line */}
          <span className="absolute -left-[21px] flex h-8 w-8 items-center justify-center rounded-full border bg-background">
            {actionIcon(entry.action)}
          </span>

          <div className="ml-4 rounded-lg border bg-card p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium">{actionLabel(entry.action)}</p>
              <time className="shrink-0 text-xs text-muted-foreground">
                {formatTime(entry.performed_at)}
              </time>
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">
              by {entry.performed_by}
            </p>
            {entry.action_details && (() => {
              const before = entry.action_details.before as Record<string, unknown> | null | undefined;
              const after = entry.action_details.after as Record<string, unknown> | null | undefined;
              if (!before && !after) return null;
              return (
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                  {before ? (
                    <div className="rounded bg-red-50 p-1.5 dark:bg-red-950/20">
                      <p className="font-medium text-red-700 dark:text-red-400">Before</p>
                      <p className="mt-0.5 text-muted-foreground">
                        {String(before.cma_field_name ?? "—")}
                      </p>
                    </div>
                  ) : <div />}
                  {after ? (
                    <div className="rounded bg-green-50 p-1.5 dark:bg-green-950/20">
                      <p className="font-medium text-green-700 dark:text-green-400">After</p>
                      <p className="mt-0.5 text-muted-foreground">
                        {String(after.cma_field_name ?? "—")}
                      </p>
                    </div>
                  ) : <div />}
                </div>
              );
            })()}
          </div>
        </li>
      ))}
    </ol>
  );
}
