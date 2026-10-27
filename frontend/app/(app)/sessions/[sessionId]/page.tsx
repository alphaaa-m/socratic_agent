"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ChatWindow } from "@/components/chat/ChatWindow";
import { HintButton } from "@/components/chat/HintButton";
import { MessageInput } from "@/components/chat/MessageInput";
import { SessionStatusBar } from "@/components/chat/SessionStatusBar";
import { useHint, useMessages, useSendMessage } from "@/hooks/useMessages";
import { useSession } from "@/hooks/useSessions";
import { useLearnerProfile } from "@/hooks/useUsers";
import { ApiError } from "@/services/http";
import type { SessionDetail, SessionState } from "@/types/api";

function initialSessionState(session: SessionDetail, learnerLevel: SessionState["learner_level"] = "beginner"): SessionState {
  const state = session.agent_state;
  return {
    status: session.status,
    difficulty: typeof state.difficulty === "number" ? state.difficulty : 2,
    hint_level: typeof state.hint_level === "number" ? state.hint_level : 0,
    resolved: state.resolved === true,
    learner_level: learnerLevel,
    rag_status: "off",
  };
}

export default function ChatPage({ params }: { params: { sessionId: string } }) {
  const { data: session, isLoading, error } = useSession(params.sessionId);
  const { data: profile } = useLearnerProfile();
  const messages = useMessages(params.sessionId);
  const [draft, setDraft] = useState("");
  const [liveState, setLiveState] = useState<SessionState | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const loadedSessionId = session?.id;

  useEffect(() => {
    setLiveState(null);
  }, [loadedSessionId]);

  const send = useSendMessage(params.sessionId, {
    onSuccess: (response) => setLiveState(response.session_state),
    onError: (requestError, content) => {
      setDraft(content);
      setNotice(requestError instanceof ApiError && requestError.code === "TURN_CONFLICT" ? "Conversation changed. Messages were reloaded." : requestError.message);
    },
  });
  const hint = useHint(params.sessionId, {
    onSuccess: (response) => setLiveState(response.session_state),
    onError: (requestError) => {
      setNotice(requestError instanceof ApiError && requestError.code === "TURN_CONFLICT" ? "Conversation changed. Messages were reloaded." : requestError.message);
    },
  });

  if (isLoading) return <section className="page-section"><p className="muted">Loading session...</p></section>;
  if (error) return <section className="page-section"><h1>Session unavailable</h1><p className="form-error" role="alert">{error.message}</p></section>;
  if (!session) return null;

  const state = liveState ?? initialSessionState(session, profile?.current_level);
  const readOnly = session.status !== "active";
  const submit = () => {
    const content = draft;
    if (!content.trim() || send.isPending) return;
    setDraft("");
    setNotice(null);
    send.mutate({ content });
  };

  return (
    <section className="page-section chat-page">
      <p className="eyebrow">Session</p>
      <div className="chat-heading">
        <h1>{session.title || "New session"}</h1>
        <span className={`status-badge ${session.status}`}>{session.status}</span>
      </div>
      <SessionStatusBar state={state} />
      {messages.isLoading ? <p className="muted">Loading conversation...</p> : null}
      {messages.error ? <p className="form-error" role="alert">{messages.error.message}</p> : null}
      <section className="panel chat-panel">
        <ChatWindow messages={messages.data?.items ?? []} isResponding={send.isPending || hint.isPending} />
        {notice && <p className="chat-toast" role="alert">{notice}</p>}
        {readOnly ? (
          <p className="read-only-notice" role="status">This {session.status} session is read-only.</p>
        ) : (
          <div className="chat-controls">
            <MessageInput value={draft} onChange={setDraft} onSend={submit} isSending={send.isPending || hint.isPending} />
            <div className="chat-actions">
              <HintButton onRequest={() => { setNotice(null); hint.mutate(); }} isRequesting={hint.isPending} disabled={send.isPending} />
              <span title="Available in phase 6">
                <button className="secondary-button" type="button" disabled>End session</button>
              </span>
            </div>
          </div>
        )}
      </section>
      <Link href="/sessions">Back to session history</Link>
    </section>
  );
}
