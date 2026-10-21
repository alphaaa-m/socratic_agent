"use client";

import { useRouter } from "next/navigation";

import type { LearningSession, Subject } from "@/types/api";

type SessionTableProps = { sessions: LearningSession[]; subjects: Subject[] };

export function SessionTable({ sessions, subjects }: SessionTableProps) {
  const router = useRouter();
  const names = new Map(subjects.map((subject) => [subject.id, subject.name]));
  if (!sessions.length) return <p className="empty-state">No learning sessions match these filters.</p>;

  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Session</th><th>Subject</th><th>Status</th><th>Started</th></tr></thead>
        <tbody>
          {sessions.map((session) => (
            <tr
              key={session.id}
              className="selectable-row"
              role="link"
              tabIndex={0}
              aria-label={`Open ${session.title || "new session"}`}
              onClick={() => router.push(`/sessions/${session.id}`)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  router.push(`/sessions/${session.id}`);
                }
              }}
            >
              <td>{session.title || "New session"}</td>
              <td>{names.get(session.subject_id) ?? "Unavailable subject"}</td>
              <td><span className={`status-badge ${session.status}`}>{session.status}</span></td>
              <td>{new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(session.started_at))}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
