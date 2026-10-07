from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    ADMIN = "admin"


class LearnerLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MessageSender(StrEnum):
    STUDENT = "student"
    AGENT = "agent"
    SYSTEM = "system"


class MessageType(StrEnum):
    QUESTION = "question"
    RESPONSE = "response"
    GUIDANCE = "guidance"
    HINT = "hint"
    SUMMARY = "summary"
    SYSTEM = "system"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
