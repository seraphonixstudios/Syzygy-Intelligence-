import { test, expect } from "@playwright/test";

test.describe("Content page", () => {
  test("renders content generation interface", async ({ page }) => {
    await page.goto("/content");
    await expect(page.locator("h1")).toContainText("Content");
    await expect(page.locator("input[placeholder*='topic' i]")).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/content");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });
});
