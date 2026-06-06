import { test, expect } from "@playwright/test";

test.describe("Improve page", () => {
  test("renders improvement interface", async ({ page }) => {
    await page.goto("/improve");
    await expect(page.locator("h1")).toContainText("Improve");
    await expect(page.locator("input[placeholder*='output' i]")).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/improve");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });
});
