# Syzygy Intelligence API Reference

## Base URL

All API endpoints are prefixed with `/api/`. The default server runs at `http://localhost:8000`.

```
http://localhost:8000/api/
```

WebSocket endpoint at `ws://localhost:8000/ws`.

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
      "model": "deepseek-r1:7b"
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
  "model": "qwen3.5:8b",
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
Chat completion with optional consensus.

**Request:**
```json
{
  "message": "Analyze AI safety",
  "use_consensus": true,
  "consensus_rounds": 4
}
```

---

## OpenAI-Compatible API

### `POST /v1/chat/completions`
OpenAI-compatible chat endpoint with Syzygy extensions.

**Request:**
```json
{
  "model": "syzygy-consensus",
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

**Server streams:**
```json
{"type": "consensus_round", "round": 1, ...}
{"type": "consensus_complete", "session_id": "...", "synthesis": "..."}
```

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
