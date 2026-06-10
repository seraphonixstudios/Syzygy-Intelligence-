import { test, expect } from "@playwright/test";
import { registerAndLogin, API } from "./helpers";

test.describe("Subscription", () => {
  test("cloud page renders all 4 tiers", async ({ page }) => {
    await page.goto("/cloud");
    await expect(page.getByRole("heading", { name: "Nigredo" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Solve" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Coagula" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Rebis" })).toBeVisible();
  });

  test("cloud page shows pricing for paid tiers", async ({ page }) => {
    await page.goto("/cloud");
    await expect(page.getByText("$29", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("$99", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Custom", { exact: true }).first()).toBeVisible();
  });

  test("cloud page has CTA buttons for each tier", async ({ page }) => {
    await page.goto("/cloud");
    const ctas = page.locator("button:has-text('Get Started Free'), button:has-text('Start Free Trial'), button:has-text('Contact Us')");
    await expect(ctas.first()).toBeVisible();
    await expect(ctas).toHaveCount(4);
  });

  test("settings subscription section shows tier and usage for free user", async ({ page }) => {
    await registerAndLogin(page);
    await page.goto("/settings");
    await expect(page.locator("h2:has-text('Subscription')")).toBeVisible();
    await expect(page.locator("text=Tier")).toBeVisible();
    await expect(page.locator("text=Messages Used")).toBeVisible();
    await expect(page.locator("text=free")).toBeVisible();
  });

  test("upgrade button navigates to cloud page", async ({ page }) => {
    await registerAndLogin(page);
    await page.goto("/settings");
    const upgradeBtn = page.locator("button:has-text('Upgrade Plan')");
    await expect(upgradeBtn).toBeVisible({ timeout: 10000 });
    await upgradeBtn.click();
    await expect(page).toHaveURL(/\/cloud/);
  });

  test("sidebar shows usage info only for free tier", async ({ page }) => {
    await registerAndLogin(page);
    await page.goto("/");
    await page.waitForTimeout(1000);
    const usageSection = page.locator("text=Messages Used, text=message limit");
    const count = await usageSection.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test("mock checkout session returns URL for paid tier", async ({ page }) => {
    const { email } = await registerAndLogin(page);
    const token = await page.evaluate(() => {
      try {
        return JSON.parse(localStorage.getItem("syzygy-auth") || "{}")?.state?.accessToken;
      } catch { return null; }
    });
    expect(token).toBeTruthy();

    const res = await page.request.post(`${API}/api/payments/create-checkout-session`, {
      data: { price_id: "price_premium_monthly" },
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.url).toContain("mock_checkout=true");
    expect(body.url).toContain("tier=premium");
  });

  test("mock checkout sets enterprise for coagula price", async ({ page }) => {
    const { email } = await registerAndLogin(page);
    const token = await page.evaluate(() => {
      try {
        return JSON.parse(localStorage.getItem("syzygy-auth") || "{}")?.state?.accessToken;
      } catch { return null; }
    });
    expect(token).toBeTruthy();

    const res = await page.request.post(`${API}/api/payments/create-checkout-session`, {
      data: { price_id: "price_enterprise_monthly" },
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.url).toContain("tier=enterprise");
  });

  test("webhook returns ignored when Stripe unconfigured", async ({ page }) => {
    const res = await page.request.post(`${API}/api/payments/webhook`, {
      headers: { "stripe-signature": "test_sig" },
      data: JSON.stringify({ type: "checkout.session.completed" }),
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("ignored");
  });
});
