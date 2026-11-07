import type { Assessment, Message } from "@/types/api";
import { FeedbackChip } from "@/components/chat/FeedbackChip";

export function MessageBubble({ message, assessment }: { message: Message; assessment?: Assessment | null }) {
  const isStudent = message.sender === "student";
  const isHint = message.message_type === "hint";
  const label = isStudent ? "You" : isHint ? "Hint" : "Tutor";
  return (
    <article className={`message-row ${isStudent ? "student" : "agent"}`} aria-label={`${label} message`}>
      <div className={`message-bubble ${isStudent ? "student" : "agent"} ${isHint ? "hint" : ""}`}>
        <span className="message-label">{isHint ? "💡 Hint" : label}</span>
        <p>{message.content}</p>
      </div>
      {isStudent && assessment?.feedback ? <FeedbackChip feedback={assessment.feedback} /> : null}
    </article>
  );
}
