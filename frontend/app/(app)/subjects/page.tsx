"use client";

import { useRouter } from "next/navigation";

import { SubjectGrid } from "@/components/subjects/SubjectGrid";
import { useCreateSession } from "@/hooks/useSessions";
import { useSubjects } from "@/hooks/useSubjects";
import type { Subject } from "@/types/api";

export default function SubjectsPage() {
  const router = useRouter();
  const { data: subjects = [], isLoading, error } = useSubjects();
  const startSession = useCreateSession();

  function start(subject: Subject) {
    startSession.mutate(subject.id, { onSuccess: (session) => router.push(`/sessions/${session.id}`) });
  }

  return (
    <section className="page-section">
      <p className="eyebrow">Choose a subject</p>
      <h1>What would you like to explore?</h1>
      <p className="muted">Start a session and your Socratic tutor will guide the conversation.</p>
      {startSession.error && <p className="form-error" role="alert">{startSession.error.message}</p>}
      {isLoading ? <div className="subject-grid skeleton-grid" aria-label="Loading subjects"><div /><div /><div /></div> : null}
      {error ? <p className="form-error" role="alert">{error.message}</p> : null}
      {!isLoading && !error && <SubjectGrid subjects={subjects} onStart={start} isStarting={startSession.isPending} />}
    </section>
  );
}
