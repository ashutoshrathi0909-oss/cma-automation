"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, ShieldOff, UserCog } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import type { UserProfileFull } from "@/types";

export default function SettingsPage() {
  const router = useRouter();
  const [users, setUsers] = useState<UserProfileFull[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      setCurrentUserId(session?.user?.id ?? null);
    });

    apiClient<UserProfileFull[]>("/api/users")
      .then((data) => setUsers(data))
      .catch((err) => {
        if (err?.status === 403) {
          router.replace("/dashboard");
        } else {
          setError("Failed to load users");
        }
      })
      .finally(() => setLoading(false));
  }, [router]);

  async function handleRoleChange(userId: string, newRole: "admin" | "employee") {
    setUpdatingId(userId);
    setError(null);
    try {
      const updated = await apiClient<UserProfileFull>(`/api/users/${userId}`, {
        method: "PUT",
        body: JSON.stringify({ role: newRole }),
      });
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleDeactivate(userId: string) {
    if (!confirm("Deactivate this user? They will no longer be able to log in.")) return;
    setUpdatingId(userId);
    setError(null);
    try {
      const updated = await apiClient<UserProfileFull>(`/api/users/${userId}/deactivate`, {
        method: "PUT",
      });
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Deactivation failed");
    } finally {
      setUpdatingId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500">Manage firm user accounts.</p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <UserCog className="h-4 w-4" />
            User Management
          </CardTitle>
          <CardDescription>
            Admins can change roles and deactivate accounts. You cannot change
            your own role or deactivate your own account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-gray-100">
            {users.map((user) => {
              const isSelf = user.id === currentUserId;
              const isUpdating = updatingId === user.id;

              return (
                <div
                  key={user.id}
                  className={`flex items-center justify-between py-3 ${
                    !user.is_active ? "opacity-50" : ""
                  }`}
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {user.full_name}
                      {isSelf && (
                        <span className="ml-2 text-xs text-gray-400">(you)</span>
                      )}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge
                        variant={user.role === "admin" ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {user.role}
                      </Badge>
                      {!user.is_active && (
                        <Badge variant="destructive" className="text-xs">
                          Inactive
                        </Badge>
                      )}
                    </div>
                  </div>

                  {!isSelf && user.is_active && (
                    <div className="flex items-center gap-2">
                      <select
                        value={user.role}
                        onChange={(e) =>
                          handleRoleChange(
                            user.id,
                            e.target.value as "admin" | "employee"
                          )
                        }
                        disabled={isUpdating}
                        className="text-xs rounded border border-gray-300 px-2 py-1"
                      >
                        <option value="employee">Employee</option>
                        <option value="admin">Admin</option>
                      </select>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeactivate(user.id)}
                        disabled={isUpdating}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        {isUpdating ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <ShieldOff className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              );
            })}

            {users.length === 0 && (
              <p className="py-4 text-sm text-gray-500 text-center">
                No users found.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
