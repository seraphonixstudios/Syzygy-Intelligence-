# Syzygy Intelligence API Reference

## Base URL

All API endpoints are prefixed with `/api/`. The default server runs at `http://localhost:8000`.

```
http://localhost:8000/api/
```

WebSocket endpoint at `ws://localhost:8000/ws`.

---

## Authentication

All authenticated endpoints require an `Authorization: Bearer <token>` header. Tokens are obtained via login or registration.

### `POST /api/auth/register`
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepass123",
  "display_name": "User"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "User",
  "subscription_tier": "free",
  "messages_used": 0
}
```

### `POST /api/auth/login`
Authenticate and receive JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### `GET /api/auth/me`
Get the current user's profile. Requires authentication.

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "User",
  "subscription_tier": "free",
  "messages_used": 5,
  "messages_limit": 50,
  "created_at": "2026-06-01T00:00:00Z"
}
```

### `POST /api/auth/refresh`
Refresh an expired access token using a refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### `POST /api/auth/logout`
Invalidate the current session.

### `POST /api/auth/forgot-password`
Request a password reset email. In development mode, the reset token is copied to the response.

**Request:**
```json
{
  "email": "user@example.com"
}
```

### `POST /api/auth/reset-password`
Reset password using a reset token.

**Request:**
```json
{
  "token": "reset-token",
  "password": "newsecurepass456"
}
```

### `PUT /api/auth/me/settings`
Update user profile or settings.

**Request:**
```json
{
  "display_name": "New Name"
}
```

### API Keys

#### `POST /api/auth/api-keys`
Create a new API key. The raw key is returned only once.

**Request:**
```json
{
  "name": "My API Key"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "My API Key",
  "key": "syzygy_abc123...",
  "created_at": "2026-06-07T00:00:00Z"
}
```

#### `GET /api/auth/api-keys`
List all API keys for the user (prefix only, not the full key).

#### `DELETE /api/auth/api-keys/{id}`
Revoke an API key.

### OAuth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/oauth/{provider}` | Redirect to OAuth provider (google, github) |
| GET | `/api/auth/oauth/{provider}/callback` | OAuth callback handler |

### Rate Limiting

All `/api/*` endpoints are rate-limited using token bucket:

| Scope | Rate | Burst |
|-------|------|-------|
| Unauthenticated (per IP) | 10 req/s | 20 |
| Authenticated (per user) | 30 req/s | 60 |

Exceeded requests return `429 Too Many Requests` with a `Retry-After` header.

---

## Agents

### `GET /api/agents/`
List all registered agents.

**Response:**
```json
{
  "agents": [
    {
      "id": "uuid",
      "name": "Sage",
      "archetype": "sage",
      "polarity": "masculine",
      "glyph": "☉",
      "shadow_active": false,
      "persona": "Sage",
      "model": "qwen3:8b-gpu"
    }
  ]
}
```

### `POST /api/agents/`
Create a new agent.

**Request:**
```json
{
  "archetype": "sage",
  "name": "MySage",
  "model": "qwen3:8b-gpu",
  "shadow_active": false
}
```

### `GET /api/agents/{agent_id}`
Get a specific agent by ID.

### `DELETE /api/agents/{agent_id}`
Delete an agent.

### `POST /api/agents/{agent_id}/shadow/toggle`
Toggle shadow activation state.

---

## Sessions

### `GET /api/sessions/`
List active sessions.

### `POST /api/sessions/`
Create a new session.

**Request:** `{"task": "Research quantum computing"}`

### `GET /api/sessions/{session_id}`
Get session details.

---

## Consensus

### `POST /api/consensus/run`
Execute the full consensus pipeline.

**Request:**
```json
{
  "task": "Analyze the future of AI alignment",
  "max_rounds": 4,
  "threshold": 0.85
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "rounds_completed": 3,
  "synthesis": "Unified synthesis text...",
  "fusion_report": {
    "masculine_forces": ["Sage", "Hero"],
    "feminine_forces": ["Great Mother", "Creator"],
    "unified_perspective": ["Rebis"],
    "individuation_notes": "..."
  },
  "round_details": [
    {
      "round": 1,
      "proposals": [...],
      "critiques": [...],
      "refinements": [...],
      "scores": {"agent_id": 0.85},
      "convergence_score": 0.72
    }
  ]
}
```

### `GET /api/consensus/sessions/{session_id}`
Get consensus session status.

---

## Memory

### `POST /api/memory/store`
Store a memory.

**Request:**
```json
{
  "content": "Important insight",
  "type": "long_term",
  "agent_id": "uuid",
  "session_id": "uuid",
  "polarity": "masculine",
  "importance": 0.9,
  "tags": ["key", "insight"]
}
```

### `GET /api/memory/recall?query=insight&limit=10`
Recall memories matching query.

### `GET /api/memory/recent?session_id=uuid&limit=5`
Get most recent memories.

---

## Tools

### `GET /api/tools/`
List available tools.

### `POST /api/tools/execute`
Execute a tool.

**Request:**
```json
{
  "tool_id": "filesystem",
  "params": {"action": "read", "path": "/path/to/file"}
}
```

---

## Workflows

### `GET /api/workflows/`
List available workflows.

### `POST /api/workflows/{name}/execute`
Execute a workflow.

**Request:**
```json
{
  "task": "Build a Python CLI app",
  "context": {"language": "python"}
}
```

---

## Chat

### `POST /api/chat/completions`
Chat completion with optional consensus, RAG context, or direct model query.

**Request:**
```json
{
  "message": "Analyze AI safety",
  "model": "syzygy",
  "consensus_rounds": 2,
  "use_rag": false
}
```

- `model: "syzygy"` — runs consensus engine (5 agents, 2 rounds default)
- `model: "qwen3:8b-gpu"` — direct query to a specific model
- `use_rag: true` — injects relevant documents from the knowledge base as context before the prompt
- Returns `{ "response": "…", "session_id": "…", "rounds": N, "fusion_report": {…} }`

### `POST /api/chat/stream`
Stream chat completions token-by-token via Server-Sent Events.

**Request:**
```json
{
  "message": "Explain quantum computing",
  "model": "qwen3:8b-gpu",
  "use_rag": false
}
```

**Response:** `text/event-stream` with:
- `data: {"token": "Quantum"}\n\n` per generated token
- `data: {"rag_context": true}\n\n` (first event when RAG is active)
- `data: {"done": true}\n\n` final event

Supports `AbortController` cancellation on the client side.

### `POST /api/chat/multi-model`

### `POST /api/chat/multi-model`
Query multiple models in parallel. Returns responses from all.

**Request:**
```json
{
  "message": "Explain quantum computing",
  "models": ["qwen3:8b-gpu", "dolphin-llama3:8b-gpu"]
}
```

**Response:**
```json
{
  "responses": {
    "qwen3:8b-gpu": "Quantum computing uses qubits…",
    "dolphin-llama3:8b-gpu": "It's a computing paradigm…"
  }
}
```

If `models` is empty, all configured models are queried.

### `GET /api/chat/models`
List configured model roles and available Ollama models.

**Response:**
```json
{
  "configured": {
    "default": "qwen3:8b-gpu",
    "creative": "dolphin-llama3:8b-gpu",
    "vision": "llava:13b-gpu"
  },
  "available": ["qwen3:8b-gpu", "dolphin-llama3:8b-gpu", "llava:13b-gpu"],
  "all_models": ["qwen3:8b-gpu", "dolphin-llama3:8b-gpu", "llava:13b-gpu"]
}
```

---

## OpenAI-Compatible API

### `POST /v1/chat/completions`
OpenAI-compatible chat endpoint with Syzygy extensions. Routes `syzygy` model through consensus engine.

**Request:**
```json
{
  "model": "syzygy",
  "messages": [{"role": "user", "content": "Hello"}],
  "syzygy_polarity_balance": 0.7,
  "syzygy_consensus_rounds": 4
}
```

---

## Audit Logs

### `GET /api/audit/?limit=50&offset=0`
Query audit log entries.

### `GET /api/audit/count`
Count audit log entries.

---

## WebSocket

Connect to `ws://localhost:8000/ws`.

**Client sends:**
```json
{"action": "run_consensus", "task": "Analyze market trends"}
```

**Server streams (live events per phase):**
```json
{"type": "consensus_started", "task": "..."}
{"type": "consensus_proposal", "agent": "Sage", "archetype": "sage", "polarity": "masculine", "content": "..."}
{"type": "consensus_critique", "agent": "Heracles", "archetype": "hero", "polarity": "masculine", "content": "..."}
{"type": "consensus_refinement", "agent": "Nurtura", ...}
{"type": "consensus_evaluation", "agent": "Aphrodite", ...}
{"type": "consensus_synthesis", "synthesis": "..."}
{"type": "consensus_complete", "session_id": "...", "synthesis": "..."}
```

---

## RAG (Knowledge Base)

### `POST /api/rag/ingest`
Ingest a single document or raw text into the vector knowledge base.

**Request (multipart/form-data):**
- `file` — uploaded file (txt, md, pdf)
- OR `text` — raw text string
- Optionally: `source` — document label

**Response:**
```json
{"document_id": "uuid", "chunks": 12, "filename": "doc.txt"}
```

### `POST /api/rag/ingest/batch`
Ingest multiple files in a single request.

**Request:** `multipart/form-data` with multiple `files` fields.

**Response:**
```json
{
  "results": [
    {"file": "doc1.txt", "document_id": "uuid", "chunks": 5},
    {"file": "doc2.pdf", "document_id": "uuid", "chunks": 24}
  ],
  "errors": [],
  "total": 2
}
```

Individual file failures don't fail the entire batch — errors are returned in the `errors` array.

### `POST /api/rag/query`
Semantic search over ingested documents.

**Request:**
```json
{
  "query": "What is syzygy?",
  "top_k": 5
}
```

**Response:**
```json
{
  "results": [
    {"chunk": "Syzygy Intelligence is...", "score": 0.92, "document_id": "uuid", "source": "doc.txt"}
  ]
}
```

### `GET /api/rag/documents`
List all ingested documents.

**Response:**
```json
{
  "documents": [
    {"id": "uuid", "filename": "doc.txt", "chunk_count": 12, "created_at": "2026-06-07T..."}
  ]
}
```

### `DELETE /api/rag/documents/{document_id}`
Delete a document and its chunks from the vector store.

---

## Admin

Admin endpoints require a user with `is_superuser = true`.

### `GET /api/admin/users`
List all users (admin only).

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "display_name": "User",
      "subscription_tier": "free",
      "is_superuser": false,
      "created_at": "2026-06-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

---

## Payments / Stripe

### `POST /api/payments/create-checkout-session`
Create a Stripe Checkout Session for subscription purchase.

**Request:**
```json
{
  "price_id": "price_monthly",
  "success_url": "http://localhost:3000/settings",
  "cancel_url": "http://localhost:3000/cloud"
}
```

**Response:**
```json
{
  "url": "https://checkout.stripe.com/pay/..."
}
```

### `POST /api/payments/customer-portal`
Get the Stripe Customer Portal URL for managing subscriptions.

### `POST /api/payments/webhook`
Stripe webhook endpoint for subscription lifecycle events (requires Stripe signature header).

---

## Uploads

### `POST /api/uploads/`
Upload a file to the server.

**Request:** `multipart/form-data` with a `file` field.

**Response:**
```json
{
  "file_id": "uuid",
  "filename": "document.pdf",
  "size": 12345,
  "url": "/uploads/uuid/document.pdf"
}
```

### `DELETE /api/uploads/{file_id}`
Delete an uploaded file.

---

## Meta

### `GET /api/meta/summary`
Get system summary metadata.

### `GET /api/meta/history`
Get system history entries.

---

## Health

### `GET /health`
```json
{"status": "healthy", "env": "development"}
```

### `GET /`
```json
{
  "service": "Syzygy Intelligence",
  "version": "0.1.0",
  "tagline": "Aligning opposites into unified intelligence",
  "status": "operational"
}
```

### `GET /metrics`
Prometheus metrics endpoint, available when observability is enabled.

---
