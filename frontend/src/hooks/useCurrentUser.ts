"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { UserProfile } from "@/types";

/**
 * Returns the currently authenticated user's profile.
 * Calls /api/auth/me on mount; handles auth errors gracefully.
 */
export function useCurrentUser() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient<UserProfile>("/api/auth/me")
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  return { user, loading };
}
