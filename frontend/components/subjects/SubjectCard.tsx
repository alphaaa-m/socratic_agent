"use client";

import type { Subject } from "@/types/api";

type SubjectCardProps = {
  subject: Subject;
  onStart: (subject: Subject) => void;
  isStarting: boolean;
};

export function SubjectCard({ subject, onStart, isStarting }: SubjectCardProps) {
  return (
    <article className="subject-card">
      <div>
        <h2>{subject.name}</h2>
        <p className="muted">{subject.description || "Choose this subject to begin a guided learning session."}</p>
      </div>
      <button className="primary-button card-action" type="button" disabled={isStarting} onClick={() => onStart(subject)}>
        {isStarting ? "Starting session…" : "Start session"}
      </button>
    </article>
  );
}
