"""CI Piper workflow — generate CI/CD pipeline configs for GitHub Actions, GitLab CI, Jenkins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.logging_setup import logger


@dataclass
class CiPiperWorkflow:
    """Generate CI/CD pipeline configurations with caching, matrix builds, and deploy stages."""

    name: str = "ci_piper"
    description: str = "CI/CD pipeline configs — GitHub Actions, GitLab CI, Jenkins with matrix builds and deploy stages"
    required_capabilities: list[str] = field(
        default_factory=lambda: ["ci_cd_design", "config_generation", "deployment_planning"]
    )
    llm: OllamaClient | None = None

    def __post_init__(self):
        if self.llm is None:
            self.llm = OllamaClient()

    async def analyze_project(self, project_description: str, language: str, framework: str) -> dict[str, Any]:
        prompt = (
            f"Analyze the following project for CI/CD pipeline requirements:\n\n"
            f"Description: {project_description[:1500]}\n"
            f"Language: {language}\n"
            f"Framework: {framework}\n\n"
            f"Determine:\n"
            f"1. Build system and commands needed\n"
            f"2. Test framework and commands\n"
            f"3. Linting/formatting tools\n"
            f"4. Artifact types and paths\n"
            f"5. Docker build requirements\n"
            f"6. Deployment targets and strategies\n"
            f"7. Caching opportunities\n"
            f"8. Matrix dimensions (OS, versions)"
        )
        analysis = await self.llm.generate(prompt, temperature=0.3)
        return {"analysis": analysis, "language": language, "framework": framework}

    async def generate_github_actions(self, project_description: str, analysis: dict) -> dict[str, Any]:
        prompt = (
            f"Generate a complete GitHub Actions workflow YAML for:\n\n"
            f"Project: {project_description[:1000]}\n\n"
            f"Analysis:\n{analysis.get('analysis', '')[:2000]}\n\n"
            f"Include:\n"
            f"1. Multiple trigger events (push, PR, schedule, workflow_dispatch)\n"
            f"2. Matrix builds for multiple OS/node/python versions\n"
            f"3. Dependency caching (npm/pip/maven)\n"
            f"4. Lint → Test → Build → Publish stages\n"
            f"5. Docker build and push\n"
            f"6. Deploy to staging/production\n"
            f"7. Artifact uploads\n"
            f"8. Concurrency and timeout settings\n"
            f"Return complete YAML with comments explaining each section."
        )
        config = await self.llm.generate(prompt, temperature=0.3)
        return {"config": config, "platform": "github_actions"}

    async def generate_gitlab_ci(self, project_description: str, analysis: dict) -> dict[str, Any]:
        prompt = (
            f"Generate a complete GitLab CI .gitlab-ci.yml for:\n\n"
            f"Project: {project_description[:1000]}\n\n"
            f"Analysis:\n{analysis.get('analysis', '')[:2000]}\n\n"
            f"Include:\n"
            f"1. Stages: .pre, lint, test, build, deploy\n"
            f"2. Parallel matrix jobs\n"
            f"3. Cache configuration for dependencies\n"
            f"4. Artifacts between stages\n"
            f"5. Environment-specific variables\n"
            f"6. Rules and conditions (merge request, tags, branches)\n"
            f"7. Dependencies between jobs\n"
            f"8. Deploy jobs with manual approval gate\n"
            f"Return complete YAML."
        )
        config = await self.llm.generate(prompt, temperature=0.3)
        return {"config": config, "platform": "gitlab_ci"}

    async def generate_jenkins(self, project_description: str, analysis: dict) -> dict[str, Any]:
        prompt = (
            f"Generate a Jenkins declarative pipeline (Jenkinsfile) for:\n\n"
            f"Project: {project_description[:1000]}\n\n"
            f"Analysis:\n{analysis.get('analysis', '')[:2000]}\n\n"
            f"Include:\n"
            f"1. agent and tools declarations\n"
            f"2. Stages: Checkout → Lint → Test → Build → Docker → Deploy\n"
            f"3. Parallel stages where possible\n"
            f"4. post actions (success, failure, always)\n"
            f"5. Credential and secret handling\n"
            f"6. Notification integrations (Slack, email)\n"
            f"7. Cleanup and workspace management\n"
            f"Return complete Jenkinsfile."
        )
        config = await self.llm.generate(prompt, temperature=0.3)
        return {"config": config, "platform": "jenkins"}

    async def execute(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        ctx = context or {}
        project_description = ctx.get("description", task)
        language = ctx.get("language", "python")
        framework = ctx.get("framework", "")
        platforms = ctx.get("platforms", ["github_actions"])

        logger.info("CI Piper workflow started", language=language, platforms=platforms)
        analysis = await self.analyze_project(project_description, language, framework)

        configs = []
        if "github_actions" in platforms:
            configs.append(await self.generate_github_actions(project_description, analysis))
        if "gitlab_ci" in platforms:
            configs.append(await self.generate_gitlab_ci(project_description, analysis))
        if "jenkins" in platforms:
            configs.append(await self.generate_jenkins(project_description, analysis))

        result = {
            "task": task,
            "language": language,
            "framework": framework,
            "analysis": analysis,
            "configs": configs,
            "status": "completed",
        }
        logger.info("CI Piper workflow completed", config_count=len(configs))
        return result


CI_PIPER_WORKFLOW = CiPiperWorkflow()
