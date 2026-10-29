"""Agent data contracts (docs Sec 14.3). Complete -- students do not change this file."""

from typing import Literal

from pydantic import BaseModel, Field

TurnKind = Literal["question", "response", "hint_request"]


class AgentState(BaseModel):
    """Saved in learning_sessions.agent_state (JSONB)."""

    turn_index: int = 0
    difficulty: int = Field(2, ge=1, le=5)
    hint_level: int = Field(0, ge=0, le=3)
    low_streak: int = 0
    high_streak: int = 0
    stuck_turns: int = 0
    hints_used: int = 0
    resolved: bool = False
    core_question: str | None = None
    last_agent_question: str | None = None
    target_concepts: list[str] = []
    misconceptions: dict[str, int] = {}
    demonstrated_concepts: list[str] = []
    perf_history: list[float] = []
    memory_summary: str = ""


class EvaluationResult(BaseModel):
    correctness_score: float = Field(ge=0, le=1)
    reasoning_score: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    misconception: str | None = None
    feedback: str
    demonstrated_concepts: list[str] = []
    addresses_core_question: bool
    requests_hint: bool = False


class TutorReply(BaseModel):
    message: str
    message_type: Literal["guidance", "hint"]
    target_concept: str | None = None


class SubjectRelevance(BaseModel):
    classification: Literal["relevant", "clearly_unrelated", "uncertain"]
    reason: str


class SessionSummary(BaseModel):
    outcome: Literal["resolved", "partial", "unresolved"]
    overview: str
    key_concepts: list[str]
    strengths: list[str]
    misconceptions_addressed: list[str]
    areas_to_review: list[str]
    next_steps: list[str]
    generated_by: Literal["llm", "fallback"] = "llm"


class ProfileSnapshot(BaseModel):
    current_level: Literal["beginner", "intermediate", "advanced"]
    level_score: float
    assessment_count: int
    learning_preferences: dict = {}
    weaknesses: list[dict] = []


class AgentTurnInput(BaseModel):
    kind: TurnKind
    student_message: str
    subject_id: str
    subject_name: str
    subject_description: str | None = None
    profile: ProfileSnapshot
    state: AgentState
    history: list[dict]
    is_first_turn: bool


class LearnerUpdate(BaseModel):
    level_score: float
    assessment_count: int
    current_level: str


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    content: str
    score: float


class AgentTurnOutput(BaseModel):
    reply: TutorReply
    evaluation: EvaluationResult | None
    performance: float | None
    difficulty_used: int
    new_state: AgentState
    learner_update: LearnerUpdate
    retrieved: list[RetrievedChunk]
    rag_status: Literal["off", "ok", "empty", "error"]
