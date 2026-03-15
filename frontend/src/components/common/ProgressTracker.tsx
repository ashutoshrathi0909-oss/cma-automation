"use client";

import { useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import type { TaskStatusResponse } from "@/types";

interface ProgressTrackerProps {
  taskId: string;
  onComplete: () => void;
  onFailed: (error: string) => void;
}

export function ProgressTracker({ taskId, onComplete, onFailed }: ProgressTrackerProps) {
  const onCompleteRef = useRef(onComplete);
  const onFailedRef = useRef(onFailed);

  useEffect(() => {
    onCompleteRef.current = onComplete;
    onFailedRef.current = onFailed;
  });

  useEffect(() => {
    let cancelled = false;

    const intervalId = setInterval(async () => {
      try {
        const status = await apiClient<TaskStatusResponse>(`/api/tasks/${taskId}`);

        if (cancelled) return;

        if (status.status === "complete") {
          clearInterval(intervalId);
          onCompleteRef.current();
        } else if (status.status === "failed" || status.status === "not_found") {
          clearInterval(intervalId);
          onFailedRef.current("Extraction failed");
        }
      } catch {
        if (!cancelled) {
          clearInterval(intervalId);
          onFailedRef.current("Extraction failed");
        }
      }
    }, 2000);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [taskId]);

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="text-sm font-medium text-muted-foreground">Extracting document...</p>
      <p className="text-xs text-muted-foreground">
        This may take a minute. Do not close this page.
      </p>
    </div>
  );
}
