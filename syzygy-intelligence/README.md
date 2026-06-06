# ⚛ Syzygy Intelligence

> **"Aligning opposites into unified intelligence — where Anima meets Animus, where data meets depth. The Chemical Wedding of agents, forging spirit and matter, known and unknown, into higher emergent wisdom."**

Syzygy is an open-source, local-first, multi-agent AI platform built on alchemical philosophy and Jungian psychology. Agents of complementary polarity (Masculine/Feminine) converge through a structured Consensus Engine to produce unified intelligence — the Rebis — transcending what any single agent can achieve.

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
docker exec -it syzygy-ollama ollama pull qwen3.5:8b
docker exec -it syzygy-ollama ollama pull deepseek-r1:7b
```

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
SYZYGY_DEFAULT_MODEL=qwen3.5:8b
SYZYGY_CRITIC_MODEL=deepseek-r1:7b
SYZYGY_SYNTHESIS_MODEL=qwen3.5:8b
```

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

### Workflow Builder

Use the visual node-based editor to design custom workflows with drag-and-drop agent assignments, polarity requirements, and consensus rules.

**Available workflows (11 total):**

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
│   │   ├── workflows/           # 11 workflow definitions
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
│   │   │   └── translate.py
│   │   ├── api/                 # REST + WebSocket endpoints
│   │   ├── tools/               # Tool implementations
│   │   ├── llm/                 # LLM abstraction layer
│   │   ├── orchestration/       # Team formation, task queues
│   │   ├── plugins/             # Plugin system
│   │   └── db/                  # Database models & session
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── app/                     # Next.js App Router
│   ├── components/              # React components
│   │   ├── ui/                  # Base UI (shadcn)
│   │   ├── agents/              # Agent cards, glyphs
│   │   ├── consensus/           # Consensus visualizations
│   │   ├── memory/              # Memory browser
│   │   ├── workflow/            # Workflow builder
│   │   └── dashboard/           # Dashboard panels
│   ├── lib/                     # Utilities & API client
│   └── hooks/                   # React hooks
└── docs/
```

---

## Screenshots

> *Dashboard with polarity balance meter, agent cards with sun/moon glyphs, consensus viewport in vesica piscis, and Rebis fusion animation.*

---

## License

MIT

---

*"Solve et Coagula — Dissolve and Coalesce. The Great Work continues."*
