"use client";

import Link from "next/link";

import { SessionTable } from "@/components/history/SessionTable";
import { useSessions } from "@/hooks/useSessions";
import { useSubjects } from "@/hooks/useSubjects";
import { useCurrentUser } from "@/hooks/useUsers";

export default function DashboardPage() {
  const { data: user } = useCurrentUser();
  const sessions = useSessions({ limit: 5 });
  const subjects = useSubjects(false);
  return (
    <section className="page-section">
      <p className="eyebrow">Dashboard</p>
      <h1>{user ? `Welcome back, ${user.name}.` : "Welcome back."}</h1>
      <p className="muted">Continue a recent session or choose a new topic.</p>
      <Link className="primary-button inline-button" href="/subjects">Start new session</Link>
      <div className="dashboard-grid">
        <section className="panel">
          <h2>Recent sessions</h2>
          {sessions.isLoading && <p className="muted">Loading sessions…</p>}
          {sessions.error && <p className="form-error" role="alert">{sessions.error.message}</p>}
          {sessions.data && <SessionTable sessions={sessions.data.items} subjects={subjects.data ?? []} />}
        </section>
        <aside className="panel placeholder-card">
          <h2>Level and mastery</h2>
          <p className="muted">Your level and mastery progress will appear here after the Phase 6 progress features are available.</p>
        </aside>
      </div>
    </section>
  );
}
