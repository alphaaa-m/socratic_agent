import type { SessionState } from "@/types/api";

export function SessionStatusBar({ state }: { state: SessionState }) {
  const difficulty = "●".repeat(state.difficulty) + "○".repeat(5 - state.difficulty);
  return (
    <div className="session-status" aria-label="Session status">
      <span>Level: {state.learner_level}</span>
      <span aria-label={`Difficulty ${state.difficulty} out of 5`}>Difficulty: {difficulty}</span>
      <span>Hint level: {state.hint_level}/3</span>
    </div>
  );
}
