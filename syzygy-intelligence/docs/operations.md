# Syzygy Intelligence — Operations Guide

## Deployment Options

### Docker Compose (Recommended)

```bash
git clone https://github.com/your-org/syzygy-intelligence.git
cd syzygy-intelligence
cp .env.example .env
docker compose up -d
```

This starts:
- `syzygy-postgres` — PostgreSQL with pgvector port 5432
- `syzygy-redis` — Redis cache port 6379
- `syzygy-neo4j` — Neo4j graph database ports 7474/7687
- `syzygy-ollama` — Ollama LLM server port 11434
- `syzygy-backend` — FastAPI backend port 8000
- `syzygy-frontend` — Next.js frontend port 3000
- `syzygy-sandbox` — Sandboxed code execution

### Pull Models

```bash
docker exec syzygy-ollama ollama pull qwen3:8b
docker exec syzygy-ollama ollama pull dolphin-llama3:8b
docker exec syzygy-ollama ollama pull llava:13b
```

### Manual Development

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Configuration

All configuration via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `SYZYGY_ENV` | `development` | Runtime environment |
| `SYZYGY_LOG_LEVEL` | `INFO` | Logging verbosity |
| `SYZYGY_DEFAULT_MODEL` | `qwen3:8b-gpu` | Primary LLM model |
| `SYZYGY_CRITIC_MODEL` | `qwen3:8b-gpu` | Critique phase model |
| `SYZYGY_SYNTHESIS_MODEL` | `qwen3:8b-gpu` | Synthesis model |
| `SYZYGY_CODING_MODEL` | `qwen3:8b-gpu` | Code generation model |
| `SYZYGY_CREATIVE_MODEL` | `dolphin-llama3:8b-gpu` | Creative/writing model |
| `SYZYGY_VISION_MODEL` | `llava:13b-gpu` | Vision/image analysis model |
| `SYZYGY_GPU_MODEL` | `qwen3:8b-gpu` | Primary GPU model |
| `SYZYGY_FAST_MODEL` | `dolphin-llama3:8b-gpu` | Fast/quick response model |
| `SYZYGY_MAX_CONSENSUS_ROUNDS` | `6` | Max debate rounds |
| `SYZYGY_CONVERGENCE_THRESHOLD` | `0.85` | Early stop threshold |
| `SYZYGY_VARIANCE_THRESHOLD` | `0.1` | Score variance threshold |

## Logging

Logs are written to `backend/data/logs/`:
- `syzygy.log` — All logs (rotated, 10MB max, 5 backups)
- `syzygy_error.log` — ERROR+ level only
- `syzygy_audit.log` — Audit trail entries

## Testing

```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/ -v --tb=short
```

## Architecture Decisions

### Why LangGraph?
LangGraph provides native state graph support, checkpointing for time-travel debugging, and built-in persistence — essential for the multi-round consensus process.

### Why Ollama-first?
Local inference ensures data privacy, zero API costs, and offline capability. Cloud fallback via LiteLLM provides flexibility.

### Why Neo4j + PostgreSQL + Chroma?
Each database serves a distinct purpose: PostgreSQL for relational data, Chroma for vector similarity, Neo4j for relationship traversal. This polyglot persistence matches the system's multi-layered memory architecture.

### Why the Alchemical Theme?
The visual theme is not decorative — it's functional. The polarity symbols, color mapping, and animation metaphors make the abstract consensus process intuitively understandable.
