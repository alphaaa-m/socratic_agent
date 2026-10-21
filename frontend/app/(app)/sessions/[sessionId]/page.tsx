"use client";

import Link from "next/link";

import { useSession } from "@/hooks/useSessions";

export default function ChatPage({ params }: { params: { sessionId: string } }) {
  const { data: session, isLoading, error } = useSession(params.sessionId);
  if (isLoading) return <section className="page-section"><p className="muted">Loading session…</p></section>;
  if (error) return <section className="page-section"><h1>Session unavailable</h1><p className="form-error" role="alert">{error.message}</p></section>;
  return (
    <section className="page-section">
      <p className="eyebrow">Session</p>
      <h1>{session?.title || "New session"}</h1>
      <p><span className={`status-badge ${session?.status}`}>{session?.status}</span></p>
      <section className="panel placeholder-card">
        <h2>Your tutoring conversation will appear here</h2>
        <p className="muted">This session is ready. Interactive chat is introduced in Phase 3.</p>
      </section>
      <Link href="/sessions">Back to session history</Link>
    </section>
  );
}
