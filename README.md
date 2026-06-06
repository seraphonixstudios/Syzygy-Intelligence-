# Syzygy Intelligence

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
│   │   └── ui/                 # shadcn/ui primitives
│   ├── hooks/                  # useApi, useWebSocket, useVoiceRecorder
│   ├── lib/                    # Utilities, theme config, structured logger
│   ├── e2e/                    # Playwright end-to-end test suite (38 tests)
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
│   └── tests/                  # Test suite
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
# Frontend E2E tests (Playwright, 38 tests across all pages)
cd frontend
npm install          # includes @playwright/test
npx playwright install chromium
npm run test         # headless CI mode
npm run test:headed  # visible browser mode
npm run test:ui      # Playwright UI mode

# Backend tests (pytest, 12 test files)
cd backend
pip install -r requirements.txt
pytest              # auto-discovers tests/
pytest -v           # verbose output
pytest --cov        # coverage report
```

### Logging

The frontend includes a structured logger (`lib/logger.ts`) with levels:
- `logger.debug` / `logger.info` / `logger.warn` / `logger.error`
- Timestamps, source tags, browser console grouping
- Set `NEXT_PUBLIC_LOG_LEVEL=debug|info|warn|error` to control verbosity
- API errors, WebSocket events, and page-level errors are logged automatically

---

## License

MIT License — see [LICENSE](./LICENSE) for details.

---

*"That which is below corresponds to that which is above, and that which is above corresponds to that which is below, to accomplish the miracles of the One Thing."* — The Emerald Tablet
