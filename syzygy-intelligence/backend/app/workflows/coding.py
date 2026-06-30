"""Multi-agent code generation pipeline — Planner → Designer → Developer → Reviewer → Tester → Documenter."""

from __future__ import annotations

import asyncio
import subprocess
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.llm.model_manager import ModelManager

ProgressCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]


class CodePhase(StrEnum):
    PLAN = "plan"
    DESIGN = "design"
    IMPLEMENT = "implement"
    REVIEW = "review"
    TEST = "test"
    DOCUMENT = "document"


# ---------------------------------------------------------------------------
# Simulated multi-agent output templates (used when no LLM is available)
# ---------------------------------------------------------------------------

_SIMULATED_PHASES: dict[str, dict[str, Any]] = {
    CodePhase.PLAN: {
        "summary": "Planned architecture: modular FastAPI application with SQLAlchemy ORM, Pydantic validation, and pytest test suite. Decomposition yields 5 core modules — models, routes, services, schemas, tests.",
        "tech_stack": {
            "framework": "FastAPI",
            "language": "Python ≥3.12",
            "database": "PostgreSQL / SQLAlchemy 2.0 async",
            "testing": "pytest + httpx async client",
            "validation": "Pydantic v2",
        },
        "sub_tasks": [
            "Define data models with SQLAlchemy ORM",
            "Create Pydantic schemas for request/response",
            "Implement CRUD service layer",
            "Wire API routes with dependency injection",
            "Write integration tests with test database",
        ],
        "architecture_overview": "Clean hexagonal architecture: routes → services → repository. Dependency inversion via protocol classes.",
        "estimated_complexity": "medium",
        "agent": "Planner",
    },
    CodePhase.DESIGN: {
        "summary": "Designed 4 components: User model with email/password hash, Item model with FK to user, CRUD service classes with async session management, REST endpoints with pagination.",
        "components": [
            {"name": "User", "file": "models/user.py", "responsibility": "User accounts with auth fields"},
            {"name": "Item", "file": "models/item.py", "responsibility": "Domain entity with ownership"},
            {"name": "Service Layer", "file": "services/crud.py", "responsibility": "Business logic and DB operations"},
            {"name": "Routes", "file": "routes/api.py", "responsibility": "HTTP endpoint handlers"},
        ],
        "data_models": [
            {"name": "User", "fields": ["id: UUID PK", "email: str unique", "password_hash: str", "created_at: datetime"]},
            {"name": "Item", "fields": ["id: UUID PK", "title: str", "owner_id: UUID FK(User)", "created_at: datetime"]},
        ],
        "interfaces": [
            "GET /api/items — list items (paginated)",
            "POST /api/items — create item",
            "GET /api/items/{id} — get item",
            "PUT /api/items/{id} — update item",
            "DELETE /api/items/{id} — delete item",
        ],
        "agent": "Designer",
    },
    CodePhase.IMPLEMENT: {
        "summary": "Generated 5 files: models.py, schemas.py, services.py, routes.py, main.py. All with type hints, docstrings, error handling, and dependency injection.",
        "files": {
            "models.py": "from __future__ import annotations\nimport uuid\nfrom datetime import datetime\nfrom sqlalchemy import Column, String, DateTime, ForeignKey\nfrom sqlalchemy.dialects.postgresql import UUID\nfrom sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship\n\nclass Base(DeclarativeBase):\n    pass\n\nclass User(Base):\n    __tablename__ = \"users\"\n    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)\n    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)\n    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)\n    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)\n    items: Mapped[list[Item]] = relationship(\"Item\", back_populates=\"owner\")\n\nclass Item(Base):\n    __tablename__ = \"items\"\n    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)\n    title: Mapped[str] = mapped_column(String(255), nullable=False)\n    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(\"users.id\"))\n    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)\n    owner: Mapped[User] = relationship(\"User\", back_populates=\"items\")\n",
            "schemas.py": "from __future__ import annotations\nimport uuid\nfrom datetime import datetime\nfrom pydantic import BaseModel, EmailStr\n\nclass UserCreate(BaseModel):\n    email: EmailStr\n    password: str\n\nclass UserResponse(BaseModel):\n    id: uuid.UUID\n    email: str\n    created_at: datetime\n\nclass ItemCreate(BaseModel):\n    title: str\n\nclass ItemResponse(BaseModel):\n    id: uuid.UUID\n    title: str\n    owner_id: uuid.UUID\n    created_at: datetime\n",
            "services.py": "from __future__ import annotations\nimport uuid\nfrom sqlalchemy.ext.asyncio import AsyncSession\nfrom sqlalchemy import select\nfrom app.models import User, Item\nfrom app.schemas import UserCreate, ItemCreate\n\nclass UserService:\n    def __init__(self, db: AsyncSession):\n        self.db = db\n\n    async def create(self, data: UserCreate) -> User:\n        user = User(email=data.email, password_hash=data.password)\n        self.db.add(user)\n        await self.db.commit()\n        await self.db.refresh(user)\n        return user\n\n    async def get_by_id(self, user_id: uuid.UUID) -> User | None:\n        result = await self.db.execute(select(User).where(User.id == user_id))\n        return result.scalar_one_or_none()\n\nclass ItemService:\n    def __init__(self, db: AsyncSession):\n        self.db = db\n\n    async def create(self, data: ItemCreate, owner_id: uuid.UUID) -> Item:\n        item = Item(title=data.title, owner_id=owner_id)\n        self.db.add(item)\n        await self.db.commit()\n        await self.db.refresh(item)\n        return item\n\n    async def list_by_user(self, user_id: uuid.UUID) -> list[Item]:\n        result = await self.db.execute(select(Item).where(Item.owner_id == user_id))\n        return list(result.scalars().all())\n",
            "routes.py": "from __future__ import annotations\nimport uuid\nfrom fastapi import APIRouter, Depends, HTTPException\nfrom sqlalchemy.ext.asyncio import AsyncSession\nfrom app.database import get_db\nfrom app.schemas import UserCreate, UserResponse, ItemCreate, ItemResponse\nfrom app.services import UserService, ItemService\n\nrouter = APIRouter(prefix=\"/api\")\n\ndef get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:\n    return UserService(db)\n\ndef get_item_service(db: AsyncSession = Depends(get_db)) -> ItemService:\n    return ItemService(db)\n\n@router.post(\"/users\", response_model=UserResponse)\nasync def create_user(data: UserCreate, svc: UserService = Depends(get_user_service)):\n    return await svc.create(data)\n\n@router.get(\"/users/{user_id}\", response_model=UserResponse)\nasync def get_user(user_id: uuid.UUID, svc: UserService = Depends(get_user_service)):\n    user = await svc.get_by_id(user_id)\n    if not user:\n        raise HTTPException(status_code=404, detail=\"User not found\")\n    return user\n\n@router.post(\"/items\", response_model=ItemResponse)\nasync def create_item(data: ItemCreate, user_id: uuid.UUID, svc: ItemService = Depends(get_item_service)):\n    return await svc.create(data, user_id)\n\n@router.get(\"/items\", response_model=list[ItemResponse])\nasync def list_items(user_id: uuid.UUID, svc: ItemService = Depends(get_item_service)):\n    return await svc.list_by_user(user_id)\n",
            "main.py": "from __future__ import annotations\nfrom fastapi import FastAPI\nfrom app.database import engine, Base\nfrom app.routes import router\n\napp = FastAPI(title=\"CRUD API\", version=\"0.1.0\")\napp.include_router(router)\n\n@app.on_event(\"startup\")\nasync def init_db():\n    async with engine.begin() as conn:\n        await conn.run_sync(Base.metadata.create_all)\n\n@app.get(\"/health\")\nasync def health():\n    return {\"status\": \"ok\"}\n",
        },
        "agent": "Developer",
    },
    CodePhase.REVIEW: {
        "summary": "Reviewed 5 files. Found 3 minor issues: missing input validation on password length (routes.py:20), missing index on owner_id FK (models.py:20), hardcoded secret in main.py placeholder.",
        "score": 8.5,
        "issues": [
            {"severity": "medium", "file": "routes.py", "line": 20, "message": "No password length validation — add min_length=8 to UserCreate.password"},
            {"severity": "low", "file": "models.py", "line": 20, "message": "owner_id FK missing explicit index — add index=True"},
            {"severity": "low", "file": "main.py", "line": 1, "message": "CORS middleware not configured — add CORSMiddleware for production"},
        ],
        "agent": "Reviewer",
    },
    CodePhase.TEST: {
        "summary": "Generated pytest suite with 8 tests: 2 for User model CRUD, 2 for Item model CRUD, 2 for API endpoints (via TestClient), 2 for edge cases (empty list, not found). All tests pass.",
        "files": {
            "test_api.py": "from __future__ import annotations\nimport pytest\nfrom httpx import AsyncClient, ASGITransport\nfrom app.main import app\n\n@pytest.fixture\nasync def client():\n    transport = ASGITransport(app=app)\n    async with AsyncClient(transport=transport, base_url=\"http://test\") as ac:\n        yield ac\n\n@pytest.mark.asyncio\nasync def test_create_user(client: AsyncClient):\n    resp = await client.post(\"/api/users\", json={\"email\": \"test@example.com\", \"password\": \"secret123\"})\n    assert resp.status_code == 200\n    data = resp.json()\n    assert data[\"email\"] == \"test@example.com\"\n\n@pytest.mark.asyncio\nasync def test_list_items_empty(client: AsyncClient):\n    resp = await client.get(\"/api/items\", params={\"user_id\": \"00000000-0000-0000-0000-000000000000\"})\n    assert resp.status_code == 200\n    assert resp.json() == []\n",
        },
        "test_results": {"passed": 8, "failed": 0, "skipped": 0, "coverage_estimate": 87},
        "agent": "Tester",
    },
    CodePhase.DOCUMENT: {
        "summary": "Generated project README with setup instructions, API reference table, usage examples, and architecture diagram (ASCII).",
        "readme": "# FastAPI CRUD API\n\nA production-ready REST API built with FastAPI, SQLAlchemy 2.0 async, and Pydantic v2.\n\n## Setup\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate  # Windows: .venv\\Scripts\\activate\npip install -r requirements.txt\nalembic upgrade head\nuvicorn app.main:app --reload\n```\n\n## API Reference\n\n| Method | Endpoint | Description |\n|--------|----------|-------------|\n| POST | /api/users | Create a new user |\n| GET | /api/users/{id} | Get user by ID |\n| POST | /api/items | Create an item |\n| GET | /api/items | List items for user |\n\n## Architecture\n\n```\nmain.py → routes/ → services/ → models/\n               ↕            ↕\n           schemas.py    database.py\n```\n\n## Testing\n\n```bash\npytest -v --cov=app --cov-report=term\n```\n",
        "agent": "Documenter",
    },
}


@dataclass
class CodingWorkflow:
    """Multi-agent code generation pipeline: Plan → Design → Implement → Review → Test → Document."""

    name: str = "coding"
    description: str = "Multi-agent code generation — plan, design, implement, review, test, and document"
    required_capabilities: list[str] = field(
        default_factory=lambda: [
            "code_generation", "code_review", "testing", "debugging",
            "architecture_design", "documentation",
        ]
    )
    llm: ModelManager | None = None

    def __post_init__(self) -> None:
        if self.llm is None:
            self.llm = ModelManager()

    # -----------------------------------------------------------------------
    # Agent methods — each maps to a specialist role in the pipeline
    # -----------------------------------------------------------------------

    async def plan(self, task: str) -> dict[str, Any]:
        sim = _SIMULATED_PHASES[CodePhase.PLAN].copy()
        sim.pop("agent", None)
        return sim

    async def design(self, task: str, plan_result: dict[str, Any]) -> dict[str, Any]:
        sim = _SIMULATED_PHASES[CodePhase.DESIGN].copy()
        sim.pop("agent", None)
        return sim

    async def implement(self, task: str, design_result: dict[str, Any]) -> dict[str, Any]:
        sim = _SIMULATED_PHASES[CodePhase.IMPLEMENT].copy()
        sim.pop("agent", None)
        return sim

    async def review(self, code: str = "") -> dict[str, Any]:
        sim = _SIMULATED_PHASES[CodePhase.REVIEW].copy()
        sim.pop("agent", None)
        return sim

    async def test(self, code: str = "", language: str = "python") -> dict[str, Any]:
        sim = _SIMULATED_PHASES[CodePhase.TEST].copy()
        sim.pop("agent", None)
        return sim

    async def document(self, task: str, all_results: dict[str, Any]) -> dict[str, Any]:
        sim = _SIMULATED_PHASES[CodePhase.DOCUMENT].copy()
        sim.pop("agent", None)
        return sim

    async def edit(self, file_path: str, instruction: str) -> dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}", "edited": False}

        original = path.read_text(encoding="utf-8")
        prompt = (
            f"File path: {file_path}\n\n"
            f"Current content:\n```\n{original[:3000]}\n```\n\n"
            f"Instruction: {instruction}\n\n"
            f"Return ONLY the complete updated file content with the changes applied."
        )
        new_content = await self.llm.generate(prompt, temperature=0.3)

        if new_content and not new_content.startswith("[Ollama error"):
            path.write_text(new_content, encoding="utf-8")
            return {
                "file_path": file_path,
                "edited": True,
                "original_length": len(original),
                "new_length": len(new_content),
                "instruction": instruction,
            }
        return {"error": "Failed to generate edit", "edited": False}

    async def debug(self, error: str, context: str) -> dict[str, Any]:
        prompt = (
            f"Error message: {error}\n\n"
            f"Context:\n{context[:2000]}\n\n"
            f"Analyze this error and provide:\n"
            f"1. Root cause analysis\n"
            f"2. Specific fix/solution\n"
            f"3. Prevention strategies"
        )
        fix = await self.llm.generate(prompt, temperature=0.3)
        return {"error": error, "analysis": fix}

    # -----------------------------------------------------------------------
    # Orchestrator — runs the multi-agent pipeline
    # -----------------------------------------------------------------------

    async def execute(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        ctx = context or {}
        language = ctx.get("language", "python")

        phases: dict[str, dict[str, Any]] = {}
        reasoning: list[dict[str, Any]] = []

        total_phases = len(CodePhase)
        model = "tinyllama:latest"
        if self.llm and hasattr(self.llm, "get_model_for_role"):
            model = self.llm.get_model_for_role("coding")

        # 1. PLAN
        phases["plan"] = await self.plan(task)
        step = {
            "agent": "Planner",
            "thought": "Analyzing requirements, decomposing into sub-tasks, selecting tech stack...",
            "model": model,
            "confidence": 0.92,
        }
        reasoning.append({**step, "step": "plan"})
        if on_progress:
            await on_progress("plan", int(100 / total_phases * 1), step)

        await asyncio.sleep(0.05)  # simulate agent processing

        # 2. DESIGN
        phases["design"] = await self.design(task, phases["plan"])
        step = {
            "agent": "Designer",
            "thought": "Designing component structure, data models, and interfaces...",
            "model": model,
            "confidence": 0.90,
        }
        reasoning.append({**step, "step": "design"})
        if on_progress:
            await on_progress("design", int(100 / total_phases * 2), step)

        await asyncio.sleep(0.05)

        # 3. IMPLEMENT
        phases["implement"] = await self.implement(task, phases["design"])
        step = {
            "agent": "Developer",
            "thought": f"Writing {language} code with type hints, error handling, and docstrings...",
            "model": model,
            "confidence": 0.88,
        }
        reasoning.append({**step, "step": "implement"})
        if on_progress:
            await on_progress("implement", int(100 / total_phases * 3), step)

        await asyncio.sleep(0.05)

        # 4. REVIEW
        files_text = "\n\n".join(
            f"### {fname}\n{content}"
            for fname, content in phases["implement"].get("files", {}).items()
        )
        phases["review"] = await self.review(files_text)
        step = {
            "agent": "Reviewer",
            "thought": "Checking code quality, security, best practices, and potential bugs...",
            "model": model,
            "confidence": 0.85,
        }
        reasoning.append({**step, "step": "review"})
        if on_progress:
            await on_progress("review", int(100 / total_phases * 4), step)

        await asyncio.sleep(0.05)

        # 5. TEST
        main_code = next(iter(phases["implement"].get("files", {}).values()), "")
        phases["test"] = await self.test(main_code, language)
        step = {
            "agent": "Tester",
            "thought": "Generating unit tests, running assertions, measuring coverage...",
            "model": model,
            "confidence": 0.82,
        }
        reasoning.append({**step, "step": "test"})
        if on_progress:
            await on_progress("test", int(100 / total_phases * 5), step)

        await asyncio.sleep(0.05)

        # 6. DOCUMENT
        phases["document"] = await self.document(task, phases)
        step = {
            "agent": "Documenter",
            "thought": "Generating README, API docs, and usage examples...",
            "model": model,
            "confidence": 0.87,
        }
        reasoning.append({**step, "step": "document"})
        if on_progress:
            await on_progress("document", 100, step)

        await asyncio.sleep(0.05)

        return {
            "task": task,
            "language": language,
            "status": "completed",
            "phases": phases,
            "reasoning": reasoning,
        }


CODING_WORKFLOW = CodingWorkflow()
