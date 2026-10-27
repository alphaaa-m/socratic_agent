import type { Message } from "@/types/api";

export function MessageBubble({ message }: { message: Message }) {
  const isStudent = message.sender === "student";
  const isHint = message.message_type === "hint";
  const label = isStudent ? "You" : isHint ? "Hint" : "Tutor";
  return (
    <article className={`message-row ${isStudent ? "student" : "agent"}`} aria-label={`${label} message`}>
      <div className={`message-bubble ${isStudent ? "student" : "agent"} ${isHint ? "hint" : ""}`}>
        <span className="message-label">{isHint ? "💡 Hint" : label}</span>
        <p>{message.content}</p>
      </div>
    </article>
  );
}
