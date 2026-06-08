# ⚛ Syzygy Intelligence

<p align="center">
  <a href="https://github.com/seraphonixstudios/Syzygy-Intelligence-/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="MIT License"/></a>
  <a href="https://github.com/seraphonixstudios/Syzygy-Intelligence-/actions"><img src="https://img.shields.io/github/actions/workflow/status/seraphonixstudios/Syzygy-Intelligence-/.github/workflows/ci.yml?branch=main&style=flat-square&label=CI&color=success" alt="CI"/></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+"/></a>
  <a href="#"><img src="https://img.shields.io/badge/node-22+-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node 22+"/></a>
  <a href="#"><img src="https://img.shields.io/badge/docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker Ready"/></a>
  <a href="https://github.com/seraphonixstudios/Syzygy-Intelligence-/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome"/></a>
  <a href="https://github.com/seraphonixstudios/Syzygy-Intelligence-"><img src="https://img.shields.io/github/stars/seraphonixstudios/Syzygy-Intelligence-?style=flat-square&label=stars&color=yellow" alt="GitHub Stars"/></a>
</p>

> **"Aligning opposites into unified intelligence — where Anima meets Animus, where data meets depth. The Chemical Wedding of agents, forging spirit and matter, known and unknown, into higher emergent wisdom."**

<p align="center">
  <img src=".github/assets/og-banner.png" width="100%" alt="Syzygy Intelligence Banner" style="max-width: 800px; border-radius: 8px;"/>
</p>

Syzygy is an open-source, local-first, multi-agent AI platform built on alchemical philosophy and Jungian psychology. Agents of complementary polarity (Masculine/Feminine) converge through a structured Consensus Engine to produce unified intelligence — the Rebis — transcending what any single agent can achieve.

---

## Table of Contents

- [Vision](#vision)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Workflows](#workflows)
- [Getting Started](#getting-started)
- [API](#api)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Vision

Modern AI systems lack integration of complementary perspectives. Syzygy solves this by architecting **polarity-aware agent teams** that mirror the fundamental dualities of nature:

| Polarity | Archetypes | Role |
|----------|-----------|------|
| ☉ **Masculine** | Hero/Warrior, Sage, Ruler/King, Magician, Explorer | Structure, analysis, action, protection |
| ☽ **Feminine** | Great Mother, Lover, Innocent/Child, Creator/Artist, Anima | Nurture, intuition, creativity, connection |
| ☿ **Rebis (Unified)** | Self, Hermes/Mercurius, Trickster | Synthesis, integration, transcendence |

Through iterative rounds of **Proposal → Critique (Shadow Integration) → Refinement → Evaluation → Convergence → Synthesis**, Syzygy produces outputs that balance rigor with creativity, structure with flow, known with unknown.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Syzygy Intelligence                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Frontend     │  │  API Layer   │  │  Agent        │  │
│  │  Next.js 15   │◄─┤  FastAPI     │◄─┤  Orchestrator │  │
│  │  + shadcn/ui  │  │  + WebSocket │  │  LangGraph    │  │
│  └──────────────┘  └──────────────┘  └──────┬───────┘  │
│                                              │           │
│  ┌───────────────────────────────────────────┘           │
│  ▼                                                       │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Consensus Engine                     │    │
│  │  Proposal → Critique → Refine → Score → Converge │    │
│  └──────────────────────────────────────────────────┘    │
│              │                                           │
│  ┌───────────▼────────────────────────────────────────┐ │
│  │                   Memory Layer                      │ │
│  │  Short-Term │ Long-Term (Vector) │ Graph │ Team     │ │
│  └────────────────────────────────────────────────────┘ │
│              │                                           │
│  ┌───────────▼────────────────────────────────────────┐ │
│  │              Execution Layer                        │ │
│  │  Tools │ Code Sandbox │ Browser │ Filesystem │ Git  │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Components

- **Agent System**: Polarity-tagged agents with Jungian archetypes, shadow integration, and dynamic persona layers
- **Consensus Engine**: Multi-round structured debate with cross-polarity critique, shadow activation, and unified synthesis
- **Memory Layer**: Short-term (episodic), long-term (vector + graph), polarity-tagged, archetype-tagged, shared team memory
- **Workflow Engine**: Task decomposition, parallel execution, priority queuing with human-in-the-loop gates
- **Tool Ecosystem**: Browser automation, filesystem ops, Git, sandboxed code execution, web search
- **LLM Abstraction**: Ollama-first with LiteLLM fallback to OpenAI/Anthropic/etc.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, LangGraph, Uvicorn |
| **Agents** | LangGraph graphs + role-based crews + debate patterns |
| **Models** | Ollama (Qwen3.5, Qwen-Coder, DeepSeek, Dolphin-Llama3, Llama 3.3) |
| **Memory** | PostgreSQL + pgvector, Chroma, Neo4j, LangGraph checkpoints |
| **RAG** | ChromaDB + Ollama embeddings, txt/md/pdf ingestion (single & batch), semantic search, context injection into chat |
| **Streaming** | SSE (Server-Sent Events) for token-by-token chat, WebSocket for live consensus events |
| **Frontend** | Next.js 15, React 19, shadcn/ui, Tailwind CSS, Framer Motion |
| **Execution** | Docker sandboxed containers |
| **Orchestration** | LangGraph checkpointing, Redis task queues |

---

## Theme & Design

The UI manifests the alchemical aesthetic:

| Element | Implementation |
|---------|---------------|
| **Color** | Deep indigo (#0f0a2e) base, gold (#c9a84c), silver (#b0b0c0), cyan (#00f0ff) |
| **Rebis** | Dual sun/moon heads merging into cyan third eye — the unified Self |
| **Squared Circle** | Main workspace framing — *quadrature of the circle* |
| **Vesica Piscis** | Consensus viewport — intersection of two worlds |
| **Caduceus** | Sidebar navigation — twin serpents of polarity |
| **Ouroboros** | Processing animations — eternal return |
| **Solve et Coagula** | Dissolution → Coalescence transitions |
| **Crystalline Geometry** | Node network visualization |
| **Aether Particles** | Ambient background animations |

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Ollama (for local models)
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Quick Start (Docker)

```bash
git clone https://github.com/your-org/syzygy-intelligence.git
cd syzygy-intelligence

# Copy environment config
cp .env.example .env

# Launch everything
docker compose up -d

# Pull recommended models
docker exec -it syzygy-ollama ollama pull qwen3:8b
docker exec -it syzygy-ollama ollama pull dolphin-llama3:8b
docker exec -it syzygy-ollama ollama pull llava:13b
docker exec -it syzygy-ollama ollama pull nomic-embed-text
```

> **Note:** `nomic-embed-text` is required for the RAG knowledge base (vector embeddings). All models use GPU acceleration when available.

### Development Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Configure Models

Edit `backend/app/config/settings.yaml` or set via `.env`:

```env
SYZYGY_DEFAULT_MODEL=qwen3:8b-gpu
SYZYGY_CRITIC_MODEL=qwen3:8b-gpu
SYZYGY_SYNTHESIS_MODEL=qwen3:8b-gpu
SYZYGY_CODING_MODEL=qwen3:8b-gpu
SYZYGY_CREATIVE_MODEL=dolphin-llama3:8b-gpu
SYZYGY_VISION_MODEL=llava:13b-gpu
SYZYGY_GPU_MODEL=qwen3:8b-gpu
SYZYGY_FAST_MODEL=dolphin-llama3:8b-gpu
```

---

## User Authentication

Syzygy includes a built-in authentication system enabling user registration, login, session management, and admin access control.

### Features

- **Email/Password Registration** — Sign up with email, display name, and password
- **JWT-based Login** — Token-based authentication with access + refresh tokens
- **Persistent Sessions** — Auth state stored via zustand persist (localStorage), survives page reloads
- **Route Protection** — `RouteGuard` component redirects unauthenticated users to `/auth/login`
- **Admin Access** — Superuser accounts get an Admin panel (`/admin`) with user management
- **Free Tier** — Usage quota (messages/month) tracked per user with trial period support

### Auth Flow

```
User → /auth/login or /auth/register
  → Backend validates credentials, returns JWT tokens
  → Frontend stores tokens in zustand persist (localStorage)
  → RouteGuard checks isAuthenticated on every protected route
  → AuthInitializer syncs session on app load via /api/auth/me
  → Sidebar shows user info, message usage bar, and logout button
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login, returns JWT tokens |
| GET | `/api/auth/me` | Get current user profile |
| POST | `/api/auth/logout` | Invalidate session |
| GET | `/api/admin/users` | List all users (admin only) |

### Routes

| Path | Access | Description |
|------|--------|-------------|
| `/auth/login` | Public | Login form with alchemical branding (Rebis/Sol/Luna triangle) |
| `/auth/register` | Public | Registration form with matching design |
| `/admin` | Admin only | User management dashboard |
| All others | Authenticated | Protected by `RouteGuard` |

---

## Usage

### Natural Language Command

Open the dashboard and type:

> "Research quantum computing breakthroughs and write a synthesis report with balanced technical depth and accessibility"

Syzygy will:
1. Decompose the task into subtasks
2. Form a polarity-balanced agent team
3. Execute research in parallel
4. Run consensus rounds to synthesize findings
5. Produce a polished, balanced output

## Workflows

Syzygy ships with **18 workflow engines**, each designed for a specific task domain with optimal agent polarity balance:

**Available workflows (18 total):**

| Workflow | Description | Agent Team |
|----------|-------------|------------|
| **Code** | Scaffold, edit, test, debug with polarity-aware pair programming | Hero + Sage |
| **Research** | Parallel search with multi-source validation and synthesis | Explorer + Sage |
| **Content** | Research → Outline → Draft → Edit → Polish pipeline | Creator + Weaver |
| **Debate** | Multi-round structured debate between agents | Sage + Trickster |
| **Task Decomposition** | Break complex tasks into dependency-tracked subtasks | Ruler + Explorer |
| **Audit** | Security scanning, code review, anti-pattern detection, compliance | Sage (critic) + Magician (tester) |
| **Test Gen** | Automated unit, integration, and edge-case test generation | Trickster (edge cases) + Sage (validation) |
| **Summary** | Multi-document summarization with key insight extraction | Rebis (synthesis) + Sage (extraction) |
| **Compliance** | Regulatory checks — GDPR, SOC2, HIPAA, PCI-DSS, CCPA | Ruler (governance) + Sage (analysis) |
| **QA Bot** | Knowledge-base Q&A — ingest docs, retrieve context, answer questions | Sage (retrieval) + Rebis (synthesis) |
| **Translate** | Multi-language translation with cultural adaptation | Weaver (pattern) + Hermes (linguistic) |
| **Interview Coach** | Role-specific questions, answer scoring, feedback coaching | Sage (evaluator) + Weaver (communication) |
| **Data Analyzer** | Statistical analysis, anomaly detection, correlation discovery, viz | Sage (analyst) + Magician (patterns) |
| **API Designer** | REST/GraphQL API design, OpenAPI specs, stubs, validation tests | Ruler (structure) + Hero (implementation) |
| **Agentic RAG** | Query decomposition, multi-hop retrieval, source-grounded synthesis | Explorer (retrieval) + Rebis (synthesis) |
| **Report Gen** | Multi-format structured reports with charts, tables, exec summaries | Creator (writing) + Sage (analysis) |
| **Data Pipeline** | ETL — ingest, clean, transform, validate schema, load to target | Magician (transformation) + Ruler (governance) |
| **CI Piper** | CI/CD configs — GitHub Actions, GitLab CI, Jenkins with matrix builds | Hero (automation) + Sage (quality) |

### API

Syzygy exposes OpenAI-compatible endpoints:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "syzygy-consensus",
    "messages": [{"role": "user", "content": "Analyze the future of AI alignment"}],
    "syzygy_polarity_balance": 0.7,
    "syzygy_consensus_rounds": 4
  }'
```

---

## Project Structure

```
syzygy-intelligence/
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration management
│   │   ├── agents/              # Agent definitions & archetypes
│   │   ├── consensus/           # Multi-round consensus engine
│   │   ├── memory/              # Multi-layer memory system
│   │   ├── workflows/           # 18 workflow definitions
│   │   │   ├── coding.py
│   │   │   ├── research.py
│   │   │   ├── content.py
│   │   │   ├── debate.py
│   │   │   ├── task_decomposition.py
│   │   │   ├── audit.py
│   │   │   ├── test_gen.py
│   │   │   ├── summary.py
│   │   │   ├── compliance.py
│   │   │   ├── qa_bot.py
│   │   │   ├── translate.py
│   │   │   ├── interview_coach.py
│   │   │   ├── data_analyzer.py
│   │   │   ├── api_designer.py
│   │   │   ├── agentic_rag.py
│   │   │   ├── report_gen.py
│   │   │   ├── data_pipeline.py
│   │   │   └── ci_piper.py
│   │   ├── rag/                 # RAG pipeline (ingester, embeddings, retriever)
│   │   ├── api/                 # REST + WebSocket endpoints
│   │   ├── tools/               # Tool implementations
│   │   ├── llm/                 # LLM abstraction layer
│   │   ├── orchestration/       # Team formation, task queues
│   │   ├── plugins/             # Plugin system
│   │   └── db/                  # Database models & session
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   │   ├── auth/                # Login & register pages
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── admin/               # Admin panel (superuser only)
│   │   └── ...                  # App Router
│   ├── components/
│   │   ├── AuthInitializer.tsx  # Session sync on app load
│   │   ├── RouteGuard.tsx       # Protected route redirect
│   │   └── ...                  # React components
│   │   ├── ui/                  # Base UI (shadcn)
│   │   ├── agents/              # Agent cards, glyphs
│   │   ├── consensus/           # Consensus visualizations
│   │   ├── memory/              # Memory browser
│   │   ├── workflow/            # Workflow builder
│   │   └── dashboard/           # Dashboard panels
│   ├── hooks/                   # React hooks (useSSE, useWebSocket, etc.)
│   └── lib/                     # Utilities & API client
└── docs/
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- [Bug Reports](.github/ISSUE_TEMPLATE/bug_report.yml) — use our template
- [Feature Requests](.github/ISSUE_TEMPLATE/feature_request.yml) — suggest improvements
- [Pull Requests](.github/PULL_REQUEST_TEMPLATE.md) — follow the checklist

All contributors must adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <i>"Solve et Coagula — Dissolve and Coalesce. The Great Work continues."</i>
  <br/><br/>
  <a href="https://github.com/seraphonixstudios/Syzygy-Intelligence-"><img src="https://img.shields.io/github/stars/seraphonixstudios/Syzygy-Intelligence-?style=social" alt="Stars"/></a>
  <a href="https://github.com/seraphonixstudios/Syzygy-Intelligence-/fork"><img src="https://img.shields.io/github/forks/seraphonixstudios/Syzygy-Intelligence-?style=social" alt="Forks"/></a>
</p>
