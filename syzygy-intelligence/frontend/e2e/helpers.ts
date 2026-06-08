import { Page } from "@playwright/test";

let userCounter = Date.now();
const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export async function registerAndLogin(page: Page, email?: string) {
  const testEmail = email || `test-${userCounter++}@example.com`;

  // Register via the API directly
  const res = await page.request.post(`${API}/api/auth/register`, {
    data: { email: testEmail, password: "testpass123" },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Registration failed: ${res.status()} ${body}`);
  }
  const data = await res.json();

  // Set auth state in localStorage using a public page to avoid RouteGuard redirect
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
