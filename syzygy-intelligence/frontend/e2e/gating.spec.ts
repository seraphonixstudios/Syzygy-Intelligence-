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
    const meRes = await request.get(`${API}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const me = await meRes.json();
    expect(me.subscription_tier).toBe("free");

    if (me.trial_ends_at) {
      const trialEnd = new Date(me.trial_ends_at).getTime();
      if (trialEnd > Date.now()) {
        test.skip();
        return;
      }
    }

    const maxMessages: number = me.monthly_message_limit || 100;
    for (let i = 0; i <= maxMessages; i++) {
      const chatRes = await request.post(`${API}/api/workflows/chat`, {
        data: { message: `test message ${i}`, workflow: "chat" },
        headers: { Authorization: `Bearer ${token}` },
      });
      if (chatRes.status() === 429) {
        const body = await chatRes.json();
        expect(body.detail.code).toBe("USAGE_LIMIT_EXCEEDED");
        return;
      }
    }
    expect(false).toBeTruthy();
  });
});
