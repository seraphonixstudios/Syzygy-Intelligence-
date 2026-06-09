import { Page } from "@playwright/test";

const TEST_EMAIL = "e2e-test@syzygy.local";
const TEST_PASS = "testpass123";
const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export async function registerAndLogin(page: Page, email?: string) {
  const testEmail = email || TEST_EMAIL;

  // Try register — if user already exists, fall back to login
  let data: { access_token: string; refresh_token: string };
  const regRes = await page.request.post(`${API}/api/auth/register`, {
    data: { email: testEmail, password: TEST_PASS },
  });
  if (regRes.ok()) {
    data = await regRes.json();
  } else if (regRes.status() === 409) {
    const loginRes = await page.request.post(`${API}/api/auth/login`, {
      data: { email: testEmail, password: TEST_PASS },
    });
    if (!loginRes.ok()) {
      const body = await loginRes.text();
      throw new Error(`Login failed: ${loginRes.status()} ${body}`);
    }
    data = await loginRes.json();
  } else {
    const body = await regRes.text();
    throw new Error(`Registration failed: ${regRes.status()} ${body}`);
  }

  // Set auth state in localStorage using a public path to avoid RouteGuard redirect
  await page.goto("/cloud");
  await page.evaluate(
    ({ token, refresh }) => {
      localStorage.setItem(
        "syzygy-auth",
        JSON.stringify({
          state: {
            accessToken: token,
            refreshToken: refresh,
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    },
    { token: data.access_token, refresh: data.refresh_token }
  );
  // Reload to pick up the auth state
  await page.reload();
  await page.waitForTimeout(1000);

  return { email: testEmail };
}
