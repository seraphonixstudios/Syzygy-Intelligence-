import { test, expect } from "@playwright/test";
import { registerAndLogin } from "./helpers";

test.describe("Sidebar navigation", () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page);
  });

  test("sidebar shows all nav links", async ({ page }) => {
    await page.goto("/");
    const links = page.locator("nav a, aside a");
    const linkCount = await links.count();
    expect(linkCount).toBeGreaterThanOrEqual(13);
  });

  test("navigates to /cloud", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/cloud']").first();
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL(/\/cloud/);
  });

  test("navigates to /", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/']").first();
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL(/\/$/);
  });

  test("navigates to /agents", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/agents']").first();
    await link.click();
    await expect(page).toHaveURL(/\/agents/);
  });

  test("navigates to /consensus", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/consensus']").first();
    await link.click();
    await expect(page).toHaveURL(/\/consensus/);
  });

  test("navigates to /chat", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/chat']").first();
    await link.click();
    await expect(page).toHaveURL(/\/chat/);
  });

  test("navigates to /workflows", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/workflows']").first();
    await link.click();
    await expect(page).toHaveURL(/\/workflows/);
  });

  test("navigates to /research", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/research']").first();
    await link.click();
    await expect(page).toHaveURL(/\/research/);
  });

  test("navigates to /code", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/code']").first();
    await link.click();
    await expect(page).toHaveURL(/\/code/);
  });

  test("navigates to /content", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/content']").first();
    await link.click();
    await expect(page).toHaveURL(/\/content/);
  });

  test("navigates to /memory", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/memory']").first();
    await link.click();
    await expect(page).toHaveURL(/\/memory/);
  });

  test("navigates to /improve", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/improve']").first();
    await link.click();
    await expect(page).toHaveURL(/\/improve/);
  });

  test("navigates to /brand", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/brand']").first();
    await link.click();
    await expect(page).toHaveURL(/\/brand/);
  });

  test("navigates to /settings", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/settings']").first();
    await link.click();
    await expect(page).toHaveURL(/\/settings/);
  });

  test("navigates to /rag (Knowledge)", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/rag']").first();
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL(/\/rag/);
  });
});
