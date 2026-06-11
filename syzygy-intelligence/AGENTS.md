# Syzygy Intelligence — Agent Guide

## Project Structure

```
syzygy-intelligence/
├── backend/
│   ├── app/              # FastAPI application
│   │   ├── agents/       # Agent archetypes, polarity, personas
│   │   ├── api/routes/   # FastAPI route handlers
│   │   ├── consensus/    # Multi-agent consensus engine
│   │   ├── db/           # SQLAlchemy models + session
│   │   ├── llm/          # Ollama / LiteLLM abstraction
│   │   ├── workflows/    # Workflow definitions (coding, research, etc.)
│   │   └── main.py       # App entry point
│   ├── tests/            # pytest tests (asyncio_mode = auto)
│   │   ├── conftest.py
│   │   └── mock_ollama_server.py
│   └── pyproject.toml
├── frontend/
│   ├── app/              # Next.js App Router pages
│   ├── e2e/              # Playwright E2E tests
│   └── .env              # NEXT_PUBLIC_SYZYGY_API_URL=http://localhost:8001
├── docker-compose.yml
└── AGENTS.md
```

## Commands

| Command | What it does |
|---------|-------------|
| `make lint` | Run ruff linter on backend |
| `make lint-fix` | Auto-fix ruff issues |
| `make test` | Run backend unit tests (SQLite) |
| `make test-all` | Run tests with OLLAMA_BASE_URL set |
| `make e2e` | Run Playwright E2E tests |
| `make clean` | Remove caches and temp files |

## Conventions

- **Python**: 3.11+, ruff with line-length 120, select E/F/I/N/W/UP
- **Type hints**: Always use `from __future__ import annotations`
- **Enums**: Use `enum.StrEnum` not `str, Enum` (UP042)
- **Async**: FastAPI async routes, SQLAlchemy async sessions
- **Testing**: pytest with `asyncio_mode = auto`; mock external services (Ollama, Stripe)
- **Frontend tests**: `registerAndLogin(page)` in `beforeEach`, avoid auth race with `waitFor`

## Pattern Notes

- Workflow tests mock `OllamaClient` with `AsyncMock` — never hit real HTTP
- Tests use `AsyncMock()` for `db` — set `db.add = MagicMock()` to avoid RuntimeWarning
- OLLAMA_BASE_URL env var controls which Ollama instance tests connect to
- Port 8000 is often taken by Docker Desktop on Windows; dev runs on 8001
- Backend `.env` controls SYZYGY_ENV; root `.env` is for Docker Compose
