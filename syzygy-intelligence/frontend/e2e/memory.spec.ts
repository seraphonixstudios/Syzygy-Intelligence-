import { test, expect } from "@playwright/test";

test.describe("Memory page", () => {
  test("renders memory interface", async ({ page }) => {
    await page.goto("/memory");
    await expect(page.locator("h1")).toContainText("Memory");
  });
});
