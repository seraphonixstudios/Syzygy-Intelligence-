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
});
