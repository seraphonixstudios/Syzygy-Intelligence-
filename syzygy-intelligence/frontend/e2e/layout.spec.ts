import { test, expect } from "@playwright/test";

test.describe("Layout", () => {
  test("page title contains Syzygy", async ({ page }) => {
    await page.goto("/");
    const title = await page.title();
    expect(title).toContain("Syzygy");
  });

  test("brand image renders in header", async ({ page }) => {
    await page.goto("/");
    const brandImg = page.locator("img[src*='pagetop']").first();
    await expect(brandImg).toBeVisible();
  });

  test("sidebar is present on all pages", async ({ page }) => {
    await page.goto("/chat");
    const nav = page.locator("nav, aside").first();
    await expect(nav).toBeVisible();
  });
});
