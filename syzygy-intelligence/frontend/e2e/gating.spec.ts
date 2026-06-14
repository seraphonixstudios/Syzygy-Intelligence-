import { test, expect } from "@playwright/test";
import { API, TEST_PASS } from "./helpers";

const email = `gate-${Date.now()}@syzygy.local`;
let token: string;

test.describe("Usage gating", () => {
  test.beforeAll(async ({ request }) => {
    const regRes = await request.post(`${API}/api/auth/register`, {
      data: { email, password: TEST_PASS },
    });
    expect(regRes.ok()).toBeTruthy();
    token = (await regRes.json()).access_token;
  });

  test("free user without active trial gets 429 when over message limit", async ({ request }) => {
    await request.post(`${API}/api/auth/expire-trial`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    const meRes = await request.get(`${API}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const me = await meRes.json();
    expect(me.subscription_tier).toBe("free");
    expect(me.trial_ends_at).toBeNull();

    const chatRes = await request.post(`${API}/api/auth/charge-message`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(chatRes.status()).toBe(429);
    const body = await chatRes.json();
    expect(body.error.code).toBe("USAGE_LIMIT_EXCEEDED");
  });
});
