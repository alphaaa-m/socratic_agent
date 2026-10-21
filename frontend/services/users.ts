import { api } from "@/services/http";
import type { AdminUserUpdateRequest, Page, User } from "@/types/api";

export type UserFilters = { role?: User["role"]; q?: string; limit?: number; offset?: number };

export function getCurrentUser() {
  return api<User>("users/me");
}

export function listUsers(filters: UserFilters = {}) {
  const query = new URLSearchParams();
  if (filters.role) query.set("role", filters.role);
  if (filters.q?.trim()) query.set("q", filters.q.trim());
  if (filters.limit) query.set("limit", String(filters.limit));
  if (filters.offset) query.set("offset", String(filters.offset));
  const suffix = query.size ? `?${query}` : "";
  return api<Page<User>>(`users${suffix}`);
}

export function updateUser(userId: string, body: AdminUserUpdateRequest) {
  return api<User>(`users/${userId}`, { method: "PATCH", body: JSON.stringify(body) });
}
