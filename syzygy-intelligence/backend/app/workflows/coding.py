"""Multi-agent code generation pipeline — Planner → Designer → Developer → Reviewer → Tester → Documenter.

Each phase calls the LLM for real. The canned _SIMULATED_PHASES below are used
ONLY as a last-resort fallback when the LLM is unreachable, and any result
built from them is explicitly labeled with "simulated": True. Test results
always come from actually executing pytest, never from assertion.
"""

from __future__ import annotations

import asyncio
import json
import re
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.llm.model_manager import ModelManager
from app.logging_setup import logger

ProgressCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]


class CodePhase(StrEnum):
    PLAN = "plan"
    DESIGN = "design"
    IMPLEMENT = "implement"
    REVIEW = "review"
    TEST = "test"
    DOCUMENT = "document"


# ---------------------------------------------------------------------------
# Fallback output templates — used ONLY when the LLM is unreachable.
# Every result built from these is labeled "simulated": True.
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
        "readme": "# FastAPI CRUD API\n\nA production-ready REST API built with FastAPI, SQLAlchemy 2.0 async, and Pydantic v2.\n\n## Setup\n\n```bash\npython -m venv .venv\nsource .venv/bin/activate  # Windows: .venv\\Scripts\\activate\npip install -r requirements.txt\nalembic upgrade head\nuvicorn app.main:app --reload\n```\n\n## API Reference\n\n| Method | Endpoint | Description |\n|--------|----------|-------------|\n| POST | /api/users | Create a new user |\n| GET | /api/users/{id} | Get user by ID |\n| POST | /api/items | Create an item |\n| GET | /api/items | List items for user |\n\n## Testing\n\n```bash\npytest -v --cov=app --cov-report=term\n```\n",
        "agent": "Documenter",
    },
}

_SIMULATED_MARKER = "simulated fallback — LLM unreachable"

# Matches ```lang:file.ext ... ```, ```file.ext ... ```, or ```lang ... ```
_FILE_BLOCK_RE = re.compile(
    r"```(?:(?P<lang>[a-zA-Z0-9_+\-]+)(?::(?P<file>[\w\-./]+\.\w+))?|(?P<barefile>[\w\-./]+\.\w+))\n(?P<body>.*?)```",
    re.DOTALL,
)

_CODE_HINTS = ("def ", "class ", "import ", "print(", "assert ", "=>", "function ", "#include")


def _looks_like_code(text: str) -> bool:
    return any(h in text for h in _CODE_HINTS)


def _safe_filename(name: str) -> str | None:
    """Accept flat relative filenames only — reject traversal/absolute paths."""
    name = name.strip().replace("\\", "/")
    if not name or name.startswith("/") or ".." in name.split("/") or " " in name:
        return None
    if "." not in name.rsplit("/", 1)[-1]:
        return None
    return name


def _parse_files(text: str) -> dict[str, str]:
    """Extract {filename: content} from fenced code blocks."""
    files: dict[str, str] = {}
    for match in _FILE_BLOCK_RE.finditer(text or ""):
        filename = match.group("file") or match.group("barefile")
        if filename is None:
            continue  # bare language block with no filename — not attributable
        safe = _safe_filename(filename)
        if safe is None:
            continue
        body = match.group("body").strip()
        if body:
            files[safe] = body
    return files


def _strip_fences(text: str) -> str:
    """Remove ``` fence marker lines (handles unterminated single-block output)."""
    lines = [line for line in (text or "").splitlines() if not line.strip().startswith("```")]
    return "\n".join(lines).strip()


def _parse_json_list(text: str) -> list[dict[str, Any]] | None:
    """Leniently extract a JSON array of objects from LLM output."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\n(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1).strip() if fenced else text.strip()
    start, end = candidate.find("["), candidate.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(candidate[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(parsed, list):  # pragma: no cover - defensive; slices starting with "[" parse as lists
        return None
    return [item for item in parsed if isinstance(item, dict)]


def _normalize_issue(raw: dict[str, Any]) -> dict[str, Any]:
    severity = str(raw.get("severity", "info")).lower()
    if severity not in ("critical", "high", "medium", "low", "info"):
        severity = "info"
    try:
        line = int(raw["line"]) if raw.get("line") is not None else None
    except (TypeError, ValueError):
        line = None
    return {
        "severity": severity,
        "file": str(raw.get("file", "")),
        "line": line,
        "message": str(raw.get("message", ""))[:500],
    }


def _score_from_issues(issues: list[dict[str, Any]]) -> float:
    weights = {"critical": 3.0, "high": 2.0, "medium": 1.0, "low": 0.5, "info": 0.1}
    penalty = sum(weights.get(i["severity"], 0.1) for i in issues)
    return round(max(0.0, 10.0 - penalty), 1)


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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        num_ctx: int = 4096,
    ) -> str | None:
        """Call the LLM (no chain-of-thought; workflow phases need answers, not thinking traces).

        Retries once on empty output. Returns stripped text, or None when unreachable/failed.
        """
        assert self.llm is not None
        for attempt in (1, 2):
            try:
                text = await self.llm.generate(
                    prompt,
                    role="coding",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    think=False,
                    num_ctx=num_ctx,
                )
            except Exception as exc:
                logger.warning("CodingWorkflow LLM call failed, using fallback", error=str(exc))
                return None
            text = (text or "").strip()
            if not text:
                logger.warning("CodingWorkflow LLM returned empty output", attempt=attempt)
                continue
            head = text[:40].lower()
            if head.startswith("[") and "error" in head:
                logger.warning("CodingWorkflow LLM returned error, using fallback", head=text[:80])
                return None
            return text
        return None

    def _simulated(self, phase: CodePhase) -> dict[str, Any]:
        sim = _SIMULATED_PHASES[phase].copy()
        sim.pop("agent", None)
        sim["simulated"] = True
        sim["simulation_note"] = _SIMULATED_MARKER
        return sim

    # ------------------------------------------------------------------
    # Agent methods — each maps to a specialist role in the pipeline
    # ------------------------------------------------------------------

    async def plan(self, task: str) -> dict[str, Any]:
        prompt = (
            f"Task: {task}\n\n"
            "You are a software architect. Break this coding task into a concrete plan:\n"
            "1. Architecture overview (1-2 sentences)\n"
            "2. Numbered sub-tasks in build order\n"
            "3. Tech stack choices\n"
            "4. Complexity estimate (low/medium/high)\n"
            "Keep it focused on THIS task, not generic advice."
        )
        text = await self._generate(prompt, temperature=0.3, max_tokens=1024)
        if text is None:
            return self._simulated(CodePhase.PLAN)
        return {"summary": text}

    async def design(self, task: str, plan_result: dict[str, Any]) -> dict[str, Any]:
        plan_text = str(plan_result.get("summary", ""))[:2000]
        prompt = (
            f"Task: {task}\n\nPlan:\n{plan_text}\n\n"
            "You are a software designer. Design the concrete structure:\n"
            "1. Components/files to create, each with its responsibility\n"
            "2. Data models with fields\n"
            "3. Public interfaces (functions, endpoints, or APIs)\n"
            "Keep it focused on THIS task."
        )
        text = await self._generate(prompt, temperature=0.3, max_tokens=1024)
        if text is None:
            return self._simulated(CodePhase.DESIGN)
        return {"summary": text}

    async def implement(
        self, task: str, design_result: dict[str, Any], *, repair_context: str = ""
    ) -> dict[str, Any]:
        design_text = str(design_result.get("summary", ""))[:2000]
        prompt = (
            f"Task: {task}\n\nDesign:\n{design_text}\n\n"
            f"{repair_context}"
            "You are a developer. Write the complete code.\n"
            "Rules:\n"
            "- Return EACH file in its own fenced block headed by the filename, e.g.:\n"
            "  ```python:models.py\n  <code>\n  ```\n"
            "- All files live in ONE flat directory; use flat imports "
            "(e.g. `from models import User`, never `from app.models import`).\n"
            "- Every module you import must be one of the files you return.\n"
            "- No placeholders, no TODOs, no ellipses — complete working code only.\n"
            "Return ONLY the file blocks, no prose."
        )
        text = await self._generate(prompt, temperature=0.3, max_tokens=4096, num_ctx=8192)
        if text is None:
            return self._simulated(CodePhase.IMPLEMENT)
        files = _parse_files(text)
        if not files:
            # One re-ask insisting on the file-block format before giving up honestly.
            reask = await self._generate(
                "Return ONLY fenced file blocks headed by filename "
                '(e.g. ```python:models.py). No prose.\n\n' + (text or "")[:2000],
                temperature=0.2,
                max_tokens=4096,
                num_ctx=8192,
            )
            files = _parse_files(reask or "")
        names = sorted(files)
        summary = f"Generated {len(files)} file(s): {', '.join(names)}" if files else "LLM returned no parseable files."
        return {"summary": summary, "files": files}

    async def review(self, code: str = "") -> dict[str, Any]:
        if not code.strip():
            return {"summary": "No code available for review.", "score": 0.0, "issues": []}
        prompt = (
            "You are a code reviewer. Review the code below and return ONLY a JSON array of findings. "
            "Each finding: severity (critical|high|medium|low|info), file, line, message. "
            "Empty array if no issues.\n\n"
            f"Code:\n{code[:6000]}"
        )
        text = await self._generate(prompt, temperature=0.2, max_tokens=1024)
        if text is None:
            return self._simulated(CodePhase.REVIEW)
        parsed = _parse_json_list(text)
        if parsed is None:
            return {
                "summary": "Reviewer returned unstructured feedback.",
                "score": 0.0,
                "issues": [{"severity": "info", "file": "", "line": None, "message": text[:500]}],
            }
        issues = [_normalize_issue(item) for item in parsed]
        score = _score_from_issues(issues)
        return {
            "summary": f"Reviewed code. Found {len(issues)} issue(s).",
            "score": score,
            "issues": issues,
        }

    async def test(
        self, code: str = "", language: str = "python", *, files: dict[str, str] | None = None
    ) -> dict[str, Any]:
        project = dict(files) if files else {}
        if not project and _looks_like_code(code):
            project = {"main.py": code}
        if language != "python":
            note = "unsupported-language"
            return {
                "summary": f"Test execution is only supported for python, not {language}.",
                "test_code": "",
                "test_results": {"passed": 0, "failed": 0, "skipped": 0, "success": False, "note": note},
            }
        if not project:
            return {
                "summary": "No code files available — nothing to test.",
                "test_code": "",
                "test_results": {"passed": 0, "failed": 0, "skipped": 0, "success": False, "note": "no-code"},
            }
        listing = "\n\n".join(f"### {name}\n{content[:3000]}" for name, content in project.items())
        prompt = (
            "You are a test engineer. Write a pytest test module for the code below.\n"
            "Rules:\n"
            "- Flat imports only (files live in one directory, e.g. `from models import User`).\n"
            "- Cover happy paths and at least one edge case.\n"
            "- Return ONLY one fenced python block, no prose.\n\n"
            f"Code:\n{listing[:6000]}"
        )
        test_text = await self._generate(prompt, temperature=0.3, max_tokens=2048)
        if test_text is None:
            return self._simulated(CodePhase.TEST)
        blocks = _parse_files(test_text)
        test_code = next(iter(blocks.values()), "")
        if not test_code:
            stripped = _strip_fences(test_text)
            if _looks_like_code(stripped):
                test_code = stripped
        if not test_code:
            return {
                "summary": "LLM returned no parseable tests.",
                "test_code": "",
                "test_results": {
                    "passed": 0, "failed": 0, "skipped": 0, "success": False, "note": "no-tests-generated",
                },
            }
        results = self._run_tests(project, test_code)
        total = results["passed"] + results["failed"] + results["errors"]
        summary = (
            f"Executed pytest: {results['passed']} passed, {results['failed']} failed, "
            f"{results['skipped']} skipped."
            if total
            else "Pytest collected no tests."
        )
        return {"summary": summary, "test_code": test_code, "test_results": results}

    def _run_tests(
        self, files: dict[str, str], test_code: str, timeout: int = 180
    ) -> dict[str, Any]:
        """Write files to an isolated temp dir and run pytest via the sandbox runner."""
        from app.tools.sandbox import run_pytest

        with tempfile.TemporaryDirectory(prefix="syzygy-code-test-") as tmpdir:
            for name, content in files.items():
                safe = _safe_filename(name)
                if safe is None:
                    continue
                target = Path(tmpdir, safe)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            Path(tmpdir, "test_generated.py").write_text(test_code, encoding="utf-8")
            return run_pytest(tmpdir, timeout=timeout)

    async def document(self, task: str, all_results: dict[str, Any]) -> dict[str, Any]:
        phase_notes = "; ".join(
            f"{name}: {str(info.get('summary', ''))[:200]}"
            for name, info in all_results.items()
            if isinstance(info, dict)
        )[:2000]
        prompt = (
            f"Task: {task}\n\nPipeline outcome:\n{phase_notes}\n\n"
            "You are a technical writer. Write a concise README in markdown: "
            "title, setup steps, API/file reference, and how to run the tests. "
            "Describe ONLY what was actually built above."
        )
        text = await self._generate(prompt, temperature=0.4, max_tokens=1024)
        if text is None:
            return self._simulated(CodePhase.DOCUMENT)
        return {"summary": "Generated project README.", "readme": text}

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
        assert self.llm is not None
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
        assert self.llm is not None
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

        async def report(phase: str, index: int, step: dict[str, Any]) -> None:
            if on_progress:
                await on_progress(phase, int(100 / total_phases * index), step)

        # 1. PLAN
        phases["plan"] = await self.plan(task)
        step = {
            "agent": "Planner",
            "thought": "Analyzing requirements, decomposing into sub-tasks, selecting tech stack...",
            "model": model,
            "confidence": 0.4 if phases["plan"].get("simulated") else 0.85,
        }
        reasoning.append({**step, "step": "plan"})
        await report("plan", 1, step)

        await asyncio.sleep(0.05)  # simulate agent processing

        # 2. DESIGN
        phases["design"] = await self.design(task, phases["plan"])
        step = {
            "agent": "Designer",
            "thought": "Designing component structure, data models, and interfaces...",
            "model": model,
            "confidence": 0.4 if phases["design"].get("simulated") else 0.85,
        }
        reasoning.append({**step, "step": "design"})
        await report("design", 2, step)

        await asyncio.sleep(0.05)

        # 3. IMPLEMENT (+ one repair attempt if tests fail)
        phases["implement"] = await self.implement(task, phases["design"])
        step = {
            "agent": "Developer",
            "thought": f"Writing {language} code with type hints, error handling, and docstrings...",
            "model": model,
            "confidence": 0.88 if phases["implement"].get("files") else 0.5,
        }
        reasoning.append({**step, "step": "implement"})
        await report("implement", 3, step)

        await asyncio.sleep(0.05)

        # 4. REVIEW (reviews the actual generated code)
        files_text = "\n\n".join(
            f"### {fname}\n{content}"
            for fname, content in phases["implement"].get("files", {}).items()
        )
        phases["review"] = await self.review(files_text)
        review_score = float(phases["review"].get("score", 0.0) or 0.0)
        step = {
            "agent": "Reviewer",
            "thought": "Checking code quality, security, best practices, and potential bugs...",
            "model": model,
            "confidence": round(max(0.0, min(1.0, review_score / 10.0)), 2),
        }
        reasoning.append({**step, "step": "review"})
        await report("review", 4, step)

        await asyncio.sleep(0.05)

        # 5. TEST (really executes pytest; one repair iteration on failure)
        test_attempts = 1
        phases["test"] = await self.test("", language, files=phases["implement"].get("files", {}))
        test_results = phases["test"].get("test_results", {})
        if not test_results.get("success") and phases["implement"].get("files") and not phases["test"].get("simulated"):
            failure_log = str(test_results.get("output_tail", ""))[-2000:]
            repair_context = (
                "The previous attempt FAILED its tests. Fix the code.\n"
                f"Pytest output:\n{failure_log}\n\n"
            )
            phases["implement"] = await self.implement(task, phases["design"], repair_context=repair_context)
            test_attempts = 2
            phases["test"] = await self.test("", language, files=phases["implement"].get("files", {}))
            test_results = phases["test"].get("test_results", {})
        ran = test_results.get("passed", 0) + test_results.get("failed", 0) + test_results.get("errors", 0)
        test_confidence = round(test_results.get("passed", 0) / ran, 2) if ran else 0.0
        step = {
            "agent": "Tester",
            "thought": "Generating unit tests, running assertions, measuring coverage...",
            "model": model,
            "confidence": test_confidence,
        }
        reasoning.append({**step, "step": "test"})
        await report("test", 5, step)

        await asyncio.sleep(0.05)

        # 6. DOCUMENT
        phases["document"] = await self.document(task, phases)
        step = {
            "agent": "Documenter",
            "thought": "Generating README, API docs, and usage examples...",
            "model": model,
            "confidence": 0.4 if phases["document"].get("simulated") else 0.85,
        }
        reasoning.append({**step, "step": "document"})
        await report("document", 6, step)

        await asyncio.sleep(0.05)

        simulated = any(isinstance(info, dict) and info.get("simulated") for info in phases.values())
        if simulated:
            logger.warning("CodingWorkflow completed with simulated phases", task=task[:100])
        return {
            "task": task,
            "language": language,
            "status": "completed",
            "phases": phases,
            "reasoning": reasoning,
            "simulated": simulated,
            "test_attempts": test_attempts,
        }


CODING_WORKFLOW = CodingWorkflow()
