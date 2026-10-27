"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getCurrentUser, getLearnerProfile, listUsers, type UserFilters, updateUser } from "@/services/users";
import type { AdminUserUpdateRequest } from "@/types/api";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["users", "me"],
    queryFn: getCurrentUser,
    staleTime: 60_000,
    retry: false,
  });
}

export function useLearnerProfile() {
  return useQuery({
    queryKey: ["users", "me", "profile"],
    queryFn: getLearnerProfile,
    staleTime: 60_000,
    retry: false,
  });
}

export function useUsers(filters: UserFilters = {}) {
  const { role, q, limit = 20, offset = 0 } = filters;
  return useQuery({
    queryKey: ["users", { role, q, limit, offset }],
    queryFn: () => listUsers({ role, q, limit, offset }),
  });
}

export function useUpdateUser() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, body }: { userId: string; body: AdminUserUpdateRequest }) =>
      updateUser(userId, body),
    onSuccess: () => client.invalidateQueries({ queryKey: ["users"] }),
  });
}
