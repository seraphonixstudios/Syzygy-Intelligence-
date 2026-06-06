import { test, expect } from "@playwright/test";

test.describe("Settings page", () => {
  test("renders settings interface", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.locator("h1")).toContainText("Settings");
  });
});
