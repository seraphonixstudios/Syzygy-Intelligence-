"""SQLAlchemy ORM models for Syzygy Intelligence."""
# mypy: disable-error-code="var-annotated,misc"

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from sqlalchemy.dialects.postgresql import VECTOR  # type: ignore[attr-defined]
except ImportError:
    from sqlalchemy import LargeBinary

    class VECTOR(TypeDecorator[Any]):  # type: ignore[no-redef]
        """Fallback for when pgvector is not installed."""
        impl = LargeBinary
        def load_dialect_impl(self, dialect: Any) -> Any:
            return dialect.type_descriptor(LargeBinary())


# SQLite-compatible UUID fallback
class UUID(TypeDecorator[Any]):
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(36))
        return PG_UUID()

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        return value


# SQLite-compatible ARRAY fallback
class ARRAY(TypeDecorator[Any]):
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(Text())
        return PG_ARRAY(String)

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if dialect.name == "sqlite":
            import json
            return json.dumps(value or [])
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if dialect.name == "sqlite" and isinstance(value, str):
            import json
            return json.loads(value)
        return value or []


class Polarity(enum.StrEnum):
    MASCULINE = "masculine"
    FEMININE = "feminine"
    UNIFIED = "unified"


class ArchetypeType(enum.StrEnum):
    HERO = "hero"
    SAGE = "sage"
    RULER = "ruler"
    MAGICIAN = "magician"
    EXPLORER = "explorer"
    GREAT_MOTHER = "great_mother"
    LOVER = "lover"
    INNOCENT = "innocent"
    CREATOR = "creator"
    ANIMA = "anima"
    SELF = "self"
    HERMES = "hermes"
    TRICKSTER = "trickster"


class AgentRole(enum.StrEnum):
    PROPOSER = "proposer"
    CRITIC = "critic"
    REFINER = "refiner"
    EVALUATOR = "evaluator"
    SYNTHESIZER = "synthesizer"
    ORCHESTRATOR = "orchestrator"


class SessionState(enum.StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ConsensusRoundStatus(enum.StrEnum):
    PENDING = "pending"
    PROPOSAL = "proposal"
    CRITIQUE = "critique"
    REFINEMENT = "refinement"
    EVALUATION = "evaluation"
    CONVERGED = "converged"
    COMPLETED = "completed"
    FAILED = "failed"


class SubscriptionTier(enum.StrEnum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    usage_reset_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    message_count = Column(Integer, default=0)
    subscription_tier = Column(SAEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_user_email", "email"),
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(16), nullable=False)
    hashed_key = Column(String(255), nullable=False, unique=True)
    searchable_key_hash = Column(String(16), nullable=False, index=True, unique=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", backref="api_keys")

    __table_args__ = (
        Index("idx_api_key_user", "user_id"),
        Index("idx_api_key_searchable", "searchable_key_hash"),
        Index("idx_api_key_active", "is_active"),
    )


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    polarity = Column(SAEnum(Polarity), nullable=False)
    primary_archetype = Column(SAEnum(ArchetypeType), nullable=False)
    shadow_archetype = Column(SAEnum(ArchetypeType), nullable=True)
    persona_instructions = Column(Text, nullable=True)
    model = Column(String(255), nullable=False, default="qwen3:8b-gpu")
    system_prompt = Column(Text, nullable=True)
    capabilities = Column(ARRAY(String), default=[])
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="agents")
    sessions = relationship("Session", back_populates="agent")
    memories = relationship("Memory", back_populates="agent")

    __table_args__ = (
        Index("idx_agent_user", "user_id"),
        Index("idx_agent_polarity", "polarity"),
        Index("idx_agent_archetype", "primary_archetype"),
    )


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    state = Column(SAEnum(SessionState), default=SessionState.ACTIVE)
    task_description = Column(Text, nullable=True)
    workflow_type = Column(String(100), nullable=True)
    consensus_rounds_completed = Column(Integer, default=0)
    polarity_balance_score = Column(Float, nullable=True)
    final_synthesis = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("User", backref="sessions")
    agent = relationship("Agent", back_populates="sessions")
    consensus_rounds = relationship("ConsensusRound", back_populates="session")
    task_results = relationship("TaskResult", back_populates="session")
    memory_entries = relationship("Memory", back_populates="session")

    __table_args__ = (
        Index("idx_session_user", "user_id"),
        Index("idx_session_state", "state"),
        Index("idx_session_agent", "agent_id"),
    )


class ConsensusRound(Base):
    __tablename__ = "consensus_rounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    status = Column(SAEnum(ConsensusRoundStatus), default=ConsensusRoundStatus.PENDING)
    proposals = Column(JSON, default=list)
    critiques = Column(JSON, default=list)
    refinements = Column(JSON, default=list)
    evaluations = Column(JSON, default=list)
    scores = Column(JSON, default=dict)
    convergence_score = Column(Float, nullable=True)
    polarity_balance = Column(Float, nullable=True)
    synthesis = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    session = relationship("Session", back_populates="consensus_rounds")

    __table_args__ = (
        Index("idx_round_session", "session_id"),
        Index("idx_round_number", "session_id", "round_number", unique=True),
    )


class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    memory_type = Column(String(50), nullable=False)  # short_term, long_term, team, polarity, archetype
    content = Column(Text, nullable=False)
    embedding = Column(VECTOR(1536), nullable=True)
    polarity = Column(SAEnum(Polarity), nullable=True)
    archetype = Column(SAEnum(ArchetypeType), nullable=True)
    importance_score = Column(Float, default=0.0)
    tags = Column(ARRAY(String), default=[])
    source = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    agent = relationship("Agent", back_populates="memories")
    session = relationship("Session", back_populates="memory_entries")

    __table_args__ = (
        Index("idx_memory_type", "memory_type"),
        Index("idx_memory_polarity", "polarity"),
        Index("idx_memory_agent", "agent_id"),
        Index("idx_memory_session", "session_id"),
        Index("idx_memory_expires", "expires_at"),
    )


class TaskResult(Base):
    __tablename__ = "task_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(255), nullable=False, index=True)
    parent_task_id = Column(String(255), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending", index=True)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    priority = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("Session", back_populates="task_results")

    __table_args__ = (
        Index("idx_task_session", "session_id"),
        Index("idx_task_id", "task_id"),
        Index("idx_task_status", "status"),
        Index("idx_task_created", "created_at"),
        Index("idx_task_session_status", "session_id", "status"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    action = Column(String(255), nullable=False)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)

    __table_args__ = (
        Index("idx_audit_event", "event_type"),
        Index("idx_audit_session", "session_id"),
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_event_created", "event_type", "created_at"),
    )
