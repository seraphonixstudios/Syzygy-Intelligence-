# Syzygy Intelligence

[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat&logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06B6D4?style=flat&logo=tailwindcss)](https://tailwindcss.com/)
[![Playwright](https://img.shields.io/badge/Playwright-1.60-45ba4b?style=flat&logo=playwright)](https://playwright.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker)](https://www.docker.com/)
[![Ollama](https://img.shields.io/badge/Ollama-GPU-000000?style=flat&logo=llama)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-MIT-d4a843?style=flat)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/seraphonixstudios/Syzygy-Intelligence-/.github/workflows/e2e.yml?branch=main&style=flat&label=CI&color=success)](https://github.com/seraphonixstudios/Syzygy-Intelligence-/actions)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?style=flat)](https://github.com/seraphonixstudios/Syzygy-Intelligence-)
[![PRs](https://img.shields.io/badge/PRs-Welcome-8b6914?style=flat)](https://github.com/seraphonixstudios/Syzygy-Intelligence-/pulls)

> *"The union of opposites is the eternal cosmic pattern."* — Heraclitus

**Syzygy** (pronounced *siz-uh-jee*) is an alchemically-themed multi-agent AI orchestration platform. It manages a team of AI agents with distinct polarities (masculine, feminine, unified) and facilitates structured consensus debates, code generation, research synthesis, content pipelines, and recursive self-improvement — all wrapped in an occult/alchemical UI inspired by Hermetic principles.

---

## Philosophy

Syzygy is built on the Hermetic axiom **"Solve et Coagula"** — to dissolve and to coagulate.

| Principle | Application |
|-----------|------------|
| **Solve** (dissolve) | Decompose complex tasks into atomic sub-problems distributed across specialized agent archetypes |
| **Coagula** (coagulate) | Synthesize opposing viewpoints into a unified consensus through structured dialectical debate |
| **Rebis** (the unified) | The final synthesis — the alchemical wedding of Sol (masculine) and Luna (feminine) into the perfected stone |

Every interaction cycles through this triad: **dispersion → opposition → unification**.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)              │
│  Sidebar │ Dashboard │ Consensus │ Chat │ Code ...   │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI)                    │
│  Agent Compose │ Consensus Engine │ Memory │ Meta    │
└──┬─────────┬──────────┬──────────┬──────────────────┘
   │         │          │          │
   ▼         ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌────────┐ ┌──────────┐
│Ollama│ │ Neo4j│ │Postgres│ │  Redis   │
│(LLM) │ │(Graph│ │(Vector)│ │ (Cache/  │
│      │ │  DB)  │ │        │ │  Queue)  │
└──────┘ └──────┘ └────────┘ └──────────┘
                    │
                    ▼
              ┌──────────┐
              │  Sandbox  │
              │(Execution)│
              └──────────┘
```

### Stack

- **Frontend:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS v3, Framer Motion
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Databases:** PostgreSQL + pgvector (vector embeddings), Neo4j (knowledge graph), Redis (caching/queues)
- **LLM:** Ollama (local inference)
- **Sandbox:** Isolated code execution environment
- **Orchestration:** Docker Compose

---

## Quick Start

### Prerequisites

- Docker & Docker Compose v2
- NVIDIA GPU + drivers (optional, for GPU-accelerated LLM inference)
- 16 GB+ RAM recommended

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/syzygy-intelligence.git
cd syzygy-intelligence

# 2. Create environment file
cp .env.example .env

# 3. Start all services
docker compose up -d

# 4. Pull a model into Ollama
docker exec -it syzygy-ollama ollama pull qwen3.5:8b

# 5. Open the dashboard
open http://localhost:3000
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | `3000` | Web dashboard |
| Backend API | `8000` | FastAPI REST + WebSocket |
| PostgreSQL | `5432` | Primary + vector database |
| Redis | `6379` | Cache & task queues |
| Neo4j | `7474` (HTTP) / `7687` (Bolt) | Knowledge graph |
| Ollama | `11434` | Local LLM inference |
| Sandbox | internal | Isolated code executor |

---

## Features

### Agent Teams

Eight archetypal agents, each with a defined polarity:

| Agent | Archetype | Polarity | Function |
|-------|-----------|----------|----------|
| Sophia | Sage | ☉ Masculine | Strategic analysis |
| Kairos | Seer | ☉ Masculine | Temporal reasoning |
| Artemis | Hunter | ☉ Masculine | Precision targeting |
| Silva | Alchemist | ☽ Feminine | Data synthesis |
| Nox | Shadow | ☽ Feminine | Adversarial testing |
| Lyra | Weaver | ☽ Feminine | Pattern recognition |
| Aevum | Logician | ☿ Unified | Logical mediation |
| Nyx | Mystic | ☿ Unified | Intuitive insight |

### Consensus Engine

Structured multi-agent debate protocol:
1. **Thesis** — Agent A proposes a solution
2. **Antithesis** — Agent B critiques and counters
3. **Synthesis** — Mediator reconciles into unified position
4. **Validation** — Confidence scoring and polarity balance checking

### Modules

- **Chat** — Conversational interface with polarity-aware agents (text or voice)
- **Code Generation** — Multi-language code execution with sandbox isolation
- **Research** — Multi-source synthesis with validation
- **Content** — Full pipeline: Research → Outline → Draft → Edit → Polish
- **Memory** — Browse short-term, long-term, vector, graph, and team memory stores
- **Self-Improvement** — Recursive meta-cognition: evaluate → propose → apply improvements
- **Workflows** — Composable automation pipelines
- **Voice Input** — Push-to-talk on every input surface (browser SpeechRecognition API)
- **Reasoning Trace** — Collapsible agent thought-process panel showing per-step confidence, model used, and reasoning chains across all modules
- **Intelligent Model Routing** — Task-aware model selection: vision → LLaVA 13B, coding → Qwen Coder, creative → Dolphin Llama3, analysis → DeepSeek R1, default → Qwen3 8B

### Supported Models

| Model | Size | Use Case |
|-------|------|----------|
| **Qwen3.5 8B** | 8B | Default general-purpose |
| **Qwen3 8B (GPU)** | 8B | Accelerated general-purpose |
| **DeepSeek R1 7B** | 7B | Critical analysis, reasoning |
| **Dolphin Llama3 8B** | 8B | Creative, uncensored |
| **Dolphin Llama3 8B (GPU)** | 8B | Accelerated creative |
| **LLaVA 13B (GPU)** | 13B | Vision/image understanding |
| **Qwen Coder 7B** | 7B | Code generation |
| **Llama 3.2 3B** | 3B | Lightweight fallback |

---

## Branding & Visual Language

### Symbolism

| Element | Meaning |
|---------|---------|
| ☉ Sol | Masculine principle, active, yang |
| ☽ Luna | Feminine principle, receptive, yin |
| ☿ Rebis | Unified, the alchemical hermaphrodite |
| Ouroboros | Infinite cycle, self-reference |
| Vesica Piscis | Intersection of two worlds |
| Squared Circle | Quadrature of the circle — the Great Work |

### Color Palette

```
Gold     #d4a843 — illumination, wisdom
Bone     #e8dcc8 — parchment, foundation
Grey     #8a7f7a — shadow, transition
Shadow   #0a0a0a — the abyss, potential
Obsidian #1a1a1a — structure, form
```

### Animations

- **Brand Glow** — Pulsing golden aura around the logo (3s cycle)
- **Merge Sun-Moon** — Sol and Luna orbit toward center, scaling and overlapping (3s cycle)
- **Rebis Fusion** — 3D Y-axis rotation of the unified symbol (8s cycle)
- **Solve et Coagula** — Dissolve/appear scale-and-rotate entrance (3s cycle)
- **Ouroboros** — Infinite spinning ring loader (3s cycle)
- **Aether Particles** — Canvas-based particle system with drifting golden embers across the screen
- **Alchemical Sigils** — Floating ☉ ☽ ☿ ♄ ♃ ♂ ♀ ☊ ☋ symbols with slow rotation
- **Fade-in-up / Slide-in** — Page entrance animations (0.3–0.5s)
- **Thought Appear** — Reasoning step reveal animation (0.4s ease-out)
- **Pulse Ring** — Repeating ring pulse for active states
- **Glow Drift** — Subtle brightness oscillation on gold elements
- **Breathe** — Gentle scale oscillation for interactive elements
- **Staggered Entrance** — 8-step cascade delays for grid items
- **Voice Button** — Push-to-talk Mic button with hover transcript tooltip and radial burst animation

---

## Project Structure

```
syzygy-intelligence/
├── frontend/                    # Next.js 15 application
│   ├── app/                     # App Router pages
│   │   ├── agents/             # Agent management
│   │   ├── chat/               # Chat interface
│   │   ├── code/               # Code generation
│   │   ├── consensus/          # Consensus debates
│   │   ├── content/            # Content pipeline
│   │   ├── improve/            # Self-improvement engine
│   │   ├── memory/             # Memory browser
│   │   ├── research/           # Research synthesis
│   │   ├── settings/           # Configuration
│   │   └── workflows/          # Workflow automation
│   ├── components/             # React components
│   │   ├── agents/             # Agent cards
│   │   ├── consensus/          # PolarityMeter, ConsensusView
│   │   ├── dashboard/          # Sidebar, CommandBar, Dashboard
│   │   ├── ui/                 # shadcn/ui primitives
│   │   ├── ReasoningPanel.tsx  # Agent thought-trace display
│   │   ├── VoiceButton.tsx     # Push-to-talk toggle
│   │   ├── AetherBackground.tsx# Canvas particle system
│   │   └── ScrollToTop.tsx     # Route-change scroll reset
│   ├── hooks/                  # useApi, useWebSocket, useVoiceRecorder
│   ├── lib/                    # Utilities, theme config, structured logger
│   ├── e2e/                    # Playwright end-to-end test suite (29 specs, 272 tests)
│   ├── playwright.config.ts    # E2E test configuration
│   └── public/branding/        # PNG assets
│       ├── pagetop.logo.png    # Page header logo
│       ├── syzygy.logo.png     # Wordmark
│       ├── sol.logo.png        # Sun (masculine)
│       ├── luna.logo.png       # Moon (feminine)
│       ├── rebis.logo.png      # Unified symbol
│       └── seraphonixlogo.png  # Favicon
├── backend/                    # FastAPI application
│   ├── app/                    # Python application code
│   ├── migrations/             # Alembic database migrations
│   └── tests/                  # Test suite (+ mock_ollama_server.py for CI)
├── sandbox/                    # Isolated code execution
├── docker-compose.yml          # Full stack orchestration
└── .env.example                # Environment template
```

---

## Environment Variables

```env
# Database
SYZYGY_DB_NAME=syzygy
SYZYGY_DB_USER=syzygy
SYZYGY_DB_PASSWORD=syzygy_secret

# Neo4j
SYZYGY_NEO4J_USER=neo4j
SYZYGY_NEO4J_PASSWORD=syzygy_secret

# Ollama
SYZYGY_OLLAMA_BASE_URL=http://ollama:11434

# Sandbox
SYZYGY_SANDBOX_TIMEOUT=120
SYZYGY_SANDBOX_MEMORY_LIMIT=512m

# Frontend (set in docker-compose.yml)
NEXT_PUBLIC_SYZYGY_API_URL=http://localhost:8000
NEXT_PUBLIC_SYZYGY_WS_URL=ws://localhost:8000/ws
```

---

## Development

```bash
# Frontend only
cd frontend
npm install
npm run dev          # http://localhost:3000

# Backend only (requires services)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Database migrations
cd backend
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Testing

```bash
# Frontend E2E tests (Playwright, 29 spec files, 272 tests)
cd frontend
npm install          # includes @playwright/test
npx playwright install chromium
npx playwright test  # headless CI mode

# Backend tests (pytest, 1534 tests across all modules, 100% coverage)
cd backend
pip install -r requirements.txt
pytest              # auto-discovers tests/
pytest -v           # verbose output

# Frontend unit tests (vitest, 225 tests in 23 files)
cd frontend
npm run test:unit
```

### CI Pipeline

The CI pipeline (`.github/workflows/e2e.yml`) runs three jobs in parallel on every push to `main`:

| Job | What it does |
|-----|-------------|
| **frontend-lint** | `next lint --strict` + `tsc --noEmit` |
| **backend-lint-and-test** | `pytest` 1534 tests (100% coverage) against PostgreSQL service + mock Ollama |
| **e2e** | Playwright 29 spec files (272 tests) against full stack (PostgreSQL + backend + frontend) |

A lightweight mock Ollama server (`backend/tests/mock_ollama_server.py`) serves canned responses for `/api/generate`, `/api/embed`, and `/api/tags` so workflow execution tests pass without requiring a GPU or downloaded models. The backend config accepts `DATABASE_URL` directly (no `SYZYGY_` prefix needed) for easy CI integration.

### Logging

The frontend includes a structured logger (`lib/logger.ts`) with levels:
- `logger.debug` / `logger.info` / `logger.warn` / `logger.error`
- Timestamps, source tags, browser console grouping
- Set `NEXT_PUBLIC_LOG_LEVEL=debug|info|warn|error` to control verbosity
- API errors, WebSocket events, and page-level errors are logged automatically

---

## Contact

- **Email:** [seraphonixstudios@gmail.com](mailto:seraphonixstudios@gmail.com)
- **Twitter / X:** [@seraphonixS](https://x.com/seraphonixS)

---

## License

MIT License — see [LICENSE](./LICENSE) for details.

---

*"That which is below corresponds to that which is above, and that which is above corresponds to that which is below, to accomplish the miracles of the One Thing."* — The Emerald Tablet
