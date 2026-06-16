"""add remaining tables (api_keys, agents, sessions, consensus_rounds, memories, task_results, audit_logs)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ARCHETYPES = ["hero", "sage", "ruler", "magician", "explorer", "great_mother",
              "lover", "innocent", "creator", "anima", "self", "hermes", "trickster"]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("hashed_key", sa.String(255), nullable=False, unique=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_api_key_user", "api_keys", ["user_id"])
    op.create_index("idx_api_key_hash", "api_keys", ["hashed_key"])

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("polarity",
                  sa.Enum("masculine", "feminine", "unified", name="polarity"),
                  nullable=False),
        sa.Column("primary_archetype",
                  sa.Enum(*ARCHETYPES, name="archetypetype"), nullable=False),
        sa.Column("shadow_archetype",
                  sa.Enum(*ARCHETYPES, name="archetypetype"), nullable=True),
        sa.Column("persona_instructions", sa.Text, nullable=True),
        sa.Column("model", sa.String(255), nullable=False),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("capabilities", postgresql.ARRAY(sa.String), default=[]),
        sa.Column("metadata", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_agent_polarity", "agents", ["polarity"])
    op.create_index("idx_agent_archetype", "agents", ["primary_archetype"])

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("state", sa.Enum("active", "paused", "completed", "failed",
                                   name="sessionstate"), default="active"),
        sa.Column("task_description", sa.Text, nullable=True),
        sa.Column("workflow_type", sa.String(100), nullable=True),
        sa.Column("consensus_rounds_completed", sa.Integer, default=0),
        sa.Column("polarity_balance_score", sa.Float, nullable=True),
        sa.Column("final_synthesis", sa.Text, nullable=True),
        sa.Column("metadata", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_session_state", "sessions", ["state"])
    op.create_index("idx_session_agent", "sessions", ["agent_id"])

    op.create_table(
        "consensus_rounds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("round_number", sa.Integer, nullable=False),
        sa.Column("status", sa.Enum("pending", "proposal", "critique",
                                    "refinement", "evaluation", "converged",
                                    "completed", "failed",
                                    name="consensusroundstatus"),
                  default="pending"),
        sa.Column("proposals", sa.JSON, default=list),
        sa.Column("critiques", sa.JSON, default=list),
        sa.Column("refinements", sa.JSON, default=list),
        sa.Column("evaluations", sa.JSON, default=list),
        sa.Column("scores", sa.JSON, default=dict),
        sa.Column("convergence_score", sa.Float, nullable=True),
        sa.Column("polarity_balance", sa.Float, nullable=True),
        sa.Column("synthesis", sa.Text, nullable=True),
        sa.Column("metadata", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_round_session", "consensus_rounds", ["session_id"])
    op.create_index("idx_round_number", "consensus_rounds",
                    ["session_id", "round_number"], unique=True)

    op.create_table(
        "memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("memory_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("polarity",
                  sa.Enum("masculine", "feminine", "unified", name="polarity"),
                  nullable=True),
        sa.Column("archetype",
                  sa.Enum(*ARCHETYPES, name="archetypetype"), nullable=True),
        sa.Column("importance_score", sa.Float, default=0.0),
        sa.Column("tags", postgresql.ARRAY(sa.String), default=[]),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("metadata", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_memory_type", "memories", ["memory_type"])
    op.create_index("idx_memory_polarity", "memories", ["polarity"])
    op.create_index("idx_memory_agent", "memories", ["agent_id"])
    op.create_index("idx_memory_session", "memories", ["session_id"])

    op.create_table(
        "task_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("task_id", sa.String(255), nullable=False),
        sa.Column("parent_task_id", sa.String(255), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("task_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("input_data", sa.JSON, default=dict),
        sa.Column("output_data", sa.JSON, default=dict),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("execution_time_ms", sa.Integer, nullable=True),
        sa.Column("priority", sa.Integer, default=0),
        sa.Column("metadata", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("details", sa.JSON, default=dict),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_audit_event", "audit_logs", ["event_type"])
    op.create_index("idx_audit_session", "audit_logs", ["session_id"])
    op.create_index("idx_audit_created", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("task_results")
    op.drop_table("memories")
    op.drop_table("consensus_rounds")
    op.drop_table("sessions")
    op.drop_table("agents")
    op.drop_table("api_keys")

    op.execute("DROP TYPE IF EXISTS consensusroundstatus")
    op.execute("DROP TYPE IF EXISTS sessionstate")
    op.execute("DROP TYPE IF EXISTS archetypetype")
    op.execute("DROP TYPE IF EXISTS polarity")
