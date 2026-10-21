import { api } from "@/services/http";
import type { Subject, SubjectCreateRequest, SubjectUpdateRequest } from "@/types/api";

export function listSubjects(activeOnly = true) {
  const query = activeOnly ? "" : "?active_only=false";
  return api<Subject[]>(`subjects${query}`);
}

export function getSubject(subjectId: string) {
  return api<Subject>(`subjects/${subjectId}`);
}

export function createSubject(body: SubjectCreateRequest) {
  return api<Subject>("subjects", { method: "POST", body: JSON.stringify(body) });
}

export function updateSubject(subjectId: string, body: SubjectUpdateRequest) {
  return api<Subject>(`subjects/${subjectId}`, { method: "PATCH", body: JSON.stringify(body) });
}

export function deleteSubject(subjectId: string) {
  return api<void>(`subjects/${subjectId}`, { method: "DELETE" });
}
