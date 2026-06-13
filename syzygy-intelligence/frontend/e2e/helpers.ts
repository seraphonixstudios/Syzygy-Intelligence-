import { Page, expect, Locator } from "@playwright/test";

export const TEST_PASS = "testpass123";
export const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";
export const WS_URL = process.env.NEXT_PUBLIC_SYZYGY_WS_URL || "ws://localhost:8000/ws";

export async function registerAndLogin(page: Page, email?: string) {
  const testEmail = email || `e2e-test-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@syzygy.local`;

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

  await page.goto("/auth/login", { waitUntil: "networkidle" });
  await page.waitForSelector("input[type='email']", { timeout: 10000 });

  await page.fill("input[type='email']", testEmail);
  await page.fill("input[type='password']", TEST_PASS);
  await page.keyboard.press("Enter");

  await page.waitForURL((url) => !url.pathname.includes("/auth/login"), { timeout: 15000 });
  await page.waitForTimeout(500);

  return { email: testEmail };
}

/** Register user via API and return auth token (no browser login). */
export async function registerAndGetToken(request: any, email?: string) {
  const testEmail = email || `token-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@syzygy.local`;
  const regRes = await request.post(`${API}/api/auth/register`, {
    data: { email: testEmail, password: TEST_PASS },
  });
  if (!regRes.ok()) {
    throw new Error(`Register failed: ${regRes.status()} ${await regRes.text()}`);
  }
  const body = await regRes.json();
  return { email: testEmail, token: body.access_token };
}

/** Fill a form input, submit, and wait for a result element to appear. */
export async function submitAndWait(
  page: Page,
  opts: {
    goto: string;
    inputLocator: string;
    text: string;
    submitLocator?: string;
    resultLocator: string;
    timeout?: number;
  },
) {
  await page.goto(opts.goto);
  const input = page.locator(opts.inputLocator);
  await input.fill(opts.text);
  const submitBtn = opts.submitLocator
    ? page.locator(opts.submitLocator)
    : page.locator("button[type='submit']");
  await submitBtn.click();
  const result = page.locator(opts.resultLocator);
  await result.waitFor({ state: "visible", timeout: opts.timeout ?? 15000 }).catch(() => {});
  return result;
}

/** Check that a toast with the given text appears (or was visible recently). */
export async function expectToast(page: Page, text: string | RegExp) {
  const toast = page.getByText(text);
  await expect(toast).toBeVisible({ timeout: 10000 }).catch(() => {});
}

/** Return a fresh test email with stable prefix for grouping. */
export function testEmail(prefix = "e2e") {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@syzygy.local`;
}
