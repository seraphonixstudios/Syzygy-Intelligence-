"""Unit tests for Syzygy Intelligence Agent System."""

import pytest

from app.agents.archetypes import (
    ARCHETYPE_REGISTRY,
    GREAT_MOTHER,
    HERO,
    SAGE,
    SELF,
    SHADOWS,
    Polarity,
    get_archetype,
    get_archetypes_by_polarity,
    get_shadow,
)
from app.agents.base import SyzygyAgent
from app.agents.shadow import IntegrationReport, ShadowAgent
from app.agents.personas import PERSONA_REGISTRY, get_persona
from app.agents.polarity import (
    POLARITY_CONFIGS,
    PolarityType,
    compute_polarity_balance,
    get_dominant_polarity,
    is_balanced,
)
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
        assert len(registry.list_agents()) == 3
        assert len(registry.list_agents(PolarityType.MASCULINE)) == 2
        assert len(registry.list_agents(PolarityType.FEMININE)) == 1

    def test_create_default_team(self):
        registry = AgentRegistry()
        registry.clear()
        team = registry.create_default_team()
        assert len(team) == 5  # 3 masculine + 3 feminine + 1 self + 1 trickster

    def test_create_polarity_balanced_team(self):
        registry = AgentRegistry()
        registry.clear()
        team = registry.create_polarity_balanced_team("test task", num_agents=5)
        assert len(team) == 5


class TestShadowAgentEdgeCases:
    def test_parent_archetype_none(self):
        shadow = ShadowAgent.create("nonexistent", name="Ghost")
        # Force _archetype to None to hit the fallback branch
        shadow._archetype = None
        assert shadow.parent_archetype is None

    def test_polarity_fallback_when_archetype_none(self):
        shadow = ShadowAgent.create("sage")
        shadow._archetype = None
        assert shadow.polarity == PolarityType.UNIFIED

    def test_custom_persona_in_system_prompt(self):
        from app.agents.personas import Persona
        custom = Persona(name="Ghost", archetype="trickster", voice_instructions="Boo!", traits=["spooky"])
        shadow = ShadowAgent.create("sage", custom_persona=custom)
        prompt = shadow.build_system_prompt()
        assert "Ghost" in prompt
        assert "trickster" in prompt

    def test_custom_system_prompt_appended(self):
        shadow = ShadowAgent.create("sage", custom_system_prompt="Custom directive here")
        prompt = shadow.build_system_prompt()
        assert "Custom directive here" in prompt

    def test_integrate_high_alignment(self):
        parent = SyzygyAgent.create("sage")
        shadow = ShadowAgent.create("sage", alignment_score=0.8)
        report = shadow.integrate(parent)
        assert len(report.insights) >= 3
        assert report.alignment_delta == 0.05

    def test_integrate_low_alignment(self):
        parent = SyzygyAgent.create("sage")
        shadow = ShadowAgent.create("sage", alignment_score=0.3)
        report = shadow.integrate(parent)
        assert len(report.insights) >= 2
        assert report.alignment_delta == 0.15

    def test_get_critique_prompt_high_alignment(self):
        shadow = ShadowAgent.create("sage", alignment_score=0.8)
        prompt = shadow.get_critique_prompt("Test task", {"a1": "proposal"})
        assert "incisive" in prompt

    def test_get_critique_prompt_low_alignment(self):
        shadow = ShadowAgent.create("sage", alignment_score=0.3)
        prompt = shadow.get_critique_prompt("Test task", {"a1": "proposal"})
        assert "raw" in prompt


class TestShadowAgent:
    def test_create_shadow_agent(self):
        from app.agents.shadow import ShadowAgent

        shadow = ShadowAgent.create("sage")
        assert shadow.parent_archetype_key == "sage"
        assert shadow.name == "Shadow Sage"
        assert shadow.shadow_archetype is not None
        assert shadow.shadow_archetype.name == "Shadow Sage"
        assert shadow.alignment_score == 0.5

    def test_shadow_polarity_matches_parent(self):
        shadow = ShadowAgent.create("hero")
        assert shadow.polarity == PolarityType.MASCULINE

        shadow = ShadowAgent.create("great_mother")
        assert shadow.polarity == PolarityType.FEMININE

        shadow = ShadowAgent.create("self")
        assert shadow.polarity == PolarityType.UNIFIED

    def test_shadow_system_prompt(self):
        shadow = ShadowAgent.create("sage")
        prompt = shadow.build_system_prompt()
        assert "Shadow Sage" in prompt
        assert "dogmatist" in prompt.lower() or "Dogmatist" in prompt

    def test_shadow_system_prompt_alignment_levels(self):
        low = ShadowAgent.create("sage", alignment_score=0.3)
        low_prompt = low.build_system_prompt()
        assert "unintegrated" in low_prompt

        mid = ShadowAgent.create("sage", alignment_score=0.5)
        mid_prompt = mid.build_system_prompt()
        assert "partially integrated" in mid_prompt

        high = ShadowAgent.create("sage", alignment_score=0.8)
        high_prompt = high.build_system_prompt()
        assert "highly integrated" in high_prompt

    def test_align_increases_score(self):
        shadow = ShadowAgent.create("sage", alignment_score=0.5)
        new_score = shadow.align(0.2)
        assert new_score == 0.7
        assert shadow.alignment_score == 0.7

    def test_align_caps_at_one(self):
        shadow = ShadowAgent.create("sage", alignment_score=0.95)
        new_score = shadow.align(0.1)
        assert new_score == 1.0

    def test_misalign_decreases_score(self):
        shadow = ShadowAgent.create("sage", alignment_score=0.5)
        new_score = shadow.misalign(0.2)
        assert new_score == 0.3

    def test_misalign_floors_at_zero(self):
        shadow = ShadowAgent.create("sage", alignment_score=0.05)
        new_score = shadow.misalign(0.1)
        assert new_score == 0.0

    def test_integrate_produces_report(self):
        parent = SyzygyAgent.create("sage")
        shadow = ShadowAgent.create("sage", alignment_score=0.5)
        report = shadow.integrate(parent)

        assert report.parent_agent_id == parent.id
        assert report.shadow_agent_id == shadow.id
        assert len(report.insights) > 0
        assert report.alignment_delta > 0
        assert report.new_alignment_score > 0.5

    def test_integration_alignment_improves(self):
        parent = SyzygyAgent.create("sage")
        shadow = ShadowAgent.create("sage", alignment_score=0.5)
        before = shadow.alignment_score
        shadow.integrate(parent)
        assert shadow.alignment_score > before

    def test_get_critique_prompt(self):
        shadow = ShadowAgent.create("sage")
        prompt = shadow.get_critique_prompt(
            "Test task", {"agent1": "Some proposal"}
        )
        assert "Shadow Sage" in prompt
        assert "Test task" in prompt
        assert "Some proposal" in prompt

    def test_to_dict(self):
        shadow = ShadowAgent.create("sage", name="Custom Shadow")
        d = shadow.to_dict()
        assert d["name"] == "Custom Shadow"
        assert d["parent_archetype"] == "sage"
        assert d["alignment_score"] == 0.5
        assert "polarity" in d

    def test_create_with_custom_name(self):
        shadow = ShadowAgent.create("hero", name="Custom Shadow Hero")
        assert shadow.name == "Custom Shadow Hero"

    def test_create_all_archetype_shadows(self):
        archetypes = ["hero", "sage", "ruler", "magician", "explorer",
                      "great_mother", "lover", "innocent", "creator", "anima",
                      "self", "hermes", "trickster"]
        for key in archetypes:
            shadow = ShadowAgent.create(key)
            assert shadow.shadow_archetype is not None
            assert shadow.polarity in (
                PolarityType.MASCULINE, PolarityType.FEMININE, PolarityType.UNIFIED
            )


class TestShadowRegistry:
    def test_create_shadow_in_registry(self):
        registry = AgentRegistry()
        registry.clear_shadows()
        shadow = registry.create_shadow_agent("sage")
        assert shadow.id in registry._shadow_agents
        assert registry.get_shadow(shadow.id) is shadow

    def test_list_shadow_agents(self):
        registry = AgentRegistry()
        registry.clear_shadows()
        registry.create_shadow_agent("sage")
        registry.create_shadow_agent("hero")
        all_agents = registry.list_shadow_agents()
        assert len(all_agents) == 2

    def test_list_shadow_agents_by_parent(self):
        registry = AgentRegistry()
        registry.clear_shadows()
        registry.create_shadow_agent("sage")
        registry.create_shadow_agent("sage")
        registry.create_shadow_agent("hero")
        sages = registry.list_shadow_agents("sage")
        assert len(sages) == 2

    def test_remove_shadow_agent(self):
        registry = AgentRegistry()
        registry.clear_shadows()
        shadow = registry.create_shadow_agent("sage")
        assert registry.remove_shadow(shadow.id)
        assert not registry.remove_shadow("nonexistent")

    def test_create_shadow_balanced_team(self):
        registry = AgentRegistry()
        registry.clear_shadows()
        team = registry.create_shadow_balanced_team(3)
        assert len(team) == 3
        # Each should have different alignment scores
        scores = [a.alignment_score for a in team]
        assert len(set(scores)) > 1

    def test_shadow_agent_invalid_archetype(self):
        registry = AgentRegistry()
        with pytest.raises(ValueError):
            registry.create_shadow_agent("nonexistent")


class TestSyzygyAgentEdgeCases:
    def test_agent_no_name_fallback(self):
        agent = SyzygyAgent(archetype_key="hero")
        assert agent.name == "Hero"

    def test_agent_custom_system_prompt(self):
        agent = SyzygyAgent(archetype_key="sage", custom_system_prompt="Custom directive")
        prompt = agent.build_system_prompt()
        assert "Custom directive" in prompt

    def test_agent_polarity_unified_when_no_archetype(self):
        agent = SyzygyAgent(archetype_key="hero")
        agent._archetype = None
        assert agent.polarity == PolarityType.UNIFIED

    def test_agent_persona_property(self):
        agent = SyzygyAgent(archetype_key="sage")
        agent._persona = None
        assert agent.persona is None


class TestPolarityEdgeCases:
    def test_color_hex_masculine(self):
        from app.agents.polarity import POLARITY_CONFIGS, PolarityType
        assert POLARITY_CONFIGS[PolarityType.MASCULINE].color_hex == "#c9a84c"

    def test_color_hex_feminine(self):
        from app.agents.polarity import POLARITY_CONFIGS, PolarityType
        assert POLARITY_CONFIGS[PolarityType.FEMININE].color_hex == "#b0b0c0"

    def test_color_hex_unified(self):
        from app.agents.polarity import POLARITY_CONFIGS, PolarityType
        assert POLARITY_CONFIGS[PolarityType.UNIFIED].color_hex == "#00f0ff"

    def test_get_dominant_polarity_empty(self):
        from app.agents.polarity import get_dominant_polarity
        assert get_dominant_polarity([]) is None

    def test_compute_balance_total_zero(self):
        from app.agents.polarity import compute_polarity_balance
        assert compute_polarity_balance([]) == 0.5
