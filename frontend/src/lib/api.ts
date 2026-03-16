import { createClient } from "@/lib/supabase/client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DISABLE_AUTH = process.env.NEXT_PUBLIC_DISABLE_AUTH === "true";

export async function apiClient<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (DISABLE_AUTH) {
    // Dev bypass: send a sentinel token; backend ignores it when DISABLE_AUTH=true
    (headers as Record<string, string>)["Authorization"] = "Bearer dev-bypass";
  } else {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (session?.access_token) {
      (headers as Record<string, string>)["Authorization"] =
        `Bearer ${session.access_token}`;
    }
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  // 204 No Content (e.g. DELETE) — no body to parse
  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

