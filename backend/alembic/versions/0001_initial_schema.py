"""initial schema -- 9 tables per docs Sec 7.1.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), server_default="student", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('student', 'admin')", name="role_valid"),
        sa.CheckConstraint("email = lower(email)", name="email_lowercase"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "learner_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_level", sa.String(20), server_default="beginner", nullable=False),
        sa.Column("level_score", sa.Numeric(4, 3), server_default=sa.text("0.300"), nullable=False),
        sa.Column("assessment_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("learning_preferences", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("strengths", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("weaknesses", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("total_sessions", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("current_level IN ('beginner', 'intermediate', 'advanced')", name="level_valid"),
        sa.CheckConstraint("level_score BETWEEN 0 AND 1", name="level_score_range"),
        sa.CheckConstraint("assessment_count >= 0 AND total_sessions >= 0", name="counts_nonnegative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_learner_profiles_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_learner_profiles"),
        sa.UniqueConstraint("user_id", name="uq_learner_profiles_user_id"),
    )
    op.create_table(
        "subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_subjects"),
        sa.UniqueConstraint("name", name="uq_subjects_name"),
    )
    op.create_table(
        "learning_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), server_default="New session", nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("agent_state", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("summary", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('active', 'completed', 'abandoned')", name="status_valid"),
        sa.CheckConstraint("(status = 'active') = (ended_at IS NULL)", name="ended_matches_status"),
        sa.CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ended_after_start"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_learning_sessions_user_id_users", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], name="fk_learning_sessions_subject_id_subjects", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_learning_sessions"),
    )
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(20), nullable=False),
        sa.Column("retrieved_chunk_ids", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("sender IN ('student', 'agent', 'system')", name="sender_valid"),
        sa.CheckConstraint("message_type IN ('question', 'response', 'guidance', 'hint', 'summary', 'system')", name="type_valid"),
        sa.CheckConstraint("char_length(content) > 0", name="content_not_empty"),
        sa.CheckConstraint(
            "(sender = 'student' AND message_type IN ('question', 'response')) OR "
            "(sender = 'agent' AND message_type IN ('guidance', 'hint', 'summary')) OR "
            "(sender = 'system' AND message_type = 'system')",
            name="sender_type_consistent",
        ),
        sa.ForeignKeyConstraint(["session_id"], ["learning_sessions.id"], name="fk_messages_session_id_learning_sessions", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_messages"),
    )
    op.create_table(
        "learner_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correctness_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("reasoning_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("difficulty_level", sa.SmallInteger(), nullable=False),
        sa.Column("misconception", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("resolves_goal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("correctness_score BETWEEN 0 AND 1", name="correctness_range"),
        sa.CheckConstraint("reasoning_score BETWEEN 0 AND 1", name="reasoning_range"),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        sa.CheckConstraint("difficulty_level BETWEEN 1 AND 5", name="difficulty_range"),
        sa.ForeignKeyConstraint(["session_id"], ["learning_sessions.id"], name="fk_learner_assessments_session_id_learning_sessions", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], name="fk_learner_assessments_message_id_messages", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_learner_assessments"),
        sa.UniqueConstraint("message_id", name="uq_learner_assessments_message_id"),
    )
    op.create_table(
        "learning_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mastery_score", sa.Numeric(4, 3), server_default=sa.text("0"), nullable=False),
        sa.Column("topics_attempted", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("topics_mastered", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_activity_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("mastery_score BETWEEN 0 AND 1", name="mastery_range"),
        sa.CheckConstraint(
            "topics_attempted >= 0 AND topics_mastered >= 0 AND topics_mastered <= topics_attempted",
            name="topics_valid",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_learning_progress_user_id_users", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], name="fk_learning_progress_subject_id_subjects", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_learning_progress"),
        sa.UniqueConstraint("user_id", "subject_id", name="uq_learning_progress_user_id_subject_id"),
    )
    op.create_table(
        "knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("source", sa.String(500), nullable=True),
        sa.Column("content_hash", sa.CHAR(64), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'processing', 'indexed', 'failed')", name="status_valid"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], name="fk_knowledge_documents_subject_id_subjects", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], name="fk_knowledge_documents_uploaded_by_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_documents"),
        sa.UniqueConstraint("subject_id", "content_hash", name="uq_knowledge_documents_subject_id_content_hash"),
    )
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("vector_id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("embedding_reference", sa.String(100), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("chunk_index >= 0", name="index_nonnegative"),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], name="fk_document_chunks_document_id_knowledge_documents", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_document_chunks"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_id_chunk_index"),
        sa.UniqueConstraint("vector_id", name="uq_document_chunks_vector_id"),
        sa.UniqueConstraint("embedding_reference", name="uq_document_chunks_embedding_reference"),
    )
    # Indexes (Sec 7.1)
    op.execute('CREATE INDEX ix_learning_sessions_user_id_started_at ON learning_sessions (user_id, started_at DESC)')
    op.create_index("ix_learning_sessions_user_id_status", "learning_sessions", ["user_id", "status"])
    op.create_index("ix_learning_sessions_subject_id", "learning_sessions", ["subject_id"])
    op.create_index("ix_messages_session_id_created_at", "messages", ["session_id", "created_at"])
    op.create_index("ix_learner_assessments_session_id_created_at", "learner_assessments", ["session_id", "created_at"])
    op.create_index("ix_learning_progress_subject_id", "learning_progress", ["subject_id"])
    op.create_index("ix_knowledge_documents_subject_id_status", "knowledge_documents", ["subject_id", "status"])
    # updated_at triggers (Sec 7.1)
    op.execute(
        "CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$ "
        "BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;"
    )
    op.execute(
        "CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER trg_learner_profiles_updated_at BEFORE UPDATE ON learner_profiles "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER trg_learning_progress_updated_at BEFORE UPDATE ON learning_progress "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_learning_progress_updated_at ON learning_progress;")
    op.execute("DROP TRIGGER IF EXISTS trg_learner_profiles_updated_at ON learner_profiles;")
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
    op.execute("DROP INDEX IF EXISTS ix_learning_sessions_user_id_started_at;")
    op.drop_index("ix_knowledge_documents_subject_id_status", table_name="knowledge_documents")
    op.drop_index("ix_learning_progress_subject_id", table_name="learning_progress")
    op.drop_index("ix_learner_assessments_session_id_created_at", table_name="learner_assessments")
    op.drop_index("ix_messages_session_id_created_at", table_name="messages")
    op.drop_index("ix_learning_sessions_subject_id", table_name="learning_sessions")
    op.drop_index("ix_learning_sessions_user_id_status", table_name="learning_sessions")
    op.drop_table("document_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("learner_assessments")
    op.drop_table("messages")
    op.drop_table("learning_progress")
    op.drop_table("learning_sessions")
    op.drop_table("learner_profiles")
    op.drop_table("subjects")
    op.drop_table("users")
