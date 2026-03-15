"use client";

import { useState, useCallback } from "react";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { IndustryType } from "@/types";

interface ClientSearchProps {
  onSearch: (search: string, industry: IndustryType | "") => void;
}

export function ClientSearch({ onSearch }: ClientSearchProps) {
  const [search, setSearch] = useState("");
  const [industry, setIndustry] = useState<IndustryType | "">("");

  const emit = useCallback(
    (s: string, ind: IndustryType | "") => onSearch(s, ind),
    [onSearch]
  );

  return (
    <div className="flex flex-wrap gap-3">
      {/* Name search */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          placeholder="Search clients…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            emit(e.target.value, industry);
          }}
          className="pl-8 pr-8"
        />
        {search && (
          <button
            onClick={() => {
              setSearch("");
              emit("", industry);
            }}
            className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Industry filter */}
      <Select
        value={industry}
        onChange={(e) => {
          const val = e.target.value as IndustryType | "";
          setIndustry(val);
          emit(search, val);
        }}
        className="w-44"
        aria-label="Filter by industry"
      >
        <option value="">All industries</option>
        <option value="manufacturing">Manufacturing</option>
        <option value="service">Service</option>
        <option value="trading">Trading</option>
        <option value="other">Other</option>
      </Select>
    </div>
  );
}
