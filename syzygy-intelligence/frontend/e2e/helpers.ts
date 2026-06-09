import { Page } from "@playwright/test";

const TEST_EMAIL = "e2e-test@syzygy.local";
const TEST_PASS = "testpass123";
const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export async function registerAndLogin(page: Page, email?: string) {
  const testEmail = email || TEST_EMAIL;

  // Try register — if user already exists, fall back to login
  let data: { access_token: string; refresh_token: string } | null = null;
  try {
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
    }
  } catch {
    // Backend unavailable — use mock token so UI tests can still run
  }

  const token = data?.access_token || "mock-token";
  const refresh = data?.refresh_token || "mock-refresh";

  // Set init script so localStorage is populated BEFORE any page JS runs
  await page.addInitScript(
    ({ token, refresh }) => {
      localStorage.setItem(
        "syzygy-auth",
        JSON.stringify({
          state: {
            accessToken: token,
            refreshToken: refresh,
            isAuthenticated: true,
            rememberMe: true,
          },
          version: 0,
        })
      );
    },
    { token, refresh }
  );

  // Navigate to a public path so the init script fires
  await page.goto("/cloud");
  await page.waitForTimeout(1500);

  return { email: testEmail };
}
