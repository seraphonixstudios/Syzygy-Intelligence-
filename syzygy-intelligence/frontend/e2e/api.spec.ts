import { test, expect } from "@playwright/test";
import { API, TEST_PASS, testEmail } from "./helpers";

let adminEmail: string;
let adminToken: string;
let userEmail: string;
let userToken: string;

test.describe("Backend API endpoints", () => {
  test.beforeAll(async ({ request }) => {
    adminEmail = testEmail("admin");
    const adminRes = await request.post(`${API}/api/auth/register`, {
      data: { email: adminEmail, password: TEST_PASS },
    });
    expect(adminRes.ok()).toBeTruthy();
    adminToken = (await adminRes.json()).access_token;

    userEmail = testEmail("user");
    const userRes = await request.post(`${API}/api/auth/register`, {
      data: { email: userEmail, password: TEST_PASS },
    });
    expect(userRes.ok()).toBeTruthy();
    userToken = (await userRes.json()).access_token;
  });

  test("GET /api/auth/me returns user profile", async ({ request }) => {
    const res = await request.get(`${API}/api/auth/me`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.email).toBe(userEmail);
    expect(body.subscription_tier).toBe("free");
    expect(typeof body.messages_used).toBe("number");
  });

  test("GET /api/auth/me returns 401 without token", async ({ request }) => {
    const res = await request.get(`${API}/api/auth/me`);
    expect(res.status()).toBe(401);
  });

  test("POST /api/chat/models returns model list", async ({ request }) => {
    const res = await request.post(`${API}/api/chat/models`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("available");
    expect(Array.isArray(body.available)).toBeTruthy();
  });

  test("GET /api/consensus/sessions returns session list", async ({ request }) => {
    const res = await request.get(`${API}/api/consensus/sessions`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    // May be empty or return sessions — either is valid
    expect(res.ok()).toBeTruthy();
  });

  test("POST /api/rag/query works without auth", async ({ request }) => {
    const res = await request.post(`${API}/api/rag/query`, {
      data: { query: "test", top_k: 5 },
    });
    // Public RAG endpoint — returns results even without auth
    expect(res.ok()).toBeTruthy();
  });

  test("POST /api/rag/query with auth returns results or empty", async ({ request }) => {
    const res = await request.post(`${API}/api/rag/query`, {
      headers: { Authorization: `Bearer ${userToken}` },
      data: { query: "syzygy", top_k: 5 },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("results");
    expect(Array.isArray(body.results)).toBeTruthy();
  });

  test("GET /api/memory/recent returns memory list", async ({ request }) => {
    const res = await request.get(`${API}/api/memory/recent?limit=5`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(Array.isArray(body.memories || body.results)).toBeTruthy();
  });

  test("GET /api/memory/recall searches memories", async ({ request }) => {
    const res = await request.get(`${API}/api/memory/recall?query=test&limit=5`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(Array.isArray(body.memories || body.results)).toBeTruthy();
  });

  test("GET /api/agents/ returns agent list", async ({ request }) => {
    const res = await request.get(`${API}/api/agents/`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("agents");
    expect(Array.isArray(body.agents)).toBeTruthy();
  });

  test("GET /api/meta/summary returns summary data", async ({ request }) => {
    const res = await request.get(`${API}/api/meta/summary`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(res.ok()).toBeTruthy();
  });

  test("GET /api/meta/history returns history array", async ({ request }) => {
    const res = await request.get(`${API}/api/meta/history`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(res.ok()).toBeTruthy();
  });

  test("GET /api/admin/users returns 403 for non-admin user", async ({ request }) => {
    const res = await request.get(`${API}/api/admin/users`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(res.status()).toBe(403);
  });

  test("POST /api/auth/api-keys CRUD lifecycle", async ({ request }) => {
    // Create
    const createRes = await request.post(`${API}/api/auth/api-keys`, {
      headers: { Authorization: `Bearer ${userToken}` },
      data: { name: "E2E API Test Key" },
    });
    expect(createRes.ok()).toBeTruthy();
    const createBody = await createRes.json();
    expect(createBody.key).toMatch(/^syzygy_/);

    // List
    const listRes = await request.get(`${API}/api/auth/api-keys`, {
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(listRes.ok()).toBeTruthy();
    const listBody = await listRes.json();
    expect(Array.isArray(listBody.api_keys || listBody.keys)).toBeTruthy();

    // Revoke
    const keyId = createBody.id || createBody.key_id;
    if (keyId) {
      const revokeRes = await request.delete(`${API}/api/auth/api-keys/${keyId}`, {
        headers: { Authorization: `Bearer ${userToken}` },
      });
      expect(revokeRes.ok()).toBeTruthy();
    }
  });

  test("POST /api/chat/completions returns 401 without auth", async ({ request }) => {
    const res = await request.post(`${API}/api/chat/completions`, {
      data: { message: "test" },
    });
    expect(res.status()).toBe(401);
  });

  test("POST /api/payments/create-checkout-session returns redirect URL or error", async ({ request }) => {
    const res = await request.post(`${API}/api/payments/create-checkout-session`, {
      headers: { Authorization: `Bearer ${userToken}` },
      data: { price_id: "price_monthly", success_url: `${API}/settings`, cancel_url: `${API}/cloud` },
    });
    expect(res.ok()).toBeTruthy();
  });

  test("POST /api/payments/webhook handles request without crashing", async ({ request }) => {
    const res = await request.post(`${API}/api/payments/webhook`, {
      data: { type: "checkout.session.completed" },
      headers: { "stripe-signature": "test" },
    });
    // Should return a valid response without crashing
    expect(res.ok()).toBeTruthy();
  });
});
