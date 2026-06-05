"""Unit tests for Syzygy Intelligence Agent System."""

import pytest
from app.agents.archetypes import (
    ARCHETYPE_REGISTRY, SHADOWS, get_archetype, get_shadow,
    get_archetypes_by_polarity, Polarity, HERO, SAGE, GREAT_MOTHER, SELF
)
from app.agents.polarity import (
    PolarityType, POLARITY_CONFIGS, compute_polarity_balance,
    is_balanced, get_dominant_polarity
)
from app.agents.personas import PERSONA_REGISTRY, get_persona, PersonaStyle
from app.agents.base import SyzygyAgent
from app.agents.registry import AgentRegistry


class TestArchetypes:
    def test_all_archetypes_registered(self):
        assert len(ARCHETYPE_REGISTRY) == 13
        assert "hero" in ARCHETYPE_REGISTRY
        assert "sage" in ARCHETYPE_REGISTRY
        assert "self" in ARCHETYPE_REGISTRY
        assert "trickster" in ARCHETYPE_REGISTRY

    def test_archetype_polarities(self):
        assert ARCHETYPE_REGISTRY["hero"].polarity == Polarity.MASCULINE
        assert ARCHETYPE_REGISTRY["great_mother"].polarity == Polarity.FEMININE
        assert ARCHETYPE_REGISTRY["self"].polarity == Polarity.UNIFIED

    def test_archetype_strengths(self):
        assert "courage" in HERO.strengths
        assert "wisdom" in SAGE.strengths
        assert "nurturing" in GREAT_MOTHER.strengths
        assert "integration" in SELF.strengths

    def test_get_archetype(self):
        assert get_archetype("hero") == HERO
        assert get_archetype("nonexistent") is None

    def test_get_shadow(self):
        shadow = get_shadow("hero")
        assert shadow is not None
        assert shadow.name == "Shadow Warrior"
        assert get_shadow("nonexistent") is None

    def test_get_archetypes_by_polarity(self):
        masc = get_archetypes_by_polarity(Polarity.MASCULINE)
        fem = get_archetypes_by_polarity(Polarity.FEMININE)
        unified = get_archetypes_by_polarity(Polarity.UNIFIED)
        assert len(masc) == 5
        assert len(fem) == 5
        assert len(unified) == 3

    def test_all_shadows_present(self):
        for key in ARCHETYPE_REGISTRY:
            assert key in SHADOWS, f"Missing shadow for {key}"


class TestPolarity:
    def test_polarity_configs(self):
        assert len(POLARITY_CONFIGS) == 3
        assert PolarityType.MASCULINE in POLARITY_CONFIGS

    def test_polarity_glyphs(self):
        assert POLARITY_CONFIGS[PolarityType.MASCULINE].glyph == "☉"
        assert POLARITY_CONFIGS[PolarityType.FEMININE].glyph == "☽"
        assert POLARITY_CONFIGS[PolarityType.UNIFIED].glyph == "☿"

    def test_opposite_polarity(self):
        masc = POLARITY_CONFIGS[PolarityType.MASCULINE]
        fem = POLARITY_CONFIGS[PolarityType.FEMININE]
        assert masc.opposite == PolarityType.FEMININE
        assert fem.opposite == PolarityType.MASCULINE
        assert POLARITY_CONFIGS[PolarityType.UNIFIED].opposite == PolarityType.UNIFIED

    def test_compute_polarity_balance(self):
        assert compute_polarity_balance([]) == 0.5
        assert compute_polarity_balance(
            [PolarityType.MASCULINE, PolarityType.FEMININE]
        ) == 1.0
        assert compute_polarity_balance(
            [PolarityType.MASCULINE, PolarityType.MASCULINE, PolarityType.FEMININE]
        ) == pytest.approx(0.666, 0.01)

    def test_is_balanced(self):
        assert is_balanced(0.8, threshold=0.6)
        assert not is_balanced(0.5, threshold=0.6)

    def test_get_dominant_polarity(self):
        assert get_dominant_polarity([PolarityType.MASCULINE]) == PolarityType.MASCULINE
        assert get_dominant_polarity([PolarityType.FEMININE]) == PolarityType.FEMININE
        assert get_dominant_polarity(
            [PolarityType.MASCULINE, PolarityType.FEMININE, PolarityType.UNIFIED]
        ) == PolarityType.UNIFIED


class TestPersonas:
    def test_all_personas_registered(self):
        assert len(PERSONA_REGISTRY) == 13

    def test_persona_styles(self):
        for key, persona in PERSONA_REGISTRY.items():
            assert persona.name
            assert persona.archetype

    def test_get_persona(self):
        persona = get_persona("hero")
        assert persona is not None
        assert persona.name == "Valiant"
        assert get_persona("nonexistent") is None

    def test_persona_system_prompt(self):
        persona = get_persona("sage")
        assert persona.to_system_prompt_fragment()
        assert "Sage" in persona.to_system_prompt_fragment()


class TestSyzygyAgent:
    def test_agent_creation(self):
        agent = SyzygyAgent.create("sage", name="TestSage", model="test-model")
        assert agent.name == "TestSage"
        assert agent.archetype_key == "sage"
        assert agent.archetype == SAGE
        assert agent.polarity == PolarityType.MASCULINE
        assert agent.model == "test-model"

    def test_agent_default_name(self):
        agent = SyzygyAgent.create("hero")
        assert agent.name == "Hero"

    def test_agent_polarity(self):
        assert SyzygyAgent.create("hero").polarity == PolarityType.MASCULINE
        assert SyzygyAgent.create("great_mother").polarity == PolarityType.FEMININE
        assert SyzygyAgent.create("self").polarity == PolarityType.UNIFIED

    def test_agent_shadow(self):
        agent = SyzygyAgent.create("hero")
        assert agent.shadow is None
        agent.activate_shadow()
        assert agent.shadow is not None
        assert agent.shadow.name == "Shadow Warrior"
        agent.deactivate_shadow()
        assert agent.shadow is None

    def test_agent_system_prompt(self):
        agent = SyzygyAgent.create("sage")
        prompt = agent.build_system_prompt()
        assert prompt
        assert "Sage" in prompt or "sage" in prompt.lower()

    def test_agent_shadow_prompt(self):
        agent = SyzygyAgent.create("ruler", shadow_active=True)
        prompt = agent.build_system_prompt()
        assert "Shadow" in prompt or "shadow" in prompt.lower()

    def test_agent_glyph(self):
        assert SyzygyAgent.create("hero").glyph == "☉"
        assert SyzygyAgent.create("great_mother").glyph == "☽"
        assert SyzygyAgent.create("self").glyph == "☿"

    def test_agent_to_dict(self):
        agent = SyzygyAgent.create("sage", name="Test")
        d = agent.to_dict()
        assert d["name"] == "Test"
        assert d["archetype"] == "sage"
        assert d["polarity"] == "masculine"
        assert d["glyph"] == "☉"


class TestAgentRegistry:
    def test_register_and_get(self):
        registry = AgentRegistry()
        registry.clear()
        agent = registry.create_agent("sage")
        assert registry.get(agent.id) == agent

    def test_create_agent(self):
        registry = AgentRegistry()
        registry.clear()
        agent = registry.create_agent("sage", name="RegTest")
        assert agent.name == "RegTest"
        assert agent.id in registry._agents

    def test_create_invalid_archetype(self):
        registry = AgentRegistry()
        with pytest.raises(ValueError):
            registry.create_agent("nonexistent")

    def test_remove_agent(self):
        registry = AgentRegistry()
        agent = registry.create_agent("sage")
        assert registry.remove(agent.id)
        assert not registry.remove("nonexistent")

    def test_list_agents(self):
        registry = AgentRegistry()
        registry.clear()
        registry.create_agent("sage")
        registry.create_agent("hero")
        registry.create_agent("great_mother")
        assert len(registry.list()) == 3
        assert len(registry.list(PolarityType.MASCULINE)) == 2
        assert len(registry.list(PolarityType.FEMININE)) == 1

    def test_create_default_team(self):
        registry = AgentRegistry()
        registry.clear()
        team = registry.create_default_team()
        assert len(team) == 8  # 3 masculine + 3 feminine + 1 self + 1 trickster

    def test_create_polarity_balanced_team(self):
        registry = AgentRegistry()
        registry.clear()
        team = registry.create_polarity_balanced_team("test task", num_agents=5)
        assert len(team) == 5
