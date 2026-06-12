# Syzygy Intelligence — Agent Guide

## Project Structure

```
syzygy-intelligence/
├── backend/
│   ├── app/              # FastAPI application
│   │   ├── agents/       # Agent archetypes, polarity, personas
│   │   ├── api/          # FastAPI route handlers
│   │   │   ├── routes/   # Main API routes (chat, consensus, etc.)
│   │   │   └── openai_compat.py  # OpenAI-compatible /v1/chat/completions
│   │   ├── consensus/    # Multi-agent consensus engine
│   │   ├── db/           # SQLAlchemy models + session
│   │   ├── llm/          # Ollama / LiteLLM abstraction
│   │   ├── workflows/    # Workflow definitions (coding, research, etc.)
│   │   └── main.py       # App entry point
│   ├── tests/            # pytest tests (asyncio_mode = auto)
│   │   ├── conftest.py
│   │   ├── mock_ollama_server.py
│   │   ├── test_chat.py
│   │   ├── test_openai_compat.py
│   │   ├── test_llm_integration.py
│   │   └── ...
│   └── pyproject.toml
├── frontend/
│   ├── app/              # Next.js App Router pages (22 prerendered)
│   ├── components/       # Shared components
│   │   ├── consensus/      # Consensus UI (PolarityMeter, LiveAgentGrid, etc.)
│   │   └── agents/         # Agent UI (ArchetypePicker, CreateAgentModal, etc.)
│   ├── e2e/              # Playwright E2E tests (25 specs)
│   └── .env              # NEXT_PUBLIC_SYZYGY_API_URL=http://localhost:8001
├── docker-compose.yml
├── docker-compose.ollama-cpu.yml  # CPU-only override (no GPU reservation)
├── scripts/
│   └── setup-ollama.ps1           # Ollama install/pull/tag automation
└── AGENTS.md
```

## Test Counts

| Layer | Runner | Count | Notes |
|-------|--------|-------|-------|
| Backend unit | pytest | **392** | Consensus (95), Chat (17), WS (16), OpenAI compat (24), integration (6), + existing |
| Frontend component | vitest | **38** | Consensus UI + agent UI presentational components |
| E2E | Playwright | **24 specs** | 22 pages + auth + navigation |

CI runs 3 jobs: `frontend-lint`, `backend-lint-and-test` (392), `e2e` (3 parallel shards × 2 workers each).

## Commands

| Command | What it does |
|---------|-------------|
| `make lint` | Run ruff linter on backend |
| `make lint-fix` | Auto-fix ruff issues |
| `make test` | Run backend unit tests (SQLite) |
| `make test-all` | Run tests with OLLAMA_BASE_URL set to mock server |
| `make e2e` | Run Playwright E2E tests |
| `npx playwright test --shard=1/3` | Run one shard locally |
| `make dev-mock` | Start mock Ollama server on port 11435 |
| `.\scripts\setup-ollama.ps1` | Install/config Ollama locally (Windows) |
| `.\scripts\setup-ollama.ps1 -Docker` | Pull models inside Docker Ollama container |
| `docker compose -f docker-compose.yml -f docker-compose.ollama-cpu.yml up -d` | Start stack with CPU-only Ollama |
| `npm run test:unit` | Run vitest component tests (frontend) |
| `make clean` | Remove caches and temp files |

## Conventions

- **Python**: 3.14+, ruff with line-length 120, select E/F/I/N/W/UP
- **Type hints**: Always use `from __future__ import annotations`
- **Enums**: Use `enum.StrEnum` not `str, Enum` (UP042)
- **Async**: FastAPI async routes, SQLAlchemy async sessions
- **Testing**: pytest with `asyncio_mode = auto`; mock external services (Ollama, Stripe)
- **E2E tests**: `registerAndLogin(page)` in `beforeEach`, avoid auth race with `waitFor`
- **Component tests**: vitest + jsdom + @testing-library/react; co-located with components

## Pattern Notes

- Workflow tests mock `OllamaClient` with `AsyncMock` — never hit real HTTP
- Tests use `AsyncMock()` for `db` — set `db.add = MagicMock()` to avoid RuntimeWarning
- **Integration tests** (`test_llm_integration.py`): use `httpx.ASGITransport(app=mock_ollama_app)` to run mock Ollama in-process — no separate server needed
- **openai_compat tests** (`test_openai_compat.py`): minimal `FastAPI` app with `debug=False`, patch `ConsensusEngine` + `OllamaClient` at module level
- OLLAMA_BASE_URL env var controls which Ollama instance tests connect to
- E2E CI uses 3 shards × 2 workers each; `playwright.config.ts` sets `workers: process.env.CI ? 2 : undefined` — the matrix is in `.github/workflows/e2e.yml`
- Port 8000 is often taken by Docker Desktop on Windows; dev runs on 8001
- Backend `.env` controls SYZYGY_ENV; root `.env` is for Docker Compose
- Consensus engine has 4 files: `engine.py` (orchestration), `phases.py` (prompts), `scoring.py` (LLM eval), `synthesis.py` (Rebis output)
- `PolarityMeter` has zero-total fallback (even 33.33/33.33/33.34 split)
- Page-level component tests in jsdom are fragile (useAuthStore/useRouter/fetch dependencies) — prefer E2E for page behavior
