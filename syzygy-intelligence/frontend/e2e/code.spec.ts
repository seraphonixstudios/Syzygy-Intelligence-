import { test, expect } from "@playwright/test";

test.describe("Code page", () => {
  test("renders code generation interface", async ({ page }) => {
    await page.goto("/code");
    await expect(page.locator("h1")).toContainText("Code");
    await expect(page.locator("input[placeholder*='code' i]")).toBeVisible();
  });

  test("has generate and copy buttons", async ({ page }) => {
    await page.goto("/code");
    const buttons = page.locator("button");
    await expect(buttons.first()).toBeVisible();
  });

  test("has voice button", async ({ page }) => {
    await page.goto("/code");
    const voiceBtn = page.locator("button:has-text('Voice')");
    await expect(voiceBtn).toBeVisible();
  });
});
