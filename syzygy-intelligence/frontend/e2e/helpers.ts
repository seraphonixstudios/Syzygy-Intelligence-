import { Page, expect } from "@playwright/test";

export const TEST_PASS = "testpass123";
export const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";

export async function registerAndLogin(page: Page, email?: string) {
  const testEmail = email || `e2e-test-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@syzygy.local`;

  // Ensure user exists via API
  try {
    const regRes = await page.request.post(`${API}/api/auth/register`, {
      data: { email: testEmail, password: TEST_PASS },
    });
    if (!regRes.ok() && regRes.status() !== 409) {
      console.warn("Register failed", regRes.status());
    }
  } catch {
    // Backend unavailable
  }

  // Do a real browser-based login to set up auth state properly
  await page.goto("/auth/login", { waitUntil: "load" });
  await page.waitForTimeout(1000);

  // Fill login form
  await page.fill("input[type='email']", testEmail);
  await page.fill("input[type='password']", TEST_PASS);
  await page.click("button[type='submit']");

  // Wait for redirect to home/settings after successful login
  await page.waitForURL((url) => !url.pathname.includes("/auth/login"), { timeout: 15000 });
  await page.waitForTimeout(1000);

  return { email: testEmail };
}
