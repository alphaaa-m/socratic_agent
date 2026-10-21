import { SubjectCard } from "@/components/subjects/SubjectCard";
import type { Subject } from "@/types/api";

type SubjectGridProps = {
  subjects: Subject[];
  onStart: (subject: Subject) => void;
  isStarting: boolean;
};

export function SubjectGrid({ subjects, onStart, isStarting }: SubjectGridProps) {
  if (!subjects.length) {
    return <p className="empty-state">There are no active subjects yet. Please check back later.</p>;
  }

  return (
    <div className="subject-grid">
      {subjects.map((subject) => (
        <SubjectCard key={subject.id} subject={subject} onStart={onStart} isStarting={isStarting} />
      ))}
    </div>
  );
}
