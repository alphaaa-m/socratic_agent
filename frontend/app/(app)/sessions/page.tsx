"use client";

import { useState } from "react";

import { SessionFilters } from "@/components/history/SessionFilters";
import { SessionTable } from "@/components/history/SessionTable";
import { useSessions } from "@/hooks/useSessions";
import { useSubjects } from "@/hooks/useSubjects";
import type { SessionStatus } from "@/types/api";

const PAGE_SIZE = 10;

export default function SessionsPage() {
  const [subjectId, setSubjectId] = useState("");
  const [status, setStatus] = useState<"" | SessionStatus>("");
  const [offset, setOffset] = useState(0);
  const sessions = useSessions({ subjectId: subjectId || undefined, status: status || undefined, limit: PAGE_SIZE, offset });
  const subjects = useSubjects(false);
  const changeSubject = (value: string) => { setSubjectId(value); setOffset(0); };
  const changeStatus = (value: "" | SessionStatus) => { setStatus(value); setOffset(0); };
  const total = sessions.data?.total ?? 0;

  return (
    <section className="page-section">
      <p className="eyebrow">Learning history</p>
      <h1>Your sessions</h1>
      <SessionFilters subjects={subjects.data ?? []} subjectId={subjectId} status={status} onSubjectChange={changeSubject} onStatusChange={changeStatus} />
      {sessions.isLoading && <p className="muted">Loading sessions…</p>}
      {sessions.error && <p className="form-error" role="alert">{sessions.error.message}</p>}
      {sessions.data && <SessionTable sessions={sessions.data.items} subjects={subjects.data ?? []} />}
      {total > PAGE_SIZE && (
        <nav className="pagination" aria-label="Session pages">
          <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Previous</button>
          <span>{Math.floor(offset / PAGE_SIZE) + 1} of {Math.ceil(total / PAGE_SIZE)}</span>
          <button type="button" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>Next</button>
        </nav>
      )}
    </section>
  );
}
