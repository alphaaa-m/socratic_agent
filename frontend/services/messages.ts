import { api } from "@/services/http";
import type { HintResponse, Message, Page, SendMessageResponse } from "@/types/api";

export type MessageListParams = {
  limit?: number;
  offset?: number;
};

export function listMessages(sessionId: string, params: MessageListParams = {}) {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));
  const suffix = query.size ? `?${query}` : "";
  return api<Page<Message>>(`sessions/${sessionId}/messages${suffix}`);
}

export function sendMessage(sessionId: string, content: string) {
  return api<SendMessageResponse>(`sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function requestHint(sessionId: string) {
  return api<HintResponse>(`sessions/${sessionId}/hints`, { method: "POST" });
}
