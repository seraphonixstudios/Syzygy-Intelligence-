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

### Production Deployment

```bash
# Build and launch with production overrides
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Build frontend with production API URL
docker compose -f docker-compose.yml -f docker-compose.prod.yml build \
  --build-arg NEXT_PUBLIC_SYZYGY_API_URL=https://api.example.com \
  --build-arg NEXT_PUBLIC_SYZYGY_WS_URL=wss://api.example.com/ws
```

The `docker-compose.prod.yml` override strips bind-mounts, disables `--reload`, runs `alembic upgrade head` on startup, and sets `SYZYGY_ENV=production`.

### Monitoring Stack

```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

This starts Prometheus (port 9090), Grafana (port 3001), Alertmanager (port 9093), and Jaeger (port 16686). See [OBSERVABILITY.md](../OBSERVABILITY.md) for dashboards and alert rules.

### Caddy Reverse Proxy

```bash
docker compose -f docker-compose.yml -f docker-compose.caddy.yml up -d
```

Terminates TLS with auto-issued Let's Encrypt certificates, routes to backend (8000) and frontend (3000). Configure your domain in `Caddyfile`.

---

## Generate Secrets

Use the included script to generate strong random values for production:

```powershell
# Windows
.\scripts\generate-secrets.ps1
```

```bash
# Linux
chmod +x scripts/generate-secrets.sh
./scripts/generate-secrets.sh
```

Outputs values for `SYZYGY_SECRET_KEY`, `SYZYGY_DB_PASSWORD`, and other sensitive variables.

---

## Backup & Restore

### Automated Backups

```bash
docker compose -f docker-compose.yml -f docker-compose.backup.yml up -d
```

Backups are written to `./backups/` daily at 2 AM, retaining 7 daily + 4 weekly copies.

### Manual Backup

```powershell
# Windows
.\scripts\backup.ps1
```

```bash
# Linux
./scripts/backup.sh
```

Dumps PostgreSQL, exports Neo4j, and archives ChromaDB data into timestamped tarballs.

---

## OAuth Configuration

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → APIs & Services → Credentials
2. Create **OAuth 2.0 Client ID** (Web application type)
3. Add **Authorized Redirect URI**: `http://localhost:8001/api/auth/oauth/google/callback`
4. Set environment variables:
   ```
   SYZYGY_GOOGLE_CLIENT_ID=your-client-id
   SYZYGY_GOOGLE_CLIENT_SECRET=your-client-secret
   ```

### GitHub OAuth

1. Go to [GitHub Settings](https://github.com/settings/developers) → Developer settings → OAuth Apps → Register a new application
2. Set **Authorization callback URL**: `http://localhost:8001/api/auth/oauth/github/callback`
3. Set environment variables:
   ```
   SYZYGY_GITHUB_CLIENT_ID=your-client-id
   SYZYGY_GITHUB_CLIENT_SECRET=your-client-secret
   ```

**Production:** Replace `localhost:8001` with your real backend domain.

---

## Port Configuration

On Windows, Docker Desktop may occupy port 8000. For local development, use port 8001:

```
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Set `SYZYGY_OAUTH_REDIRECT_URL=http://localhost:8001/api/auth/oauth` to match. The frontend's `NEXT_PUBLIC_SYZYGY_API_URL` env var controls which backend URL the browser uses.

---

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

### Backend (pytest — 392 tests)

```bash
cd backend
pip install -r requirements.txt
pytest                              # All tests
pytest -v --tb=short               # Verbose with short tracebacks
```

Tests use a mock Ollama server (`backend/tests/mock_ollama_server.py`) to avoid requiring a GPU or model downloads in CI.

### Frontend E2E (Playwright — 28 spec files)

```bash
cd frontend
npx playwright test                 # Headless (CI: 2 workers, 3 shards)
npx playwright test --ui           # Interactive UI mode
npx playwright test e2e/auth.spec.ts  # Single file
```

### CI Pipeline

Three parallel jobs run on every push to `main`:
1. `frontend-lint` — `next lint --strict` + `tsc --noEmit`
2. `backend-lint-and-test` — pytest 392 tests with PostgreSQL + mock Ollama
3. `e2e` — full-stack Playwright (3 shards × 2 workers, ~5min wall-clock)

## Architecture Decisions

### Why LangGraph?
LangGraph provides native state graph support, checkpointing for time-travel debugging, and built-in persistence — essential for the multi-round consensus process.

### Why Ollama-first?
Local inference ensures data privacy, zero API costs, and offline capability. Cloud fallback via LiteLLM provides flexibility.

### Why Neo4j + PostgreSQL + Chroma?
Each database serves a distinct purpose: PostgreSQL for relational data, Chroma for vector similarity, Neo4j for relationship traversal. This polyglot persistence matches the system's multi-layered memory architecture.

### Why the Alchemical Theme?
The visual theme is not decorative — it's functional. The polarity symbols, color mapping, and animation metaphors make the abstract consensus process intuitively understandable.
