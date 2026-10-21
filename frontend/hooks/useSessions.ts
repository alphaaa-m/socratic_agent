"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createSession, getSession, listSessions, type SessionFilters } from "@/services/sessions";

export function useSessions(filters: SessionFilters = {}) {
  const { subjectId, status, limit = 20, offset = 0 } = filters;
  return useQuery({
    queryKey: ["sessions", { subjectId, status, limit, offset }],
    queryFn: () => listSessions({ subjectId, status, limit, offset }),
  });
}

export function useSession(sessionId: string) {
  return useQuery({
    queryKey: ["sessions", sessionId],
    queryFn: () => getSession(sessionId),
    enabled: Boolean(sessionId),
  });
}

export function useCreateSession() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: createSession,
    onSuccess: () => client.invalidateQueries({ queryKey: ["sessions"] }),
  });
}
