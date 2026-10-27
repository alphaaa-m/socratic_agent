"use client";

import type { KeyboardEvent } from "react";

type MessageInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isSending: boolean;
};

export function MessageInput({ value, onChange, onSend, isSending }: MessageInputProps) {
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (value.trim() && !isSending) onSend();
    }
  };

  return (
    <div className="message-input">
      <label htmlFor="chat-message">Your response</label>
      <textarea
        id="chat-message"
        value={value}
        maxLength={4000}
        disabled={isSending}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your question or response…"
        rows={3}
      />
      <div className="message-input-actions">
        <span className="character-count" aria-live="polite">{value.length}/4000</span>
        <button className="primary-button chat-send" type="button" disabled={isSending || !value.trim()} onClick={onSend}>
          {isSending ? "Sending…" : "Send"}
        </button>
      </div>
    </div>
  );
}
