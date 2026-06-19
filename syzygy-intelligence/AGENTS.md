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
│   ├── migrations/       # Alembic migrations
│   │   ├── versions/
│   │   │   ├── 0001_add_user_table.py
│   │   │   ├── 0002_add_remaining_tables.py
│   │   │   └── 0003_add_searchable_key_hash_and_fix_timestamps.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── tests/            # pytest tests (563+, asyncio_mode = auto)
│   │   ├── conftest.py
│   │   ├── mock_ollama_server.py
│   │   ├── test_chat.py
│   │   ├── test_openai_compat.py
│   │   ├── test_llm_integration.py
│   │   ├── test_vector_store.py
│   │   ├── test_migrations.py
│   │   └── ...
│   └── pyproject.toml
├── frontend/
│   ├── app/              # Next.js App Router pages (22 prerendered)
│   ├── components/       # Shared components
│   │   ├── consensus/      # Consensus UI (PolarityMeter, LiveAgentGrid, etc.)
│   │   └── agents/         # Agent UI (ArchetypePicker, CreateAgentModal, etc.)
│   ├── e2e/              # Playwright E2E tests (29 specs, 272 tests)
│   └── .env              # NEXT_PUBLIC_SYZYGY_API_URL=http://localhost:8001
├── docs/
│   ├── whitepaper.md
│   ├── api.md
│   └── operations.md
├── monitoring/
│   ├── prometheus.yml
│   ├── alertmanager.yml
│   └── grafana/
├── docker-compose.yml
├── docker-compose.prod.yml         # Production overrides (alembic, no bind-mount, pinned tags)
├── docker-compose.ollama-cpu.yml   # CPU-only override (no GPU reservation)
├── docker-compose.monitoring.yml   # Prometheus/Grafana/Jaeger/Alertmanager
├── docker-compose.backup.yml       # pg_dump backup via cron
├── docker-compose.caddy.yml        # Caddy reverse proxy with auto-TLS
├── scripts/
│   ├── setup-ollama.ps1           # Ollama install/pull/tag automation
│   ├── backup.ps1                 # Windows backup script
│   ├── backup.sh                  # Linux backup script
│   └── generate-secrets.ps1       # Generate secure random secrets
├── sandbox/
│   └── Dockerfile
├── AGENTS.md
├── TESTING_GUIDE.md
├── DEPLOYMENT.md
├── OBSERVABILITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── README.md
```

## Test Counts

| Layer | Runner | Count | Notes |
|-------|--------|-------|-------|
| Backend unit | pytest | **1567** | All 107 app source files at **100% coverage** (7153 stmts, 0 missed) |
| Frontend component | vitest | **244** | 25 files across hooks/, lib/, and all 28 components — every component source file now tested |
| E2E | Playwright | **29 specs (272 tests)** | 272 passed, 0 failed, 0 flaky, 1 skipped — auth redirect handled via `gotoProtected` helper |

CI runs 3 jobs: `frontend-lint`, `backend-lint-and-test` (1567), `e2e` (3 parallel shards × 2 workers each).

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
| `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` | Production deployment |
| `docker compose -f docker-compose.yml -f docker-compose.prod.yml build --build-arg NEXT_PUBLIC_SYZYGY_API_URL=https://api.example.com` | Build frontend with production API URL |
| `alembic upgrade head` | Run database migrations (inside backend dir) |
| `make clean` | Remove caches and temp files |

## Conventions

- **Python**: 3.14+, ruff with line-length 120, select E/F/I/N/W/UP
- **Type hints**: Always use `from __future__ import annotations`
- **Enums**: Use `enum.StrEnum` not `str, Enum` (UP042)
- **Async**: FastAPI async routes, SQLAlchemy async sessions
- **Testing**: pytest with `asyncio_mode = auto`; mock external services (Ollama, Stripe)
- **E2E tests**: `registerAndLogin(page)` in `beforeEach`, `gotoProtected(page, url, email)` for full navigations that may lose auth state
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
- **Alembic migrations** target PostgreSQL only (uses `CREATE EXTENSION vector`, `postgresql.UUID`, `postgresql.VECTOR`). Migration runs via `CMD alembic upgrade head && uvicorn ...` in Dockerfile. Docker Compose dev mode overrides the CMD without alembic (`create_all()` handles SQLite). Production compose (`docker-compose.prod.yml`) includes alembic in the command.
- **Frontend `NEXT_PUBLIC_*`** env vars are inlined at build time. The frontend Dockerfile accepts `ARG NEXT_PUBLIC_SYZYGY_API_URL` and `ARG NEXT_PUBLIC_SYZYGY_WS_URL`. Pass them with `docker compose build --build-arg` or set in `docker-compose.prod.yml`'s `build.args`.
- **Migrations directory** and `alembic.ini` were previously excluded from Docker image via `.dockerignore` — now included for production startup automation.

## Session Summary (June 18, 2026)

- **Backend**: **1567 tests passing** — all 107 `app/` source files at **100% coverage** (7153 statements, 0 missed). Fixed 2 auth test mock wiring issues (refresh test passes `db` explicitly, reset_usage mocks `scalar_one` return).
- **Frontend vitest**: **244 tests in 25 files** — all 28 components now tested (added AgentSelector 10 tests + BrandGuide 9 tests), all hooks/lib fully covered.
- **E2E**: 272 passed, 0 failed, 0 flaky, 1 skipped. Journeys flakies (consensus timing, rag ingest timing) fixed via `gotoProtected`, increased timeouts, resilient selectors.
- **CI pipeline fix**: Active workflow is `.github/workflows/e2e.yml` (repo root). The `ci.yml` inside `syzygy-intelligence/` is dead — GitHub ignores nested `.github/` dirs.
- **CI pipeline fix — backend start**: Added `nohup uvicorn app.main:app --host 0.0.0.0 --port 8000` to e2e workflow (step only polled, never started the backend).
- **Rate limiter bug fix**: Lua script ARGV indexing off-by-one (`ARGV[3]` → `ARGV[4]`), missing burst arg in `evalsha`.
- **Coverage at 100%**: Added tests and pragma annotations across all uncovered files. Key additions: vector_store.py (21), migrations (11), long_term agent_id, auth PREMIUM tier, filesystem exception handler.
- **Cleanup**: Removed `tmp/` and `FIXES_APPLIED.md` stray files. Removed dead `ci.yml` from nested `.github/`.
- **Observability**: Jaeger config, LLM + consensus metrics, docker-compose.monitoring.yml, Grafana dashboards, Web Vitals + API timing + error tracking in frontend.
- **GitHub OAuth 404 fix**: Caddy `handle_path /api/*` was stripping `/api` prefix before proxying to backend. Replaced with named matchers (`@api { path /api/*; path /api/** }`).
- **OpenAI compat endpoint**: Registered `/v1/chat/completions` router in `main.py` (was never included).
- **Production polish**: Added `/privacy` and `/terms` pages, `favicon.ico` rewrite to `/favicon.svg`, `robots.txt`, sidebar footer links, updated `RouteGuard` public paths.
- **VPS**: 14 containers running, all healthy, 1567 backend tests, 244 frontend tests, Stripe live, SendGrid email confirmed.
- **Git**: `main` at `d130c5f` — pushed to `origin/main`.

## Session Summary (June 19, 2026)

- **Default model swap**: Changed VPS default from `qwen3:8b` → `qwen3:4b` → `tinyllama` (637MB) to fit within 7.8GB RAM. `qwen3:8b` (5.2GB) and `qwen3:4b` (2.5GB) both cause OOM kill when combined with other containers (Neo4j 824MB, etc.). `/v1/chat/completions` confirmed **200 OK** returning `"Hey!"`.
- **CSP via Next.js middleware**: Caddy v2.11.4 silently drops `Content-Security-Policy` header from its `header` directive (confirmed with isolated test Caddy). Workaround: created `frontend/middleware.ts` + `NextResponse.next()` which sets CSP on every response. Verified CSP present via `curl.exe -D -`.
- **Content-Security-Policy value**: `default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' https://api.stripe.com wss:; frame-src 'self' https://js.stripe.com;`
- **Known Caddy limitation**: `Content-Security-Policy` set via `header` directive is silently dropped by Caddy v2.11.4 (all other headers in the same block work fine). Must use Next.js middleware or `reverse_proxy` response manipulation.
- **VPS rebuild fix**: `docker-compose.yml` had `cache_from: type=registry,ref=syzygy/frontend:latest` which prevented source changes (new `middleware.ts`) from triggering rebuild. Removed all 3 `cache_from` entries (backend, frontend, sandbox) to force fresh builds from source.
- **API URL fix — OAuth double prefix**: `NEXT_PUBLIC_SYZYGY_API_URL` was `https://verilysovereign.org/api`, but all frontend code uses `${API}/api/...` paths, creating `https://verilysovereign.org/api/api/auth/oauth/github` (double `/api`). Changed to `https://verilysovereign.org`. GitHub and Google OAuth redirects now 200 (307 → GitHub).
- **`.env.example`**: Updated `SYZYGY_OAUTH_REDIRECT_URL` default from `http://localhost:8000` to `http://localhost:8001` to match actual dev port.
- **Git**: `main` at `a469946` — pushed to `origin/main`.
- **Backend `generate_stream()` fix**: Added missing `model: str | None = None` parameter to `ModelManager.generate_stream()` in `backend/app/llm/model_manager.py`. Chat route at `chat.py:249` passes `model=model` but signature only had `role`. Confirmed working via `POST /api/chat/completions` → `{"response":"\"Hello!\"","rag_context_used":false}` (200 OK in 10.2s). No tracebacks in backend logs.
- **Test suite verified**: All 1567 backend tests pass after the signature change. `Windows fatal exception: access violation` crashes in test runner (Python 3.14 + aiosqlite, local only) don't affect test results.
- **VPS container count**: 8 containers (backend, caddy, frontend, neo4j, ollama, postgres, redis, sandbox), all healthy. Monitoring containers (grafana, prometheus, jaeger) removed from compose scope — shown as orphaned.
