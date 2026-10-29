"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/services/http";
import { listMessages, requestHint, sendMessage, type MessageListParams } from "@/services/messages";
import { mergeMessages, orderMessages } from "@/lib/message-order";
import type { HintResponse, Message, Page, SendMessageResponse } from "@/types/api";

const DEFAULT_PARAMS = { limit: 50, offset: 0 };

export function messagesQueryKey(sessionId: string, params: MessageListParams = DEFAULT_PARAMS) {
  return ["messages", sessionId, { limit: params.limit ?? 50, offset: params.offset ?? 0 }] as const;
}

const messagesPrefix = (sessionId: string) => ["messages", sessionId] as const;

export function useMessages(sessionId: string, params: MessageListParams = DEFAULT_PARAMS) {
  const normalized = { limit: params.limit ?? 50, offset: params.offset ?? 0 };
  return useQuery({
    queryKey: messagesQueryKey(sessionId, normalized),
    queryFn: async () => {
      const page = await listMessages(sessionId, normalized);
      return { ...page, items: orderMessages(page.items) };
    },
    enabled: Boolean(sessionId),
  });
}

type SendOptions = {
  onSuccess?: (response: SendMessageResponse) => void;
  onError?: (error: Error, content: string) => void;
};
type SendVariables = { content: string };
type OptimisticContext = {
  optimisticId: string;
};

export function useSendMessage(sessionId: string, options: SendOptions = {}) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ content }: SendVariables) => sendMessage(sessionId, content),
    onMutate: async ({ content }): Promise<OptimisticContext> => {
      await client.cancelQueries({ queryKey: messagesPrefix(sessionId) });
      const optimisticId = `optimistic-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      const optimistic: Message = {
        id: optimisticId,
        session_id: sessionId,
        sender: "student",
        message_type: "response",
        content,
        created_at: new Date().toISOString(),
      };
      client.setQueriesData<Page<Message>>({ queryKey: messagesPrefix(sessionId) }, (old) => {
        if (!old) return old;
        return { ...old, items: mergeMessages(old.items, [optimistic]), total: old.total + 1 };
      });
      return { optimisticId };
    },
    onSuccess: (response, _variables, context) => {
      client.setQueriesData<Page<Message>>({ queryKey: messagesPrefix(sessionId) }, (old) => {
        if (!old) return old;
        const withoutOptimistic = old.items.filter((message) => message.id !== context?.optimisticId);
        const knownIds = new Set(withoutOptimistic.map((message) => message.id));
        const added = [response.student_message, response.agent_message].filter((message) => !knownIds.has(message.id)).length;
        const removedOptimistic = old.items.length - withoutOptimistic.length;
        return {
          ...old,
          items: mergeMessages(withoutOptimistic, [response.student_message, response.agent_message]),
          total: old.total - removedOptimistic + added,
        };
      });
      options.onSuccess?.(response);
    },
    onError: (error, variables, context) => {
      if (context) {
        client.setQueriesData<Page<Message>>({ queryKey: messagesPrefix(sessionId) }, (old) => {
          if (!old) return old;
          const items = old.items.filter((message) => message.id !== context.optimisticId);
          const removed = old.items.length - items.length;
          return removed ? { ...old, items, total: old.total - removed } : old;
        });
      }
      if (error instanceof ApiError && error.code === "TURN_CONFLICT") {
        void client.invalidateQueries({ queryKey: messagesPrefix(sessionId) });
        void client.invalidateQueries({ queryKey: ["sessions", sessionId] });
      }
      options.onError?.(error, variables.content);
    },
    onSettled: () => client.invalidateQueries({ queryKey: messagesPrefix(sessionId) }),
  });
}

type HintOptions = {
  onSuccess?: (response: HintResponse) => void;
  onError?: (error: Error) => void;
};

export function useHint(sessionId: string, options: HintOptions = {}) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => requestHint(sessionId),
    onSuccess: (response) => {
      client.setQueriesData<Page<Message>>({ queryKey: messagesPrefix(sessionId) }, (old) => {
        if (!old) return old;
        const existed = old.items.some((message) => message.id === response.agent_message.id);
        return {
          ...old,
          items: mergeMessages(old.items, [response.agent_message]),
          total: old.total + (existed ? 0 : 1),
        };
      });
      options.onSuccess?.(response);
    },
    onError: (error) => {
      if (error instanceof ApiError && error.code === "TURN_CONFLICT") {
        void client.invalidateQueries({ queryKey: messagesPrefix(sessionId) });
        void client.invalidateQueries({ queryKey: ["sessions", sessionId] });
      }
      options.onError?.(error);
    },
    onSettled: () => client.invalidateQueries({ queryKey: messagesPrefix(sessionId) }),
  });
}
