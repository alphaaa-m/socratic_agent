import type { Message } from "@/types/api";

const senderOrder: Record<Message["sender"], number> = {
  student: 0,
  system: 1,
  agent: 2,
};

/** Sort conversation records by time, putting student messages first on timestamp ties. */
export function orderMessages(messages: Message[]): Message[] {
  const unique = new Map<string, Message>();
  for (const message of messages) unique.set(message.id, message);

  return [...unique.values()].sort((left, right) => {
    const timeOrder = left.created_at.localeCompare(right.created_at);
    if (timeOrder !== 0) return timeOrder;
    return senderOrder[left.sender] - senderOrder[right.sender];
  });
}

export function mergeMessages(existing: Message[], incoming: Message[]): Message[] {
  return orderMessages([...existing, ...incoming]);
}
