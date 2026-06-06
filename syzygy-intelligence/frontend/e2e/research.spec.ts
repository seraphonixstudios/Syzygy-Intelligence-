import { test, expect } from "@playwright/test";

test.describe("Research page", () => {
  test("renders research interface", async ({ page }) => {
    await page.goto("/research");
    await expect(page.locator("h1")).toContainText("Research");
    await expect(page.locator("input[placeholder*='query' i]")).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/research");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });
});
