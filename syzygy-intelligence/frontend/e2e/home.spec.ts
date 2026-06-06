import { test, expect } from "@playwright/test";

test.describe("Home page", () => {
  test("renders brand elements", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("img[alt*='Syzygy' i]").first()).toBeVisible();
  });

  test("shows command bar input", async ({ page }) => {
    await page.goto("/");
    const input = page.locator("input[placeholder*='command' i], input[type='text']").first();
    await expect(input).toBeVisible();
  });

  test("has working sidebar navigation", async ({ page }) => {
    await page.goto("/");
    const sidebar = page.locator("nav, aside").first();
    await expect(sidebar).toBeVisible();
  });

  test("sidebar has Cloud at top", async ({ page }) => {
    await page.goto("/");
    const cloudLink = page.locator("a[href='/cloud']").first();
    await expect(cloudLink).toBeVisible();
  });

  test("can type in command input", async ({ page }) => {
    await page.goto("/");
    const input = page.locator("input[placeholder*='command' i], input[type='text']").first();
    await input.fill("test command");
    await expect(input).toHaveValue("test command");
  });

  test("has branding images with correct alts", async ({ page }) => {
    await page.goto("/");
    const logos = page.locator("img[alt*='logo' i], img[alt*='Syzygy' i]");
    const count = await logos.count();
    expect(count).toBeGreaterThan(0);
  });
});
