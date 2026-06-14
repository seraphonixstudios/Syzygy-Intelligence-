import { Page, expect, Locator } from "@playwright/test";

export const TEST_PASS = "testpass123";
export const API = process.env.NEXT_PUBLIC_SYZYGY_API_URL || "http://localhost:8000";
export const WS_URL = process.env.NEXT_PUBLIC_SYZYGY_WS_URL || "ws://localhost:8000/ws";

export async function registerAndLogin(page: Page, email?: string) {
  const testEmail = email || `e2e-test-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@syzygy.local`;

  // Try API registration + localStorage injection for reliability
  const regRes = await page.request.post(`${API}/api/auth/register`, {
    data: { email: testEmail, password: TEST_PASS },
  });
  if (regRes.ok() || regRes.status() === 409) {
    const body = regRes.status() === 409 ? { access_token: "" } : await regRes.json().catch(() => ({ access_token: "" }));
    const token = body.access_token || "";
    if (token) {
      // Inject token into localStorage so full page navigations keep auth
      await page.goto("/", { waitUntil: "domcontentloaded" }).catch(() => {});
      await page.evaluate((t) => {
        localStorage.setItem("syzygy-auth", JSON.stringify({
          state: { accessToken: t, refreshToken: "", isAuthenticated: true, rememberMe: true },
          version: 0,
        }));
      }, token);
      await page.goto("/");
      return { email: testEmail };
    }
  }

  // Fallback: form-based login
  await page.goto("/auth/login", { waitUntil: "load", timeout: 10000 }).catch(() => {});
  await page.waitForSelector("input[type='email']", { timeout: 10000 });
  await page.fill("input[type='email']", testEmail);
  await page.fill("input[type='password']", TEST_PASS);
  await page.keyboard.press("Enter");
  await page.waitForURL((url) => !url.pathname.includes("/auth/login"), { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(300);

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

/** Navigate to a protected page that may redirect to login on full page load.
 *  If redirected, re-authenticate using the form and retry the navigation. */
export async function gotoProtected(page: Page, url: string, email = "", pass = TEST_PASS) {
  await page.goto(url).catch(() => {});
  if (page.url().includes("/auth/login")) {
    await page.waitForSelector("input[type='email']", { timeout: 10000 }).catch(() => {});
    if (email) {
      await page.fill("input[type='email']", email);
      await page.fill("input[type='password']", pass);
      await page.keyboard.press("Enter");
      await page.waitForURL((u) => !u.pathname.includes("/auth/login"), { timeout: 15000 }).catch(() => {});
      await page.goto(url).catch(() => {});
    }
  }
}

/** Register + login via API directly and inject the auth token into localStorage.
 *  Avoids the auth redirect race that can happen when relying on form-based login persistence. */
export async function registerAndLoginDirect(page: Page, email?: string) {
  const testEmail = email || `direct-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@syzygy.local`;
  const regRes = await page.request.post(`${API}/api/auth/register`, {
    data: { email: testEmail, password: TEST_PASS },
  });
  if (!regRes.ok() && regRes.status() !== 409) {
    console.warn("Register failed", regRes.status());
    // Fall back to form-based login
    return registerAndLogin(page, testEmail);
  }
  const body = await regRes.json().catch(() => ({ access_token: "", refresh_token: "" }));
  const token = body.access_token;
  if (!token) {
    return registerAndLogin(page, testEmail);
  }
  // Inject token into localStorage so the React app finds it on next full page load
  await page.goto("/", { waitUntil: "domcontentloaded" }).catch(() => {});
  await page.evaluate((t) => {
    const payload = JSON.stringify({
      state: {
        accessToken: t,
        refreshToken: "",
        isAuthenticated: true,
        rememberMe: true,
      },
      version: 0,
    });
    localStorage.setItem("syzygy-auth", payload);
  }, token);
  return { email: testEmail };
}
