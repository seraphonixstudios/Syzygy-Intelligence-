"""Interview Coach workflow — role-specific questions, practice answer evaluation, scoring feedback."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class InterviewCoachWorkflow:
    """Generate role-specific interview questions, evaluate practice answers, score with feedback."""

    name: str = "interview_coach"
    description: str = "Role-specific interview questions, practice answer evaluation, and scoring feedback"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["question_generation", "answer_evaluation", "feedback_scoring"]
    )
    llm: Optional[OllamaClient] = None

    def __post_init__(self):
        if self.llm is None:
            self.llm = OllamaClient()

    async def generate_questions(self, role: str, difficulty: str, count: int) -> dict[str, Any]:
        prompt = (
            f"Generate {count} {difficulty}-level interview questions for a {role} position.\n\n"
            f"For each question provide:\n"
            f"1. The question text\n"
            f"2. The category (technical / behavioral / system-design / situational)\n"
            f"3. What the interviewer is looking for in a good answer\n"
            f"4. Ideal answer key points\n\n"
            f"Cover a range of topics relevant to {role}."
        )
        result = await self.llm.generate(prompt, temperature=0.4)
        return {"questions": result, "role": role, "difficulty": difficulty, "count": count}

    async def evaluate_answer(self, question: str, answer: str, role: str) -> dict[str, Any]:
        prompt = (
            f"Evaluate the following interview answer for a {role} position:\n\n"
            f"Question: {question}\n\n"
            f"Candidate Answer: {answer}\n\n"
            f"Score each dimension (1-10):\n"
            f"1. Correctness — is the answer technically accurate?\n"
            f"2. Completeness — does it cover all important aspects?\n"
            f"3. Structure — is it well-organized and clear?\n"
            f"4. Depth — does it show deep understanding or just surface-level?\n"
            f"5. Communication — is it concise and well-expressed?\n\n"
            f"Provide overall score, strengths, weaknesses, and specific improvement suggestions."
        )
        result = await self.llm.generate(prompt, temperature=0.3)
        return {"evaluation": result, "question": question}

    async def generate_feedback(self, evaluations: list[dict]) -> str:
        combined = "\n\n".join(
            f"Q: {e.get('question', '')}\nEvaluation: {e.get('evaluation', '')}"
            for e in evaluations
        )
        prompt = (
            f"Based on the following interview answer evaluations, generate comprehensive feedback:\n\n"
            f"{combined}\n\n"
            f"Provide:\n"
            f"1. Overall performance summary\n"
            f"2. Key strengths (top 3)\n"
            f"3. Areas for improvement (top 3)\n"
            f"4. Recommended preparation resources\n"
            f"5. Estimated readiness level (Strong / Good / Needs Work / Weak)"
        )
        return await self.llm.generate(prompt, temperature=0.3)

    async def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        ctx = context or {}
        role = ctx.get("role", task)
        difficulty = ctx.get("difficulty", "medium")
        count = ctx.get("question_count", 5)
        answers = ctx.get("answers", [])

        logger.info(f"Interview Coach workflow started", role=role, difficulty=difficulty)
        questions = await self.generate_questions(role, difficulty, count)

        evaluations = []
        if answers:
            for item in answers:
                q = item.get("question", "")
                a = item.get("answer", "")
                if q and a:
                    ev = await self.evaluate_answer(q, a, role)
                    evaluations.append(ev)

        feedback = None
        if evaluations:
            feedback = await self.generate_feedback(evaluations)

        result = {
            "task": task,
            "role": role,
            "difficulty": difficulty,
            "questions": questions,
            "evaluations": evaluations,
            "feedback": feedback,
            "status": "completed",
        }
        logger.info(f"Interview Coach workflow completed")
        return result


INTERVIEW_COACH_WORKFLOW = InterviewCoachWorkflow()
