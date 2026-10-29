import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ChatWindow } from "@/components/chat/ChatWindow";
import { MessageInput } from "@/components/chat/MessageInput";
import { messagesQueryKey, useSendMessage } from "@/hooks/useMessages";
import { orderMessages } from "@/lib/message-order";
import type { Message, Page, SendMessageResponse } from "@/types/api";

const sessionId = "session-1";
const initialMessage: Message = {
  id: "agent-1",
  session_id: sessionId,
  sender: "agent",
  message_type: "guidance",
  content: "What have you noticed?",
  created_at: "2026-10-21T00:00:00Z",
};

function response(content: string): SendMessageResponse {
  return {
    student_message: {
      id: "student-1",
      session_id: sessionId,
      sender: "student",
      message_type: "response",
      content,
      created_at: "2026-10-21T00:00:01Z",
    },
    agent_message: {
      id: "agent-2",
      session_id: sessionId,
      sender: "agent",
      message_type: "guidance",
      content: "What evidence supports that?",
      created_at: "2026-10-21T00:00:02Z",
    },
    assessment: null,
    session_state: {
      status: "active",
      difficulty: 2,
      hint_level: 0,
      resolved: false,
      learner_level: "beginner",
      rag_status: "off",
    },
  };
}

function testClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
}

function wrapper(client: QueryClient) {
  return function QueryWrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("Phase 3 chat interface", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("sends on Enter, retains multiline behavior for Shift+Enter, and exposes the character limit", () => {
    const onChange = vi.fn();
    const onSend = vi.fn();
    render(<MessageInput value="A response" onChange={onChange} onSend={onSend} isSending={false} />);
    const input = screen.getByLabelText("Your response");

    fireEvent.keyDown(input, { key: "Enter" });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });

    expect(onSend).toHaveBeenCalledTimes(1);
    expect(input).toHaveAttribute("maxlength", "4000");
    expect(screen.getByText("10/4000")).toBeInTheDocument();
  });

  it("presents a polite accessible log and a distinct hint bubble", () => {
    render(
      <ChatWindow
        isResponding
        messages={[
          initialMessage,
          { ...initialMessage, id: "hint-1", message_type: "hint", content: "Try a smaller example." },
        ]}
      />,
    );

    expect(screen.getByRole("log", { name: "Tutoring conversation" })).toHaveAttribute("aria-live", "polite");
    expect(screen.getByText("💡 Hint")).toBeInTheDocument();
    expect(screen.getByLabelText("Tutor is typing")).toBeInTheDocument();
  });

  it("renders student first when response timestamps tie and API ids sort the agent first", () => {
    const sameTime = "2026-10-21T00:00:01Z";
    const student = { ...initialMessage, id: "z-student", sender: "student" as const, message_type: "response" as const, content: "I think the denominator stays the same", created_at: sameTime };
    const agent = { ...initialMessage, id: "a-agent", content: "What happens to both parts?", created_at: sameTime };

    const { container } = render(<ChatWindow isResponding={false} messages={[agent, student]} />);

    const entries = Array.from(container.querySelectorAll("article.message-row"));
    expect(entries.map((entry) => entry.textContent)).toEqual([
      "YouI think the denominator stays the same",
      "TutorWhat happens to both parts?",
    ]);
    expect(orderMessages([agent, student]).map((message) => message.id)).toEqual([student.id, agent.id]);
  });

  it("adds a student message optimistically and replaces it with saved messages", async () => {
    const client = testClient();
    client.setQueryData<Page<Message>>(messagesQueryKey(sessionId), { items: [initialMessage], total: 1, limit: 50, offset: 0 });
    let resolveFetch: ((value: Response) => void) | undefined;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => { resolveFetch = resolve; })));
    const { result } = renderHook(() => useSendMessage(sessionId), { wrapper: wrapper(client) });

    act(() => result.current.mutate({ content: "My thought" }));
    await waitFor(() => expect(client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))?.items).toHaveLength(2));
    expect(client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))?.items[1].id).toMatch(/^optimistic-/);

    await act(async () => {
      resolveFetch?.(new Response(JSON.stringify(response("My thought")), { status: 201, headers: { "Content-Type": "application/json" } }));
    });
    await waitFor(() => expect(client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))?.items.map((message) => message.id)).toEqual(["agent-1", "student-1", "agent-2"]));
  });

  it("deduplicates a refetched response pair and preserves student-first order", async () => {
    const client = testClient();
    const sameTime = "2026-10-21T00:00:01Z";
    const student = { ...initialMessage, id: "z-student", sender: "student" as const, message_type: "response" as const, content: "My thought", created_at: sameTime };
    const agent = { ...initialMessage, id: "a-agent", content: "What evidence supports that?", created_at: sameTime };
    client.setQueryData<Page<Message>>(messagesQueryKey(sessionId), { items: [initialMessage], total: 1, limit: 50, offset: 0 });
    let resolveFetch: ((value: Response) => void) | undefined;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => { resolveFetch = resolve; })));
    const { result } = renderHook(() => useSendMessage(sessionId), { wrapper: wrapper(client) });

    act(() => result.current.mutate({ content: "My thought" }));
    await waitFor(() => expect(client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))?.items).toHaveLength(2));
    client.setQueryData<Page<Message>>(messagesQueryKey(sessionId), {
      items: [initialMessage, agent, student, ...client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))!.items.filter((message) => message.id.startsWith("optimistic-"))],
      total: 4,
      limit: 50,
      offset: 0,
    });

    await act(async () => {
      resolveFetch?.(new Response(JSON.stringify({ ...response("My thought"), student_message: student, agent_message: agent }), { status: 201, headers: { "Content-Type": "application/json" } }));
    });

    await waitFor(() => {
      const items = client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))!.items;
      expect(items.map((message) => message.id)).toEqual(["agent-1", "z-student", "a-agent"]);
      expect(new Set(items.map((message) => message.id)).size).toBe(items.length);
    });
  });

  it("removes only a failed mutation's optimistic message when sends overlap", async () => {
    const client = testClient();
    client.setQueryData<Page<Message>>(messagesQueryKey(sessionId), { items: [initialMessage], total: 1, limit: 50, offset: 0 });
    const resolvers: ((value: Response) => void)[] = [];
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => { resolvers.push(resolve); })));
    const { result } = renderHook(() => useSendMessage(sessionId), { wrapper: wrapper(client) });

    act(() => result.current.mutate({ content: "First thought" }));
    await waitFor(() => expect(client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))?.items).toHaveLength(2));
    act(() => result.current.mutate({ content: "Second thought" }));
    await waitFor(() => expect(client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))?.items).toHaveLength(3));

    await act(async () => {
      resolvers[0](new Response(JSON.stringify({ error: { code: "LLM_UNAVAILABLE", message: "Tutor unavailable" } }), { status: 503, headers: { "Content-Type": "application/json" } }));
      resolvers[1](new Response(JSON.stringify(response("Second thought")), { status: 201, headers: { "Content-Type": "application/json" } }));
    });

    await waitFor(() => {
      const items = client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))!.items;
      expect(items.map((message) => message.content)).toEqual([
        "What have you noticed?",
        "Second thought",
        "What evidence supports that?",
      ]);
      expect(items.some((message) => message.content === "First thought")).toBe(false);
    });
  });

  it("restores the cached messages and returns the rejected draft to the caller", async () => {
    const client = testClient();
    const onError = vi.fn();
    client.setQueryData<Page<Message>>(messagesQueryKey(sessionId), { items: [initialMessage], total: 1, limit: 50, offset: 0 });
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ error: { code: "LLM_UNAVAILABLE", message: "Tutor unavailable" } }), { status: 503, headers: { "Content-Type": "application/json" } })));
    const { result } = renderHook(() => useSendMessage(sessionId, { onError }), { wrapper: wrapper(client) });

    act(() => result.current.mutate({ content: "Keep this draft" }));

    await waitFor(() => expect(onError).toHaveBeenCalledWith(expect.any(Error), "Keep this draft"));
    expect(client.getQueryData<Page<Message>>(messagesQueryKey(sessionId))).toEqual({ items: [initialMessage], total: 1, limit: 50, offset: 0 });
  });
});
