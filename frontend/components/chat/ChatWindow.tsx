"use client";

import { useEffect, useRef } from "react";

import { MessageBubble } from "@/components/chat/MessageBubble";
import { orderMessages } from "@/lib/message-order";
import type { Message } from "@/types/api";

export function ChatWindow({ messages, isResponding }: { messages: Message[]; isResponding: boolean }) {
  const newest = useRef<HTMLDivElement>(null);
  const orderedMessages = orderMessages(messages);

  useEffect(() => {
    const target = newest.current;
    if (target && typeof target.scrollIntoView === "function") {
      target.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages, isResponding]);

  if (!orderedMessages.length && !isResponding) {
    return <section className="chat-log empty-chat" role="log" aria-live="polite" aria-label="Tutoring conversation">Start by asking a question.</section>;
  }

  return (
    <section className="chat-log" role="log" aria-live="polite" aria-label="Tutoring conversation">
      {orderedMessages.map((message) => <MessageBubble key={message.id} message={message} />)}
      {isResponding && (
        <div className="message-row agent" aria-label="Tutor is typing">
          <div className="typing-bubble"><span /><span /><span /></div>
        </div>
      )}
      <div ref={newest} />
    </section>
  );
}
