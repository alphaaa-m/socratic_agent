export type Level = "beginner" | "intermediate" | "advanced";
export type SessionStatus = "active" | "completed" | "abandoned";
export type MessageType = "question" | "response" | "guidance" | "hint" | "summary" | "system";

export interface Message {
  id: string;
  session_id: string;
  sender: "student" | "agent" | "system";
  message_type: MessageType;
  content: string;
  created_at: string;
}

export interface Assessment {
  id: string;
  session_id: string;
  message_id: string;
  correctness_score: number;
  reasoning_score: number;
  confidence_score: number;
  difficulty_level: number;
  misconception: string | null;
  feedback: string | null;
  resolves_goal: boolean;
  created_at: string;
}

export interface SessionState {
  status: SessionStatus;
  difficulty: number;
  hint_level: number;
  resolved: boolean;
  learner_level: Level;
  rag_status: "off" | "ok" | "empty" | "error";
}

export interface SendMessageResponse {
  student_message: Message;
  agent_message: Message;
  assessment: Assessment | null;
  session_state: SessionState;
}

export interface HintResponse {
  agent_message: Message;
  session_state: SessionState;
}

export interface Subject {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface SubjectCreateRequest {
  name: string;
  description?: string | null;
}

export interface SubjectUpdateRequest {
  name?: string;
  description?: string | null;
  is_active?: boolean;
}

export interface LearningSession {
  id: string;
  subject_id: string;
  title: string;
  status: SessionStatus;
  started_at: string;
  ended_at: string | null;
}

export interface SessionDetail extends LearningSession {
  agent_state: Record<string, unknown>;
  summary: Record<string, unknown> | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: "student" | "admin";
  is_active: boolean;
  created_at: string;
}

export interface LearnerProfile {
  user_id: string;
  current_level: Level;
  level_score: number;
  assessment_count: number;
  learning_preferences: Record<string, unknown>;
  strengths: unknown[];
  weaknesses: unknown[];
  total_sessions: number;
}

export interface AdminUserUpdateRequest {
  role?: User["role"];
  is_active?: boolean;
}
