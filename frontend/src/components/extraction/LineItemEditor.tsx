"use client";

import { useState, useRef, useEffect } from "react";
import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api";
import type { LineItemResponse } from "@/types";

interface LineItemEditorProps {
  item: LineItemResponse;
  onSaved: (updated: LineItemResponse) => void;
}

function formatIndian(value: number | null): string {
  if (value === null) return "—";
  return value.toLocaleString("en-IN");
}

export function LineItemEditor({ item, onSaved }: LineItemEditorProps) {
  const [editing, setEditing] = useState(false);
  const [inputValue, setInputValue] = useState(item.amount?.toString() ?? "");
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  function handleStartEdit() {
    setInputValue(item.amount?.toString() ?? "");
    setEditing(true);
  }

  function handleCancel() {
    setEditing(false);
    setInputValue(item.amount?.toString() ?? "");
  }

  async function handleSave() {
    const parsed = inputValue.trim() === "" ? null : Number(inputValue.trim());
    if (inputValue.trim() !== "" && isNaN(parsed as number)) return;

    setSaving(true);
    try {
      const updated = await apiClient<LineItemResponse>(
        `/api/documents/${item.document_id}/items/${item.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({ amount: parsed }),
        }
      );
      onSaved(updated);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      void handleSave();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  }

  if (editing) {
    return (
      <div className="flex items-center gap-1">
        <Input
          ref={inputRef}
          type="number"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          className="h-7 w-32 text-right text-sm"
          disabled={saving}
          placeholder="Amount"
        />
        <Button
          size="icon-sm"
          variant="ghost"
          onClick={() => void handleSave()}
          disabled={saving}
          title="Save"
        >
          <Check className="h-3.5 w-3.5 text-green-600" />
        </Button>
        <Button
          size="icon-sm"
          variant="ghost"
          onClick={handleCancel}
          disabled={saving}
          title="Cancel"
        >
          <X className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </div>
    );
  }

  return (
    <button
      onClick={handleStartEdit}
      className="rounded px-1 py-0.5 text-right text-sm tabular-nums hover:bg-muted transition-colors"
      title="Click to edit"
    >
      {formatIndian(item.amount)}
    </button>
  );
}
