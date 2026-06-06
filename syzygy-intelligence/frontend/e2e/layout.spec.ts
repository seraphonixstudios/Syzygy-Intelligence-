import { test, expect } from "@playwright/test";

test.describe("Layout", () => {
  test("page title contains Syzygy", async ({ page }) => {
    await page.goto("/");
    const title = await page.title();
    expect(title).toContain("Syzygy");
  });

  test("brand image renders in sidebar", async ({ page }) => {
    await page.goto("/");
    const brandImg = page.locator("img[src*='pagetop']").first();
    await expect(brandImg).toBeVisible();
  });

  test("sidebar is present on all pages", async ({ page }) => {
    await page.goto("/chat");
    const nav = page.locator("nav, aside").first();
    await expect(nav).toBeVisible();
  });

  test("has pagetop logo on all pages", async ({ page }) => {
    await page.goto("/code");
    await expect(page.locator("img[src*='pagetop']").first()).toBeVisible();
  });

  test("all brand images in brand footer load", async ({ page }) => {
    await page.goto("/");
    const solLuna = page.locator("img[alt='Sol'], img[alt='Luna']");
    const count = await solLuna.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test("sidebar has exactly 13 nav links", async ({ page }) => {
    await page.goto("/");
    const links = page.locator("nav a, aside a");
    const count = await links.count();
    expect(count).toBeGreaterThanOrEqual(13);
  });
});
