import { api } from "@/services/http";
import type { LearningSession, Page, SessionDetail, SessionStatus } from "@/types/api";

export type SessionFilters = {
  subjectId?: string;
  status?: SessionStatus;
  limit?: number;
  offset?: number;
};

export function createSession(subjectId: string) {
  return api<LearningSession>("sessions", {
    method: "POST",
    body: JSON.stringify({ subject_id: subjectId }),
  });
}

export function listSessions(filters: SessionFilters = {}) {
  const query = new URLSearchParams();
  if (filters.subjectId) query.set("subject_id", filters.subjectId);
  if (filters.status) query.set("status", filters.status);
  if (filters.limit) query.set("limit", String(filters.limit));
  if (filters.offset) query.set("offset", String(filters.offset));
  const suffix = query.size ? `?${query}` : "";
  return api<Page<LearningSession>>(`sessions${suffix}`);
}

export function getSession(sessionId: string) {
  return api<SessionDetail>(`sessions/${sessionId}`);
}
