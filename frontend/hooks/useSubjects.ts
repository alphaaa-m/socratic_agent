"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createSubject, deleteSubject, getSubject, listSubjects, updateSubject } from "@/services/subjects";
import type { SubjectCreateRequest, SubjectUpdateRequest } from "@/types/api";

const subjectKey = (activeOnly: boolean) => ["subjects", { activeOnly }] as const;

export function useSubjects(activeOnly = true) {
  return useQuery({ queryKey: subjectKey(activeOnly), queryFn: () => listSubjects(activeOnly) });
}

export function useSubject(subjectId: string) {
  return useQuery({ queryKey: ["subjects", subjectId], queryFn: () => getSubject(subjectId), enabled: Boolean(subjectId) });
}

function useInvalidateSubjects() {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: ["subjects"] });
}

export function useCreateSubject() {
  const invalidate = useInvalidateSubjects();
  return useMutation({ mutationFn: (body: SubjectCreateRequest) => createSubject(body), onSuccess: invalidate });
}

export function useUpdateSubject() {
  const invalidate = useInvalidateSubjects();
  return useMutation({
    mutationFn: ({ subjectId, body }: { subjectId: string; body: SubjectUpdateRequest }) =>
      updateSubject(subjectId, body),
    onSuccess: invalidate,
  });
}

export function useDeleteSubject() {
  const invalidate = useInvalidateSubjects();
  return useMutation({ mutationFn: deleteSubject, onSuccess: invalidate });
}
