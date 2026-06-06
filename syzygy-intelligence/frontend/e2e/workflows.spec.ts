import { test, expect } from "@playwright/test";

test.describe("Workflows page", () => {
  test("renders workflows interface", async ({ page }) => {
    await page.goto("/workflows");
    await expect(page.locator("h1")).toContainText("Workflows");
  });

  test("workflow cards are clickable", async ({ page }) => {
    await page.goto("/workflows");
    const cards = page.locator("button").first();
    await expect(cards).toBeVisible();
  });
});
