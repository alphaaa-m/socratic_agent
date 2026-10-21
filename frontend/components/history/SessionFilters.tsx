"use client";

import type { SessionStatus, Subject } from "@/types/api";

type SessionFiltersProps = {
  subjects: Subject[];
  subjectId: string;
  status: "" | SessionStatus;
  onSubjectChange: (subjectId: string) => void;
  onStatusChange: (status: "" | SessionStatus) => void;
};

export function SessionFilters({ subjects, subjectId, status, onSubjectChange, onStatusChange }: SessionFiltersProps) {
  return (
    <div className="filters" aria-label="Session filters">
      <label>
        Subject
        <select value={subjectId} onChange={(event) => onSubjectChange(event.target.value)}>
          <option value="">All subjects</option>
          {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
        </select>
      </label>
      <label>
        Status
        <select value={status} onChange={(event) => onStatusChange(event.target.value as "" | SessionStatus)}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="abandoned">Abandoned</option>
        </select>
      </label>
    </div>
  );
}
