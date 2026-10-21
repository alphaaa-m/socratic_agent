"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/hooks/useUsers";

export function UserMenu() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: user, isLoading } = useCurrentUser();

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
