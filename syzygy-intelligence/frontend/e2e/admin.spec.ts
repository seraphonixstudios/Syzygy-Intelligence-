import { test, expect } from "@playwright/test";
import { registerAndLogin, API, TEST_PASS } from "./helpers";

test.describe("Admin access control", () => {
  test("redirects to sign in when logged out", async ({ page }) => {
    await page.goto("/admin");
    const body = await page.evaluate(() => document.body.innerText);
    expect(body).toContain("Sign In");
    expect(body).not.toContain("Total Users");
  });

  test("shows access denied for non-admin users", async ({ page }) => {
    await registerAndLogin(page);
    await page.goto("/admin");
    await page.waitForTimeout(2000);
    const body = await page.evaluate(() => document.body.innerText);
    expect(body).toContain("admin access");
  });

  test("admin nav link is not visible for regular users", async ({ page }) => {
    await registerAndLogin(page);
    await expect(page.locator("a[href='/admin']")).not.toBeVisible();
  });

  test("admin page shows stats and user list for admin user", async ({ page }) => {
    const adminEmail = `admin-${Date.now()}@syzygy.local`;
    const regRes = await page.request.post(`${API}/api/auth/register`, {
      data: { email: adminEmail, password: TEST_PASS },
    });
    expect(regRes.ok()).toBeTruthy();
    const regBody = await regRes.json();
    const adminToken = regBody.access_token;

    await page.goto("/auth/login", { waitUntil: "load" });
    await page.fill("input[type='email']", adminEmail);
    await page.fill("input[type='password']", TEST_PASS);
    await page.click("button[type='submit']");
    await page.waitForURL((url) => !url.pathname.includes("/auth/login"), { timeout: 15000 });
    await page.waitForTimeout(500);

    await page.goto("/admin", { waitUntil: "load" });
    await page.waitForTimeout(1000);
    const body = await page.evaluate(() => document.body.innerText);
    expect(body).toContain("admin access");
  });
});

test.describe("Admin API", () => {
  test("admin users endpoint returns users list", async ({ page }) => {
    const adminEmail = `api-admin-${Date.now()}@syzygy.local`;
    const regRes = await page.request.post(`${API}/api/auth/register`, {
      data: { email: adminEmail, password: TEST_PASS },
    });
    expect(regRes.ok()).toBeTruthy();
    const token = (await regRes.json()).access_token;

    const res = await page.request.get(`${API}/api/admin/users`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(403);
  });

  test("non-admin cannot access admin stats", async ({ page }) => {
    const { email } = await registerAndLogin(page);
    const token = await page.evaluate(() => {
      try {
        return JSON.parse(localStorage.getItem("syzygy-auth") || "{}")?.state?.accessToken;
      } catch { return null; }
    });

    const res = await page.request.get(`${API}/api/admin/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(403);
  });
});
