import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import type { UserProfile } from "@/types";

/**
 * Authenticated app layout — wraps all routes except /login.
 * Server-side session check: unauthenticated users are redirected to /login.
 */
export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  // Use getUser() — validates JWT signature + expiry against Supabase server.
  // getSession() only reads the cookie without cryptographic validation.
  const {
    data: { user: authUser },
  } = await supabase.auth.getUser();

  if (!authUser) {
    redirect("/login");
  }

  // Fetch user profile for the Header
  const { data: profileData } = await supabase
    .from("user_profiles")
    .select("*")
    .eq("id", authUser.id)
    .single();

  const userProfile: UserProfile | null = profileData ?? null;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header user={userProfile} />
        <main className="flex-1 overflow-y-auto bg-muted/20 p-6">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
