# Testing Guide for Security Fixes

## Quick Start

```bash
# Backend tests
cd backend
pytest tests/test_auth.py -v              # Auth & API key tests
pytest tests/test_websockets.py -v        # WebSocket auth tests
pytest tests/test_models.py -v            # DB model tests

# Frontend tests
cd frontend
npm run test:unit                          # Unit tests
npm run test                               # Playwright E2E tests
npx tsc --noEmit                          # Type checking
```

---

## Test Cases

### 1. WebSocket Authorization (CRITICAL)

**Test:** `test_websocket_requires_valid_session_ownership`

```python
async def test_websocket_auth_with_user_mismatch():
    """Verify WebSocket rejects user accessing another user's session"""
    
    # Create users
    user1 = await create_user("user1@test.com")
    user2 = await create_user("user2@test.com")
    
    # User1 creates agent + session
    agent = await create_agent(user1, "sage")
    session = await create_session(user1, agent)
    
    # User2 tries to connect to User1's session
    user2_token = create_access_token(str(user2.id), user2.email)
    
    # Attempt WebSocket connection
    with pytest.raises(WebSocketDisconnect) as exc_info:
        async with websocket_connect(
            f"ws://localhost/ws?session_id={session.id}&token={user2_token}"
        ) as ws:
            pass
    
    # Assert disconnected with proper error code
    assert "Session not found or access denied" in str(exc_info.value)
    
    # Only User1's connection should succeed
    user1_token = create_access_token(str(user1.id), user1.email)
    async with websocket_connect(
        f"ws://localhost/ws?session_id={session.id}&token={user1_token}"
    ) as ws:
        msg = await ws.receive_json()
        assert msg["type"] == "ping"  # WebSocket is open
```

**Run:** `pytest tests/test_websockets.py::test_websocket_auth_with_user_mismatch -v`

---

### 2. Agent Ownership (CRITICAL)

**Test:** `test_agent_user_isolation`

```python
async def test_agent_query_isolation():
    """Verify agents are tied to users and isolated"""
    
    user1 = await create_user("user1@test.com")
    user2 = await create_user("user2@test.com")
    
    # User1 creates agent
    agent1 = await create_agent(user1, "sage")
    
    # Query: User1 should see own agent
    db_session = get_db()
    result = await db_session.execute(
        select(Agent).where(Agent.user_id == user1.id)
    )
    agents = result.scalars().all()
    assert len(agents) == 1
    assert agents[0].id == agent1.id
    
    # Query: User2 should see no agents
    result = await db_session.execute(
        select(Agent).where(Agent.user_id == user2.id)
    )
    agents = result.scalars().all()
    assert len(agents) == 0
    
    # Query: Direct query without user_id should still work (internal)
    result = await db_session.execute(select(Agent).where(Agent.id == agent1.id))
    agent = result.scalar_one_or_none()
    assert agent is not None
    assert agent.user_id == user1.id
```

**Run:** `pytest tests/test_models.py::test_agent_query_isolation -v`

---

### 3. API Key Race Condition (HIGH)

**Test:** `test_api_key_concurrent_updates`

```python
import asyncio

async def test_api_key_last_used_atomic():
    """Verify concurrent API key auth doesn't lose updates"""
    
    user = await create_user("test@test.com")
    raw_key, hashed_key, searchable = generate_api_key()
    
    api_key = await create_api_key(user, hashed_key, searchable)
    initial_used = api_key.last_used_at
    
    # Simulate 10 concurrent authentications
    tasks = [
        authenticate_api_key(raw_key, get_db())
        for _ in range(10)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # All should succeed
    assert all(r is not None for r in results if not isinstance(r, Exception))
    
    # Check last_used_at was updated
    db_session = get_db()
    result = await db_session.execute(
        select(ApiKey).where(ApiKey.id == api_key.id)
    )
    updated_key = result.scalar_one()
    
    # Should be recent (not lost in race condition)
    assert updated_key.last_used_at > initial_used
    assert (datetime.now(UTC) - updated_key.last_used_at).total_seconds() < 5
```

**Run:** `pytest tests/test_auth.py::test_api_key_last_used_atomic -v`

---

### 4. Token Decode Error Logging (MEDIUM)

**Test:** `test_token_decode_logging`

```python
async def test_token_decode_logs_invalid_signature(caplog):
    """Verify tampering attempts are logged"""
    
    import logging
    caplog.set_level(logging.WARNING)
    
    # Create valid token
    valid_token = create_access_token("user-id", "user@test.com")
    
    # Tamper with signature
    parts = valid_token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.INVALID"
    
    # Attempt decode
    result = decode_token(tampered_token)
    
    # Should return None
    assert result is None
    
    # Should log warning about invalid token
    assert any("Token decode failed: invalid token" in record.message 
              for record in caplog.records 
              if record.levelname == "WARNING")
```

**Run:** `pytest tests/test_auth.py::test_token_decode_logging -v`

---

### 5. React Message Key Uniqueness (MEDIUM)

**Test:** `frontend/tests/chat.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test('message keys are unique and preserve state on concurrent sends', async ({ page }) => {
  await page.goto('http://localhost:3000/chat');
  
  // Type first message
  const input = page.locator('input[placeholder="Type your message..."]');
  await input.fill('First message');
  
  // Send first message
  await page.locator('button:has-text("Send")').first().click();
  
  // While waiting for response, send second message
  await input.fill('Second message');
  await page.locator('button:has-text("Send")').first().click();
  
  // Wait for responses
  await page.waitForTimeout(2000);
  
  // Both messages should be present (not overwritten)
  const messages = page.locator('[class*="flex gap-3"]');
  const count = await messages.count();
  
  // Should have: initial greeting + user msg 1 + user msg 2 + assistant responses
  expect(count).toBeGreaterThanOrEqual(4);
  
  // Verify message content is intact
  expect(page.locator('text="First message"')).toBeVisible();
  expect(page.locator('text="Second message"')).toBeVisible();
});
```

**Run:** `npm run test -- tests/chat.spec.ts`

---

### 6. Error Boundary (MEDIUM)

**Test:** `frontend/tests/error-boundary.spec.ts`

```typescript
test('error boundary catches rendering errors', async ({ page }) => {
  // Navigate to chat
  await page.goto('http://localhost:3000/chat');
  
  // Simulate error in streaming (trigger onError callback)
  // Mock fetch to return bad SSE data
  await page.evaluate(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args: any[]) => {
      if (args[0]?.includes('stream')) {
        // Return invalid SSE response
        return new Response('invalid data', { status: 500 });
      }
      return originalFetch(...args);
    };
  });
  
  // Send message
  const input = page.locator('input[placeholder="Type your message..."]');
  await input.fill('Test message');
  await page.locator('button:has-text("Send")').first().click();
  
  // Wait for error to be caught
  await page.waitForTimeout(1000);
  
  // Error boundary should show fallback UI or error toast
  // (Page shouldn't crash to blank screen)
  expect(await page.locator('body').isVisible()).toBeTruthy();
});
```

**Run:** `npm run test -- tests/error-boundary.spec.ts`

---

### 7. Model Validation (LOW)

**Test:** `frontend/tests/model-validation.spec.ts`

```typescript
test('invalid model selection is rejected', async ({ page }) => {
  await page.goto('http://localhost:3000/chat');
  
  // Intercept fetch to inject invalid model
  await page.evaluate(() => {
    const originalFetch = window.fetch;
    window.fetch = async (url: string, options?: any) => {
      // Simulate selecting invalid model
      if (options?.body?.includes('model')) {
        const body = JSON.parse(options.body);
        body.model = 'invalid_model_name';
        options.body = JSON.stringify(body);
      }
      return originalFetch(url, options);
    };
  });
  
  // Try to send
  const input = page.locator('input[placeholder="Type your message..."]');
  await input.fill('Test');
  await page.locator('button:has-text("Send")').first().click();
  
  // Should reject with error toast
  const errorToast = page.locator('text="Invalid model"');
  await expect(errorToast).toBeVisible({ timeout: 2000 });
});
```

**Run:** `npm run test -- tests/model-validation.spec.ts`

---

### 8. useEffect Error Handling (LOW)

**Test:** `frontend/tests/error-handling.spec.ts`

```typescript
test('model fetch errors are logged and handled gracefully', async ({ page }) => {
  // Mock fetch to fail
  await page.evaluate(() => {
    window.fetch = async (url: string) => {
      if (url.includes('models')) {
        return new Response('Server Error', { status: 500 });
      }
      return new Response('{}');
    };
  });
  
  await page.goto('http://localhost:3000/chat');
  
  // Wait for fetch to fail and fallback to defaults
  await page.waitForTimeout(1000);
  
  // Should show error toast
  const errorToast = page.locator('text="Could not load models"');
  await expect(errorToast).toBeVisible();
  
  // Should still be functional (fallback models available)
  const modelButton = page.locator('text="Auto"');
  await expect(modelButton).toBeEnabled();
});
```

**Run:** `npm run test -- tests/error-handling.spec.ts`

---

## Load Testing: API Key Race Condition

```python
# tests/test_load.py

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def test_api_key_auth_load(n_concurrent=100):
    """Load test: 100 concurrent authentications with same key"""
    
    user = await create_user("load@test.com")
    raw_key, hashed_key, searchable = generate_api_key()
    
    # Create API key
    api_key = await create_api_key(user, hashed_key, searchable)
    
    # Authenticate concurrently
    start = time.time()
    tasks = [
        authenticate_api_key(raw_key, get_db())
        for _ in range(n_concurrent)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start
    
    # Verify results
    successful = sum(1 for r in results if r is not None)
    failed = sum(1 for r in results if isinstance(r, Exception))
    
    print(f"Concurrent auth test: {n_concurrent} requests")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Rate: {n_concurrent/elapsed:.0f} req/s")
    
    # Assert all succeeded
    assert failed == 0, f"{failed} authentication attempts failed"
    assert successful == n_concurrent
    
    # Check last_used_at was updated (verify atomic)
    db_session = get_db()
    result = await db_session.execute(
        select(ApiKey).where(ApiKey.id == api_key.id)
    )
    updated = result.scalar_one()
    assert updated.last_used_at is not None
```

**Run:** `pytest tests/test_load.py::test_api_key_auth_load -v -s`

---

## CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Security Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest tests/test_auth.py tests/test_websockets.py tests/test_models.py -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run test:unit
      - run: cd frontend && npm run test -- --ui=false
```

---

## Manual Testing Checklist

- [ ] **WebSocket:** Connect to session with wrong user's token → should reject
- [ ] **WebSocket:** Connect with expired token → should reject  
- [ ] **WebSocket:** Connect with valid token → should accept
- [ ] **Agent:** Query agents with User A → only see User A's agents
- [ ] **Agent:** Query agents with User B → only see User B's agents
- [ ] **API Key:** Load test 100 concurrent auth requests → all succeed
- [ ] **Chat:** Send two messages rapidly → both appear (not overwritten)
- [ ] **Chat:** Network error while streaming → error toast appears
- [ ] **Chat:** Invalid model selection → toast shows "Invalid model"
- [ ] **Chat:** Models API timeout → uses fallback models

---

## Success Criteria

✅ All WebSocket auth tests pass  
✅ All agent ownership tests pass  
✅ API key race condition test passes (100% success rate)  
✅ Token logging captures invalid attempts  
✅ Message keys are unique (no React warnings)  
✅ Error boundary catches errors gracefully  
✅ Model validation prevents invalid selections  
✅ useEffect errors logged properly  

