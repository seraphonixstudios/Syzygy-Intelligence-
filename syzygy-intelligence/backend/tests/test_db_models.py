"""Tests for database models and custom types."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.dialects.sqlite import dialect as sqlite_dialect


class TestEnums:
    def test_polarity_values(self):
        from app.db.models import Polarity
        assert list(Polarity) == [Polarity.MASCULINE, Polarity.FEMININE, Polarity.UNIFIED]

    def test_archetype_type_values(self):
        from app.db.models import ArchetypeType
        assert ArchetypeType.HERO.value == "hero"
        assert ArchetypeType.SELF.value == "self"

    def test_agent_role_values(self):
        from app.db.models import AgentRole
        assert AgentRole.PROPOSER.value == "proposer"

    def test_session_state_values(self):
        from app.db.models import SessionState
        assert SessionState.ACTIVE.value == "active"
        assert SessionState.FAILED.value == "failed"

    def test_subscription_tier_values(self):
        from app.db.models import SubscriptionTier
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.PREMIUM.value == "premium"

    def test_consensus_round_status_values(self):
        from app.db.models import ConsensusRoundStatus
        assert ConsensusRoundStatus.PENDING.value == "pending"
        assert ConsensusRoundStatus.COMPLETED.value == "completed"


class TestUUIDType:
    @pytest.fixture
    def uuid_type(self):
        from app.db.models import UUID
        return UUID()

    def test_load_dialect_impl_sqlite(self, uuid_type):
        impl = uuid_type.load_dialect_impl(sqlite_dialect())
        assert str(impl.__class__.__name__) == "String"

    def test_process_bind_param_none(self, uuid_type):
        assert uuid_type.process_bind_param(None, sqlite_dialect()) is None

    def test_process_bind_param_converts_to_str(self, uuid_type):
        val = uuid.uuid4()
        result = uuid_type.process_bind_param(val, sqlite_dialect())
        assert result == str(val)

    def test_process_result_value_sqlite_converts_to_uuid(self, uuid_type):
        val = uuid.uuid4()
        result = uuid_type.process_result_value(str(val), sqlite_dialect())
        assert result == val

    def test_process_result_value_sqlite_invalid_string(self, uuid_type):
        result = uuid_type.process_result_value("not-a-uuid", sqlite_dialect())
        assert result == "not-a-uuid"

    def test_process_result_value_none(self, uuid_type):
        assert uuid_type.process_result_value(None, sqlite_dialect()) is None


class TestARRAYType:
    @pytest.fixture
    def array_type(self):
        from app.db.models import ARRAY
        return ARRAY()

    def test_load_dialect_impl_sqlite(self, array_type):
        impl = array_type.load_dialect_impl(sqlite_dialect())
        assert str(impl.__class__.__name__) == "Text"

    def test_bind_param_sqlite_serializes(self, array_type):
        result = array_type.process_bind_param(["a", "b", "c"], sqlite_dialect())
        assert result == '["a", "b", "c"]'

    def test_bind_param_sqlite_none(self, array_type):
        result = array_type.process_bind_param(None, sqlite_dialect())
        assert result == "[]"

    def test_result_value_sqlite_deserializes(self, array_type):
        result = array_type.process_result_value('["a", "b"]', sqlite_dialect())
        assert result == ["a", "b"]

    def test_result_value_sqlite_none(self, array_type):
        result = array_type.process_result_value(None, sqlite_dialect())
        assert result == []

    def test_result_value_sqlite_empty_string(self, array_type):
        result = array_type.process_result_value("[]", sqlite_dialect())
        assert result == []


class TestVECTORType:
    def test_fallback_is_type_decorator(self):
        from app.db.models import VECTOR
        from sqlalchemy import TypeDecorator
        assert issubclass(VECTOR, TypeDecorator)

    def test_fallback_impl_is_large_binary(self):
        from app.db.models import VECTOR
        from sqlalchemy import LargeBinary
        v = VECTOR()
        impl = v.load_dialect_impl(sqlite_dialect())
        assert isinstance(impl, LargeBinary)


class TestModelInstantiation:
    def test_user_construct_and_set_fields(self):
        from app.db.models import User, SubscriptionTier
        uid = uuid.uuid4()
        u = User(
            id=uid,
            email="test@test.com",
            hashed_password="hash",
            display_name="Admin",
            is_active=True,
            is_superuser=True,
            subscription_tier=SubscriptionTier.PREMIUM,
            settings={"theme": "dark"},
        )
        assert u.id == uid
        assert u.email == "test@test.com"
        assert u.hashed_password == "hash"
        assert u.display_name == "Admin"
        assert u.is_active is True
        assert u.is_superuser is True
        assert u.subscription_tier == SubscriptionTier.PREMIUM
        assert u.settings == {"theme": "dark"}

    def test_user_minimal_construct(self):
        from app.db.models import User
        uid = uuid.uuid4()
        u = User(id=uid, email="min@test.com", hashed_password="hash")
        assert u.email == "min@test.com"

    def test_user_str_representation(self):
        from app.db.models import User
        u = User(id=uuid.uuid4(), email="repr@test.com", hashed_password="hash")
        assert "User" in repr(u)

    def test_agent_construct(self):
        from app.db.models import Agent, Polarity, ArchetypeType
        uid = uuid.uuid4()
        a = Agent(
            id=uuid.uuid4(),
            user_id=uid,
            name="Test Agent",
            polarity=Polarity.MASCULINE,
            primary_archetype=ArchetypeType.HERO,
            persona_instructions="Be helpful",
        )
        assert a.name == "Test Agent"
        assert a.polarity == Polarity.MASCULINE
        assert a.primary_archetype == ArchetypeType.HERO
        assert a.persona_instructions == "Be helpful"

    def test_agent_with_capabilities(self):
        from app.db.models import Agent, Polarity, ArchetypeType
        a = Agent(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Capable Agent",
            polarity=Polarity.FEMININE,
            primary_archetype=ArchetypeType.SAGE,
            capabilities=["coding", "research"],
        )
        assert a.capabilities == ["coding", "research"]

    def test_session_construct(self):
        from app.db.models import Session
        s = Session(
            id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test Session",
            task_description="Do work",
            workflow_type="research",
        )
        assert s.name == "Test Session"
        assert s.task_description == "Do work"
        assert s.workflow_type == "research"

    def test_api_key_construct(self):
        from app.db.models import ApiKey
        k = ApiKey(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test Key",
            key_prefix="sk-",
            hashed_key="hash123",
            searchable_key_hash="abc123def456",
        )
        assert k.name == "Test Key"
        assert k.key_prefix == "sk-"
        assert k.hashed_key == "hash123"

    def test_consensus_round_construct(self):
        from app.db.models import ConsensusRound
        r = ConsensusRound(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            round_number=1,
            proposals=[{"agent_id": "a1", "content": "proposal"}],
            scores={"a1": 0.9},
        )
        assert r.round_number == 1
        assert r.proposals == [{"agent_id": "a1", "content": "proposal"}]
        assert r.scores == {"a1": 0.9}

    def test_memory_construct(self):
        from app.db.models import Memory
        m = Memory(
            id=uuid.uuid4(),
            memory_type="short_term",
            content="Important info",
            tags=["key", "value"],
        )
        assert m.memory_type == "short_term"
        assert m.content == "Important info"
        assert m.tags == ["key", "value"]

    def test_task_result_construct(self):
        from app.db.models import TaskResult
        t = TaskResult(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            task_id="t1",
            task_type="code",
            status="running",
            priority=5,
        )
        assert t.task_id == "t1"
        assert t.task_type == "code"
        assert t.status == "running"
        assert t.priority == 5

    def test_audit_log_construct(self):
        from app.db.models import AuditLog
        entry = AuditLog(
            id=uuid.uuid4(),
            event_type="login",
            action="user_login",
            ip_address="127.0.0.1",
        )
        assert entry.event_type == "login"
        assert entry.action == "user_login"
        assert entry.ip_address == "127.0.0.1"
