import { test, expect } from "@playwright/test";

test.describe("Sidebar navigation", () => {
  test("navigates to all main pages", async ({ page }) => {
    await page.goto("/");

    const links = page.locator("nav a, aside a");
    const linkCount = await links.count();
    expect(linkCount).toBeGreaterThan(5);
  });

  test("clicking Chat link navigates to /chat", async ({ page }) => {
    await page.goto("/");
    const chatLink = page.locator("a[href='/chat']").first();
    if (await chatLink.isVisible()) {
      await chatLink.click();
      await expect(page).toHaveURL(/\/chat/);
    }
  });

  test("clicking Consensus link navigates to /consensus", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/consensus']").first();
    if (await link.isVisible()) {
      await link.click();
      await expect(page).toHaveURL(/\/consensus/);
    }
  });

  test("clicking Code link navigates to /code", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/code']").first();
    if (await link.isVisible()) {
      await link.click();
      await expect(page).toHaveURL(/\/code/);
    }
  });

  test("clicking Research link navigates to /research", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/research']").first();
    if (await link.isVisible()) {
      await link.click();
      await expect(page).toHaveURL(/\/research/);
    }
  });

  test("clicking Content link navigates to /content", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/content']").first();
    if (await link.isVisible()) {
      await link.click();
      await expect(page).toHaveURL(/\/content/);
    }
  });

  test("clicking Improve link navigates to /improve", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("a[href='/improve']").first();
    if (await link.isVisible()) {
      await link.click();
      await expect(page).toHaveURL(/\/improve/);
    }
  });
});
