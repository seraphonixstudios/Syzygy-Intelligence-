"""Syzygy Consensus Engine — multi-round structured debate with polarity integration.

The consensus process:
1. Proposal Phase — agents produce independent proposals tagged by polarity + archetype
2. Critique / Shadow Phase — cross-polarity critique with shadow activation
3. Refinement Phase — agents revise incorporating feedback
4. Evaluation Phase — multi-axis scoring
5. Convergence Check — early stop on high polarity balance / low variance
6. Final Synthesis — Rebis/Self Oracle produces unified output
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.agents.archetypes import get_shadow
from app.agents.base import SyzygyAgent
from app.agents.polarity import PolarityType, compute_polarity_balance
from app.agents.registry import agent_registry
from app.config import settings
from app.consensus.phases import (
    ProposalPhase,
    CritiquePhase,
    RefinementPhase,
    EvaluationPhase,
)
from app.consensus.scoring import ConsensusScorer
from app.consensus.synthesis import SynthesisGenerator
from app.llm.ollama_client import OllamaClient


@dataclass
class ConsensusRound:
    """A single round of the consensus process."""

    round_number: int
    proposals: dict[str, str] = field(default_factory=dict)  # agent_id -> proposal text
    critiques: dict[str, str] = field(default_factory=dict)   # agent_id -> critique text
    refinements: dict[str, str] = field(default_factory=dict) # agent_id -> refined text
    evaluations: dict[str, dict] = field(default_factory=dict) # agent_id -> {score: float, dimensions: dict}
    scores: dict[str, float] = field(default_factory=dict)
    convergence_score: float = 0.0
    polarity_balance: float = 0.5
    synthesis: str = ""
    completed: bool = False


@dataclass
class ConsensusSession:
    """A complete consensus session spanning multiple rounds."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task: str = ""
    agents: list[SyzygyAgent] = field(default_factory=list)
    rounds: list[ConsensusRound] = field(default_factory=list)
    current_round: int = 0
    max_rounds: int = 6
    min_rounds: int = 2
    convergence_threshold: float = 0.85
    variance_threshold: float = 0.1
    final_synthesis: str = ""
    polarity_fusion_report: dict = field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ConsensusEngine:
    """Orchestrates the full consensus process across multiple rounds."""

    def __init__(
        self,
        llm_client: Optional[OllamaClient] = None,
    ):
        self.llm = llm_client or OllamaClient()
        self.scorer = ConsensusScorer()
        self.synthesizer = SynthesisGenerator(self.llm)
        self.active_sessions: dict[str, ConsensusSession] = {}

    async def run_consensus(
        self,
        task: str,
        agents: Optional[list[SyzygyAgent]] = None,
        max_rounds: int = 6,
        min_rounds: int = 2,
        convergence_threshold: float = 0.85,
    ) -> ConsensusSession:
        """Run the full consensus process with all phases."""

        if agents is None:
            agents = agent_registry.create_default_team()

        session = ConsensusSession(
            task=task,
            agents=agents,
            max_rounds=min(max_rounds, settings.max_consensus_rounds),
            min_rounds=min_rounds,
            convergence_threshold=convergence_threshold,
            variance_threshold=settings.variance_threshold,
        )
        self.active_sessions[session.id] = session
        session.status = "running"

        for round_num in range(1, max_rounds + 1):
            round_data = ConsensusRound(round_number=round_num)
            session.rounds.append(round_data)
            session.current_round = round_num

            # Phase 1: Proposals
            await self._proposal_phase(session, round_data)

            # Phase 2: Critique with Shadow activation
            if round_num >= 2 or len(agents) >= 3:
                await self._critique_phase(session, round_data)

            # Phase 3: Refinement
            if round_num >= 2:
                await self._refinement_phase(session, round_data)

            # Phase 4: Evaluation
            await self._evaluation_phase(session, round_data)

            # Phase 5: Convergence check
            converged = await self._convergence_check(session, round_data)

            if converged and round_num >= min_rounds:
                round_data.completed = True
                break

            round_data.completed = True

        # Final Synthesis
        final_round = session.rounds[-1]
        session.final_synthesis = await self.synthesizer.generate_synthesis(
            task=task,
            proposals=final_round.proposals,
            critiques=final_round.critiques,
            refinements=final_round.refinements,
            evaluations=final_round.evaluations,
            agents=agents,
        )

        # Polarity Fusion Report
        session.polarity_fusion_report = self._generate_fusion_report(session)

        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        return session

    async def _proposal_phase(self, session: ConsensusSession, round_data: ConsensusRound):
        """Phase 1: Each agent produces an independent proposal."""
        tasks = []
        for agent in session.agents:
            context = self._build_proposal_context(session, round_data, agent)
            tasks.append(self._agent_propose(agent, session.task, context))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for agent, result in zip(session.agents, results):
            if isinstance(result, Exception):
                round_data.proposals[agent.id] = f"[Error generating proposal: {result}]"
            else:
                round_data.proposals[agent.id] = result

    async def _critique_phase(self, session: ConsensusSession, round_data: ConsensusRound):
        """Phase 2: Cross-polarity critique with shadow activation."""
        tasks = []
        prev_round = session.rounds[-2] if len(session.rounds) >= 2 else None

        for agent in session.agents:
            # Find proposals from agents of opposite polarity for critique
            targets = [
                a for a in session.agents
                if a.id != agent.id and a.polarity != agent.polarity
            ]
            if not targets:
                targets = [a for a in session.agents if a.id != agent.id]

            target_proposals = {
                t.id: round_data.proposals.get(t.id, "")
                for t in targets[:2]
            }

            # Activate shadow for deeper critique
            agent.activate_shadow()
            tasks.append(
                self._agent_critique(
                    agent,
                    session.task,
                    target_proposals,
                    prev_round.critiques if prev_round else None,
                )
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for agent, result in zip(session.agents, results):
            if isinstance(result, Exception):
                round_data.critiques[agent.id] = f"[Error during critique: {result}]"
            else:
                round_data.critiques[agent.id] = result
            agent.deactivate_shadow()

    async def _refinement_phase(self, session: ConsensusSession, round_data: ConsensusRound):
        """Phase 3: Agents revise proposals based on received critiques."""
        tasks = []
        for agent in session.agents:
            # Collect critiques directed at this agent
            received_critiques = {
                critic_id: critique
                for critic_id, critique in round_data.critiques.items()
                if critic_id != agent.id
            }
            tasks.append(
                self._agent_refine(
                    agent,
                    session.task,
                    round_data.proposals.get(agent.id, ""),
                    received_critiques,
                )
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for agent, result in zip(session.agents, results):
            if isinstance(result, Exception):
                round_data.refinements[agent.id] = round_data.proposals.get(agent.id, "")
            else:
                round_data.refinements[agent.id] = result

    async def _evaluation_phase(self, session: ConsensusSession, round_data: ConsensusRound):
        """Phase 4: Multi-axis scoring of all refinements/proposals."""
        contents = round_data.refinements or round_data.proposals
        evaluations = await self.scorer.evaluate_all(
            session.task,
            contents,
            session.agents,
            self.llm,
        )
        round_data.evaluations = evaluations
        round_data.scores = {
            agent_id: ev["overall"]
            for agent_id, ev in evaluations.items()
        }

        # Compute polarity balance
        polarities = [a.polarity for a in session.agents]
        round_data.polarity_balance = compute_polarity_balance(polarities)

    async def _convergence_check(
        self, session: ConsensusSession, round_data: ConsensusRound
    ) -> bool:
        """Phase 5: Check for convergence based on score variance and stability."""
        scores = list(round_data.scores.values())
        if len(scores) < 2:
            return False

        # Variance check
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)

        # Polarity balance check
        round_data.convergence_score = 1.0 - min(variance / 5.0, 1.0)

        # Converged if scores are stable and polarity is balanced
        high_agreement = round_data.convergence_score >= session.convergence_threshold
        low_variance = variance <= session.variance_threshold

        return high_agreement or low_variance

    def _generate_fusion_report(self, session: ConsensusSession) -> dict:
        """Generate polarity fusion report with individuation notes."""
        masc_contributions = []
        fem_contributions = []
        unified_contributions = []

        for agent in session.agents:
            if agent.polarity == PolarityType.MASCULINE:
                masc_contributions.append(agent.name)
            elif agent.polarity == PolarityType.FEMININE:
                fem_contributions.append(agent.name)
            else:
                unified_contributions.append(agent.name)

        return {
            "masculine_forces": masc_contributions,
            "feminine_forces": fem_contributions,
            "unified_perspective": unified_contributions,
            "polarity_balance_scores": [
                r.polarity_balance for r in session.rounds if r.polarity_balance
            ],
            "rounds_completed": session.current_round,
            "individuation_notes": (
                f"The {' and '.join(fem_contributions) if fem_contributions else 'feminine'} "
                f"and {' and '.join(masc_contributions) if masc_contributions else 'masculine'} "
                f"perspectives were integrated through {session.current_round} rounds of "
                f"structured dialogue. {len(unified_contributions)} unified agent(s) "
                f"facilitated the synthesis."
            ),
        }

    async def _agent_propose(self, agent: SyzygyAgent, task: str, context: str) -> str:
        prompt = (
            f"As a {agent.archetype.name} agent ({agent.polarity.value} polarity), "
            f"propose your approach to the following task:\n\n{task}\n\n"
            f"{context}\n\n"
            f"Frame your proposal through the lens of your archetype's strengths: "
            f"{', '.join(agent.archetype.strengths)}."
        )
        return await self.llm.generate(prompt, system=agent.build_system_prompt())

    async def _agent_critique(
        self,
        agent: SyzygyAgent,
        task: str,
        target_proposals: dict[str, str],
        previous_critiques: Optional[dict[str, str]] = None,
    ) -> str:
        shadow = agent.shadow
        targets_text = "\n\n".join(
            f"[{aid}]: {prop}" for aid, prop in target_proposals.items()
        )

        shadow_prompt = ""
        if shadow:
            shadow_prompt = (
                f"\n\nYour shadow ({shadow.name}) is active. "
                f"{shadow.activation_prompt} "
                f"Allow this critical perspective to inform but not dominate your analysis."
            )

        prompt = (
            f"Review the following proposals for the task:\n\n{task}\n\n"
            f"Proposals to critique:\n{targets_text}\n"
            f"{shadow_prompt}\n\n"
            f"Provide constructive cross-polarity critique. Identify blind spots, "
            f"unexamined assumptions, and opportunities for integration."
        )
        return await self.llm.generate(prompt, system=agent.build_system_prompt())

    async def _agent_refine(
        self,
        agent: SyzygyAgent,
        task: str,
        own_proposal: str,
        critiques: dict[str, str],
    ) -> str:
        critiques_text = "\n\n".join(
            f"Critique from {cid}: {c}" for cid, c in critiques.items()
        )

        prompt = (
            f"Your original proposal:\n{own_proposal}\n\n"
            f"Critiques received:\n{critiques_text}\n\n"
            f"Revise your proposal, incorporating the valid feedback "
            f"while maintaining your archetypal perspective as {agent.archetype.name}. "
            f"Explain what you changed and why."
        )
        return await self.llm.generate(prompt, system=agent.build_system_prompt())

    def _build_proposal_context(
        self,
        session: ConsensusSession,
        round_data: ConsensusRound,
        agent: SyzygyAgent,
    ) -> str:
        """Build context from previous rounds for the proposal phase."""
        if len(session.rounds) <= 1:
            return "This is the first round. Provide your initial perspective."

        prev_round = session.rounds[-2]
        context_parts = ["Previous round context:"]

        if prev_round.synthesis:
            context_parts.append(f"Previous synthesis: {prev_round.synthesis[:500]}")

        if prev_round.critiques.get(agent.id):
            context_parts.append(
                f"Your previous critique: {prev_round.critiques[agent.id][:300]}"
            )

        return "\n".join(context_parts)


__all__ = [
    "ConsensusEngine",
    "ConsensusSession",
    "ConsensusRound",
]
