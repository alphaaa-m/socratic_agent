"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { api } from "@/services/http";

type CurrentUser = { id: string; name: string; email: string; role: "student" | "admin" };

export function UserMenu() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: user, isLoading } = useQuery({
    queryKey: ["user", "me"],
    queryFn: () => api<CurrentUser>("users/me"),
    staleTime: 60_000,
    retry: false,
  });

  async function logout() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      queryClient.clear();
      router.replace("/login");
      router.refresh();
    }
  }

  return (
    <details className="user-menu">
      <summary aria-label="Open account menu">
        <span className="user-avatar" aria-hidden="true">
          {user?.name?.trim().charAt(0).toUpperCase() ?? "•"}
        </span>
        <span>{isLoading ? "Loading account…" : user?.name ?? "Account"}</span>
      </summary>
      <div className="user-menu-panel">
        <p className="muted">{user?.email ?? "Your account"}</p>
        <button type="button" onClick={logout}>Sign out</button>
      </div>
    </details>
  );
}
